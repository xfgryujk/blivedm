# -*- coding: utf-8 -*-
import asyncio
import collections
import enum
import json
import logging
import ssl as ssl_
import struct
import zlib
from typing import *

import aiohttp

from . import handlers

logger = logging.getLogger('blivedm')

ROOM_INIT_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom'
DANMAKU_SERVER_CONF_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo'
DEFAULT_DANMAKU_SERVER_LIST = [
    {'host': 'broadcastlv.chat.bilibili.com', 'port': 2243, 'wss_port': 443, 'ws_port': 2244}
]

HEADER_STRUCT = struct.Struct('>I2H2I')
HeaderTuple = collections.namedtuple('HeaderTuple', ('pack_len', 'raw_header_size', 'ver', 'operation', 'seq_id'))
WS_BODY_PROTOCOL_VERSION_INFLATE = 0
WS_BODY_PROTOCOL_VERSION_NORMAL = 1
WS_BODY_PROTOCOL_VERSION_DEFLATE = 2


# go-common\app\service\main\broadcast\model\operation.go
class Operation(enum.IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    SEND_MSG_REPLY = 5
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9
    PROTO_READY = 10
    PROTO_FINISH = 11
    CHANGE_ROOM = 12
    CHANGE_ROOM_REPLY = 13
    REGISTER = 14
    REGISTER_REPLY = 15
    UNREGISTER = 16
    UNREGISTER_REPLY = 17
    # B站业务自定义OP
    # MinBusinessOp = 1000
    # MaxBusinessOp = 10000


class InitError(Exception):
    """初始化失败"""


class BLiveClient:
    """
    B站直播弹幕客户端，负责连接房间

    :param room_id: URL中的房间ID，可以用短ID
    :param uid: B站用户ID，0表示未登录
    :param session: cookie、连接池
    :param heartbeat_interval: 发送心跳包的间隔时间（秒）
    :param ssl: True表示用默认的SSLContext验证，False表示不验证，也可以传入SSLContext
    :param loop: 协程事件循环
    """

    def __init__(
        self,
        room_id,
        uid=0,
        session: Optional[aiohttp.ClientSession] = None,
        heartbeat_interval=30,
        ssl: Union[bool, ssl_.SSLContext] = True,
        loop: Optional[asyncio.BaseEventLoop] = None,
    ):
        # 用来init_room的临时房间ID，可以用短ID
        self._tmp_room_id = room_id
        self._uid = uid

        if loop is not None:
            self._loop = loop
        elif session is not None:
            self._loop = session.loop  # noqa
        else:
            self._loop = asyncio.get_event_loop()

        if session is None:
            self._session = aiohttp.ClientSession(loop=self._loop, timeout=aiohttp.ClientTimeout(total=10))
            self._own_session = True
        else:
            self._session = session
            self._own_session = False
            if self._session.loop is not self._loop:  # noqa
                raise RuntimeError('BLiveClient and session must use the same event loop')

        self._heartbeat_interval = heartbeat_interval
        self._ssl = ssl if ssl else ssl_._create_unverified_context()  # noqa

        # 消息处理器，可动态增删
        self._handlers: List[handlers.HandlerInterface] = []

        # 在调用init_room后初始化的字段
        # 真实房间ID
        self._room_id = None
        # 房间短ID，没有则为0
        self._room_short_id = None
        # 主播用户ID
        self._room_owner_uid = None
        # 弹幕服务器列表
        # [{host: "tx-bj4-live-comet-04.chat.bilibili.com", port: 2243, wss_port: 443, ws_port: 2244}, ...]
        self._host_server_list: Optional[List[dict]] = None
        # 连接弹幕服务器用的token
        self._host_server_token = None

        # 在运行时初始化的字段
        # websocket连接
        self._websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        # 网络协程的future
        self._network_future: Optional[asyncio.Future] = None
        # 发心跳包定时器的handle
        self._heartbeat_timer_handle: Optional[asyncio.TimerHandle] = None

    @property
    def is_running(self) -> bool:
        """
        本客户端正在运行，注意调用stop后还没完全停止也算正在运行
        """
        return self._network_future is not None

    @property
    def room_id(self) -> Optional[int]:
        """
        房间ID，调用init_room后初始化
        """
        return self._room_id

    @property
    def room_short_id(self) -> Optional[int]:
        """
        房间短ID，没有则为0，调用init_room后初始化
        """
        return self._room_short_id

    @property
    def room_owner_uid(self) -> Optional[int]:
        """
        主播用户ID，调用init_room后初始化
        """
        return self._room_owner_uid

    def add_handler(self, handler: 'handlers.HandlerInterface'):
        """
        添加消息处理器
        注意多个处理器是并发处理的，不要依赖处理的顺序
        消息处理器和接收消息运行在同一协程，如果处理消息耗时太长会阻塞接收消息，这种情况建议将消息推到队列，让另一个协程处理

        :param handler: 消息处理器
        """
        if handler not in self._handlers:
            self._handlers.append(handler)

    def remove_handler(self, handler: 'handlers.HandlerInterface'):
        """
        移除消息处理器

        :param handler: 消息处理器
        """
        try:
            self._handlers.remove(handler)
        except ValueError:
            pass

    def start(self):
        """
        启动本客户端
        """
        if self.is_running:
            logger.warning('room %s 已经在运行中，不能再次start', self.room_id)
            return

        self._network_future = asyncio.ensure_future(self._network_coroutine_wrapper(), loop=self._loop)

    def stop(self):
        """
        停止本客户端
        """
        if not self.is_running:
            logger.warning('room %s 已经停止，不能再次stop', self.room_id)
            return

        self._network_future.cancel()

    async def stop_and_close(self):
        """
        停止本客户端并释放本客户端的资源，调用后本客户端将不可用
        """
        self.stop()
        await self.join()
        await self.close()

    async def join(self):
        """
        等待本客户端停止
        """
        if not self.is_running:
            logger.warning('room %s 已经停止，不能join', self.room_id)
            return

        await self._network_future

    async def close(self):
        """
        释放本客户端的资源，调用后本客户端将不可用
        """
        if self.is_running:
            logger.warning('room %s 在运行状态中调用了close', self.room_id)

        # 如果session是自己创建的则关闭session
        if self._own_session:
            await self._session.close()

    async def init_room(self):
        """
        初始化连接房间需要的字段

        :return: True代表没有降级，如果需要降级后还可用，重载这个函数返回True
        """
        res = True
        if not await self._init_room_id_and_owner():
            res = False
            # 失败了则降级
            self._room_id = self._room_short_id = self._tmp_room_id
            self._room_owner_uid = 0

        if not await self._init_host_server():
            res = False
            # 失败了则降级
            self._host_server_list = DEFAULT_DANMAKU_SERVER_LIST
            self._host_server_token = None
        return res

    async def _init_room_id_and_owner(self):
        try:
            async with self._session.get(ROOM_INIT_URL, params={'room_id': self._tmp_room_id},
                                         ssl=self._ssl) as res:
                if res.status != 200:
                    logger.warning('room %d init_room失败：%d %s', self._tmp_room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room %d init_room失败：%s', self._tmp_room_id, data['message'])
                    return False
                if not self._parse_room_init(data['data']):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room %d init_room失败：', self._tmp_room_id)
            return False
        return True

    def _parse_room_init(self, data):
        room_info = data['room_info']
        self._room_id = room_info['room_id']
        self._room_short_id = room_info['short_id']
        self._room_owner_uid = room_info['uid']
        return True

    async def _init_host_server(self):
        try:
            async with self._session.get(DANMAKU_SERVER_CONF_URL, params={'id': self._room_id, 'type': 0},
                                         ssl=self._ssl) as res:
                if res.status != 200:
                    logger.warning('room %d getConf失败：%d %s', self._room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room %d getConf失败：%s', self._room_id, data['message'])
                    return False
                if not self._parse_danmaku_server_conf(data['data']):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room %d getConf失败：', self._room_id)
            return False
        return True

    def _parse_danmaku_server_conf(self, data):
        self._host_server_list = data['host_list']
        self._host_server_token = data['token']
        if not self._host_server_list:
            logger.warning('room %d getConf失败：host_server_list为空', self._room_id)
            return False
        return True

    @staticmethod
    def _make_packet(data: dict, operation: int) -> bytes:
        """
        创建一个要发送给服务器的包

        :param data: 包体JSON数据
        :param operation: 操作码，见Operation
        :return: 整个包的数据
        """
        body = json.dumps(data).encode('utf-8')
        header = HEADER_STRUCT.pack(
            HEADER_STRUCT.size + len(body),  # pack_len
            HEADER_STRUCT.size,  # raw_header_size
            1,  # ver
            operation,  # operation
            1  # seq_id
        )
        return header + body

    async def _network_coroutine_wrapper(self):
        """
        负责处理网络协程的异常，网络协程具体逻辑在_network_coroutine里
        """
        try:
            await self._network_coroutine()
        except asyncio.CancelledError:
            # 正常停止
            pass
        except Exception as e:  # noqa
            logger.exception('room %s 网络协程异常结束：', self.room_id)
        finally:
            logger.debug('room %s 网络协程结束', self.room_id)
            self._network_future = None

    async def _network_coroutine(self):
        """
        网络协程，负责连接服务器、接收消息、解包
        """
        # 如果之前未初始化则初始化
        if self._host_server_token is None:
            if not await self.init_room():
                raise InitError('初始化失败')

        retry_count = 0
        while True:
            try:
                # 连接
                host_server = self._host_server_list[retry_count % len(self._host_server_list)]
                async with self._session.ws_connect(
                    f"wss://{host_server['host']}:{host_server['wss_port']}/sub",
                    receive_timeout=self._heartbeat_interval + 5,
                    ssl=self._ssl
                ) as websocket:
                    self._websocket = websocket
                    await self._on_ws_connect()

                    # 处理消息
                    message: aiohttp.WSMessage
                    async for message in websocket:
                        retry_count = 0
                        await self._on_ws_message(message)

            except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
                # 掉线重连
                pass
            except ssl_.SSLError:
                logger.error('room %d 发生SSL错误，无法重连', self.room_id)
                raise
            finally:
                self._websocket = None
                await self._on_ws_close()

            # 准备重连
            retry_count += 1
            logger.warning('room %d 掉线重连中%d', self.room_id, retry_count)
            await asyncio.sleep(1, loop=self._loop)

    async def _on_ws_connect(self):
        """
        websocket连接成功
        """
        await self._send_auth()
        self._heartbeat_timer_handle = self._loop.call_later(self._heartbeat_interval, self._on_send_heartbeat)

    async def _on_ws_close(self):
        """
        websocket连接断开
        """
        if self._heartbeat_timer_handle is not None:
            self._heartbeat_timer_handle.cancel()
            self._heartbeat_timer_handle = None

    async def _send_auth(self):
        """
        发送认证包
        """
        auth_params = {
            'uid': self._uid,
            'roomid': self._room_id,
            'protover': 2,
            'platform': 'web',
            'clientver': '1.14.3',
            'type': 2
        }
        if self._host_server_token is not None:
            auth_params['key'] = self._host_server_token
        await self._websocket.send_bytes(self._make_packet(auth_params, Operation.AUTH))

    def _on_send_heartbeat(self):
        """
        定时发送心跳包的回调
        """
        coro = self._websocket.send_bytes(self._make_packet({}, Operation.HEARTBEAT))
        asyncio.ensure_future(coro, loop=self._loop)
        self._heartbeat_timer_handle = self._loop.call_later(self._heartbeat_interval, self._on_send_heartbeat)

    async def _on_ws_message(self, message: aiohttp.WSMessage):
        """
        收到websocket消息

        :param message: websocket消息
        """
        if message.type != aiohttp.WSMsgType.BINARY:
            logger.warning('room %d 未知的websocket消息：type=%s %s', self.room_id,
                           message.type, message.data)
            return

        try:
            await self._parse_ws_message(message.data)
        except asyncio.CancelledError:
            # 正常停止，让外层处理
            raise
        except Exception:  # noqa
            logger.exception('room %d 处理websocket消息时发生错误：', self.room_id)

    async def _parse_ws_message(self, data: bytes):
        """
        解析websocket消息

        :param data: websocket消息数据
        """
        offset = 0
        while offset < len(data):
            try:
                header = HeaderTuple(*HEADER_STRUCT.unpack_from(data, offset))
            except struct.error:
                break

            if header.operation == Operation.HEARTBEAT_REPLY:
                # 心跳包，自己造个消息当成业务消息处理
                popularity = int.from_bytes(
                    data[offset + HEADER_STRUCT.size: offset + HEADER_STRUCT.size + 4],
                    'big'
                )
                body = {
                    'cmd': '_HEARTBEAT',
                    'data': {
                        'popularity': popularity
                    }
                }
                await self._handle_command(body)

            elif header.operation == Operation.SEND_MSG_REPLY:
                # 业务消息
                body = data[offset + HEADER_STRUCT.size: offset + header.pack_len]
                if header.ver == WS_BODY_PROTOCOL_VERSION_DEFLATE:
                    # 压缩过的先解压，为了避免阻塞网络线程，放在其他线程执行
                    body = await self._loop.run_in_executor(None, zlib.decompress, body)
                    await self._parse_ws_message(body)
                else:
                    # 没压缩过的
                    try:
                        body = json.loads(body.decode('utf-8'))
                        await self._handle_command(body)
                    except Exception:
                        logger.error('room %d body=%s', self.room_id, body)
                        raise

            elif header.operation == Operation.AUTH_REPLY:
                # 认证响应
                await self._websocket.send_bytes(self._make_packet({}, Operation.HEARTBEAT))

            else:
                # 未知消息
                body = data[offset + HEADER_STRUCT.size: offset + header.pack_len]
                logger.warning('room %d 未知包类型：operation=%d %s%s', self.room_id,
                               header.operation, header, body)

            offset += header.pack_len

    async def _handle_command(self, command: Union[list, dict]):
        """
        解析并处理业务消息

        :param command: 业务消息
        """
        # 这里可能会多个消息一起发
        if isinstance(command, list):
            for one_command in command:
                await self._handle_command(one_command)
            return

        results = await asyncio.gather(
            *(handler.handle(self, command) for handler in self._handlers),
            loop=self._loop,
            return_exceptions=True
        )
        for res in results:
            if isinstance(res, Exception):
                logger.exception('room %d 处理消息时发生错误，command=%s', self.room_id, command, exc_info=res)
