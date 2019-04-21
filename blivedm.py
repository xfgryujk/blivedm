# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import struct
from collections import namedtuple
from enum import IntEnum
# noinspection PyProtectedMember
from ssl import _create_unverified_context

import aiohttp

logger = logging.getLogger(__name__)


class Operation(IntEnum):
    SEND_HEARTBEAT = 2
    POPULARITY = 3
    COMMAND = 5
    AUTH = 7
    RECV_HEARTBEAT = 8


class BLiveClient:
    ROOM_INIT_URL = 'https://api.live.bilibili.com/room/v1/Room/room_init'
    WEBSOCKET_URL = 'wss://broadcastlv.chat.bilibili.com:2245/sub'

    HEADER_STRUCT = struct.Struct('>I2H2I')
    HeaderTuple = namedtuple('HeaderTuple', ('total_len', 'header_len', 'proto_ver', 'operation', 'sequence'))

    _COMMAND_HANDLERS = {
        # 收到弹幕
        'DANMU_MSG': lambda client, command: client._on_get_danmaku(
            command['info'][1], command['info'][2][1]
        ),
        # 有人送礼
        'SEND_GIFT': lambda client, command: client._on_gift(
            command['data']['giftName'], command['data']['num'], command['data']['uname']
        )
    }
    for cmd in (  # 其他已知命令
        # 从前端扒来的
        '66FFFF', 'SYS_MSG', 'SYS_GIFT', 'GUARD_MSG', 'LIVE', 'PREPARING',
        'END', 'CLOSE', 'BLOCK', 'ROUND', 'WELCOME', 'REFRESH',
        'ACTIVITY_RED_PACKET', 'ROOM_LIMIT', 'PK_PRE', 'PK_END', 'PK_SETTLE',
        'PK_MIC_END', 'live', 'preparing', 'end', 'close', 'block', 'pre-round',
        'round', 'error', 'player-state-play', 'player-state-pause', 'http:',
        'https:', 'ws:', 'wss:', 'videoVolume', 'homeVideoVolume', 'div',
        'canvas', 'initialized', 'playerStateChange', 'liveStateChange',
        'videoStateChange', 'fullscreenChange', 'playing', 'paused', 'switchLine',
        'switchQuality', 'webFullscreen', 'feedBackClick', 'blockSettingClick',
        'set', 'initDanmaku', 'addDanmaku', 'sendDanmaku', 'receiveOnlineCount',
        'receiveMessage', 'userLogin', 'giftPackageClick', 'sendGift', 'guidChange',
        'reload', 'danmaku', 'block', 'gift', 'firstLoadedAPIPlayer',
        'firstLoadedAPIPlayurl', 'firstLoadStart', 'firstLoadedMetaData',
        'firstPlaying', 'enterTheRoom', 'operableElementsChange',
        # 其他遇到的
        'COMBO_SEND', 'COMBO_END', 'ROOM_RANK', 'NOTICE_MSG', 'WELCOME_GUARD',
        'WISH_BOTTLE', 'RAFFLE_START', 'ENTRY_EFFECT', 'ROOM_REAL_TIME_MESSAGE_UPDATE'
    ):
        _COMMAND_HANDLERS[cmd] = None

    def __init__(self, room_id, ssl=True, loop=None, session: aiohttp.ClientSession=None,
                 uid=0):
        """
        :param room_id: URL中的房间ID
        :param ssl: True表示用默认的SSLContext验证，False表示不验证，也可以传入SSLContext
        :param loop: 协程事件循环
        :param session: cookie、连接池
        :param uid: B站用户ID，0表示未登录
        """
        self._short_id = room_id
        self._room_id = None
        self._uid = uid

        if loop is not None:
            self._loop = loop
        elif session is not None:
            self._loop = session.loop
        else:
            self._loop = asyncio.get_event_loop()
        self._is_running = False

        if session is None:
            self._session = aiohttp.ClientSession(loop=self._loop)
            self._own_session = True
        else:
            self._session = session
            self._own_session = False
            if self._session.loop is not self._loop:
                raise RuntimeError('BLiveClient and session has to use same event loop')
        self._ssl = ssl if ssl else _create_unverified_context()
        self._websocket = None

    @property
    def is_running(self):
        return self._is_running

    async def close(self):
        """
        如果session是自己创建的则关闭session
        """
        if self._own_session:
            await self._session.close()

    def run(self):
        """
        创建相关的协程，不会执行事件循环
        :return: 协程的future
        """
        if self._is_running:
            raise RuntimeError('This client is already running')
        self._is_running = True
        return asyncio.ensure_future(self._message_loop(), loop=self._loop)

    async def _get_room_id(self):
        async with self._session.get(self.ROOM_INIT_URL,
                                     params={'id': self._short_id},
                                     ssl=self._ssl) as res:
            if res.status == 200:
                data = await res.json()
                if data['code'] == 0:
                    self._room_id = data['data']['room_id']
                else:
                    raise ConnectionAbortedError('获取房间ID失败：' + data['msg'])
            else:
                raise ConnectionAbortedError('获取房间ID失败：' + res.reason)

    def _make_packet(self, data, operation):
        body = json.dumps(data).encode('utf-8')
        header = self.HEADER_STRUCT.pack(
            self.HEADER_STRUCT.size + len(body),
            self.HEADER_STRUCT.size,
            1,
            operation,
            1
        )
        return header + body

    async def _send_auth(self):
        auth_params = {
            'uid':       self._uid,
            'roomid':    self._room_id,
            'protover':  1,
            'platform':  'web',
            'clientver': '1.4.0'
        }
        await self._websocket.send_bytes(self._make_packet(auth_params, Operation.AUTH))

    async def _message_loop(self):
        # 获取房间ID
        if self._room_id is None:
            await self._get_room_id()

        while True:
            heartbeat_future = None
            try:
                # 连接
                async with self._session.ws_connect(self.WEBSOCKET_URL,
                                                    ssl=self._ssl) as websocket:
                    self._websocket = websocket
                    await self._send_auth()
                    heartbeat_future = asyncio.ensure_future(self._heartbeat_loop(), loop=self._loop)

                    # 处理消息
                    async for message in websocket:  # type: aiohttp.WSMessage
                        if message.type == aiohttp.WSMsgType.BINARY:
                            await self._handle_message(message.data)
                        else:
                            logger.warning('未知的websocket消息：type=%s %s', message.type, message.data)

            except asyncio.CancelledError:
                break
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError):
                # 重连
                logger.warning('掉线重连中')
                try:
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break
            finally:
                if heartbeat_future is not None:
                    heartbeat_future.cancel()
                    try:
                        await heartbeat_future
                    except asyncio.CancelledError:
                        break
                self._websocket = None

        self._is_running = False

    async def _heartbeat_loop(self):
        while True:
            try:
                await self._websocket.send_bytes(self._make_packet({}, Operation.SEND_HEARTBEAT))
                await asyncio.sleep(30)

            except (asyncio.CancelledError, aiohttp.ClientConnectorError):
                break

    async def _handle_message(self, message):
        offset = 0
        while offset < len(message):
            try:
                header = self.HeaderTuple(*self.HEADER_STRUCT.unpack_from(message, offset))
            except struct.error:
                break

            if header.operation == Operation.POPULARITY:
                popularity = int.from_bytes(message[offset + self.HEADER_STRUCT.size:
                                                    offset + self.HEADER_STRUCT.size + 4],
                                            'big')
                await self._on_get_popularity(popularity)

            elif header.operation == Operation.COMMAND:
                body = message[offset + self.HEADER_STRUCT.size: offset + header.total_len]
                body = json.loads(body.decode('utf-8'))
                await self._handle_command(body)

            elif header.operation == Operation.RECV_HEARTBEAT:
                await self._websocket.send_bytes(self._make_packet({}, Operation.SEND_HEARTBEAT))

            else:
                body = message[offset + self.HEADER_STRUCT.size: offset + header.total_len]
                logger.warning('未知包类型：operation=%d %s%s', header.operation, header, body)

            offset += header.total_len

    async def _handle_command(self, command):
        if isinstance(command, list):
            for one_command in command:
                await self._handle_command(one_command)
            return

        cmd = command['cmd']
        if cmd in self._COMMAND_HANDLERS:
            handler = self._COMMAND_HANDLERS[cmd]
            if handler is not None:
                await handler(self, command)
        else:
            logger.warning('未知命令：cmd=%s %s', cmd, command)

    async def _on_get_popularity(self, popularity):
        """
        获取到人气值
        :param popularity: 人气值
        """
        pass

    async def _on_get_danmaku(self, content, user_name):
        """
        获取到弹幕
        :param content: 弹幕内容
        :param user_name: 弹幕作者
        """
        pass

    async def _on_gift(self, gift_name, gift_num, user_name):
        """
        有人送礼
        :param gift_name: 礼物名
        :param gift_num: 礼物数
        :param user_name: 送礼人
        """
        pass
