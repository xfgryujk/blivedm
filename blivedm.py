# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import ssl as ssl_
import struct
import zlib
from collections import namedtuple
from enum import IntEnum
from typing import *

import aiohttp

logger = logging.getLogger(__name__)

ROOM_INIT_URL = 'https://api.live.bilibili.com/room/v1/Room/room_init'
DANMAKU_SERVER_CONF_URL = 'https://api.live.bilibili.com/room/v1/Danmu/getConf'

HEADER_STRUCT = struct.Struct('>I2H2I')
HeaderTuple = namedtuple('HeaderTuple', ('pack_len', 'raw_header_size', 'ver', 'operation', 'seq_id'))
WS_BODY_PROTOCOL_VERSION_NORMAL = 0
WS_BODY_PROTOCOL_VERSION_INT = 1  # 用于心跳包
WS_BODY_PROTOCOL_VERSION_DEFLATE = 2


# go-common\app\service\main\broadcast\model\operation.go
class Operation(IntEnum):
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


class DanmakuMessage:
    def __init__(self, mode, font_size, color, timestamp, rnd, uid_crc32, msg_type, bubble,
                 msg,
                 uid, uname, admin, vip, svip, urank, mobile_verify, uname_color,
                 medal_level, medal_name, runame, room_id, mcolor, special_medal,
                 user_level, ulevel_color, ulevel_rank,
                 old_title, title,
                 privilege_type):
        """
        :param mode: 弹幕显示模式（滚动、顶部、底部）
        :param font_size: 字体尺寸
        :param color: 颜色
        :param timestamp: 时间戳
        :param rnd: 随机数
        :param uid_crc32: 用户ID文本的CRC32
        :param msg_type: 是否礼物弹幕（节奏风暴）
        :param bubble: 右侧评论栏气泡

        :param msg: 弹幕内容

        :param uid: 用户ID
        :param uname: 用户名
        :param admin: 是否房管
        :param vip: 是否月费老爷
        :param svip: 是否年费老爷
        :param urank: 用户身份，用来判断是否正式会员，猜测非正式会员为5000，正式会员为10000
        :param mobile_verify: 是否绑定手机
        :param uname_color: 用户名颜色

        :param medal_level: 勋章等级
        :param medal_name: 勋章名
        :param runame: 勋章房间主播名
        :param room_id: 勋章房间ID
        :param mcolor: 勋章颜色
        :param special_medal: 特殊勋章

        :param user_level: 用户等级
        :param ulevel_color: 用户等级颜色
        :param ulevel_rank: 用户等级排名，>50000时为'>50000'

        :param old_title: 旧头衔
        :param title: 头衔

        :param privilege_type: 舰队类型，0非舰队，1总督，2提督，3舰长
        """
        self.mode = mode
        self.font_size = font_size
        self.color = color
        self.timestamp = timestamp
        self.rnd = rnd
        self.uid_crc32 = uid_crc32
        self.msg_type = msg_type
        self.bubble = bubble

        self.msg = msg

        self.uid = uid
        self.uname = uname
        self.admin = admin
        self.vip = vip
        self.svip = svip
        self.urank = urank
        self.mobile_verify = mobile_verify
        self.uname_color = uname_color

        self.medal_level = medal_level
        self.medal_name = medal_name
        self.runame = runame
        self.room_id = room_id
        self.mcolor = mcolor
        self.special_medal = special_medal

        self.user_level = user_level
        self.ulevel_color = ulevel_color
        self.ulevel_rank = ulevel_rank

        self.old_title = old_title
        self.title = title

        self.privilege_type = privilege_type

    @classmethod
    def from_command(cls, info: dict):
        return cls(
            info[0][1], info[0][2], info[0][3], info[0][4], info[0][5], info[0][7], info[0][9], info[0][10],
            info[1],
            *info[2][:8],
            *(info[3][:6] or (0, '', '', 0, 0, 0)),
            info[4][0], info[4][2], info[4][3],
            *info[5][:2],
            info[7]
        )


class GiftMessage:
    def __init__(self, gift_name, num, uname, face, guard_level, uid, timestamp, gift_id,
                 gift_type, action, price, rnd, coin_type, total_coin):
        """
        :param gift_name: 礼物名
        :param num: 礼物数量
        :param uname: 用户名
        :param face: 用户头像URL
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param uid: 用户ID
        :param timestamp: 时间戳
        :param gift_id: 礼物ID
        :param gift_type: 礼物类型（未知）
        :param action: 目前遇到的有'喂食'、'赠送'
        :param price: 礼物单价瓜子数
        :param rnd: 随机数
        :param coin_type: 瓜子类型，'silver'或'gold'
        :param total_coin: 总瓜子数
        """
        self.gift_name = gift_name
        self.num = num
        self.uname = uname
        self.face = face
        self.guard_level = guard_level
        self.uid = uid
        self.timestamp = timestamp
        self.gift_id = gift_id
        self.gift_type = gift_type
        self.action = action
        self.price = price
        self.rnd = rnd
        self.coin_type = coin_type
        self.total_coin = total_coin

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data['giftName'], data['num'], data['uname'], data['face'], data['guard_level'],
            data['uid'], data['timestamp'], data['giftId'], data['giftType'],
            data['action'], data['price'], data['rnd'], data['coin_type'], data['total_coin']
        )


class GuardBuyMessage:
    def __init__(self, uid, username, guard_level, num, price, gift_id, gift_name,
                 start_time, end_time):
        """
        :param uid: 用户ID
        :param username: 用户名
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param num: 数量
        :param price: 单价金瓜子数
        :param gift_id: 礼物ID
        :param gift_name: 礼物名
        :param start_time: 开始时间戳？
        :param end_time: 结束时间戳？
        """
        self.uid = uid
        self.username = username
        self.guard_level = guard_level
        self.num = num
        self.price = price
        self.gift_id = gift_id
        self.gift_name = gift_name
        self.start_time = start_time
        self.end_time = end_time

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data['uid'], data['username'], data['guard_level'], data['num'], data['price'],
            data['role_name'], data['gift_name'], data['start_time'], data['end_time']
        )


class SuperChatMessage:
    def __init__(self, price, message, message_jpn, start_time, end_time, time, id_,
                 gift_id, gift_name, uid, uname, face, guard_level, user_level,
                 background_bottom_color, background_color, background_icon, background_image,
                 background_price_color):
        """
        :param price: 价格（人民币）
        :param message: 消息
        :param message_jpn: 消息日文翻译（目前只出现在SUPER_CHAT_MESSAGE_JPN）
        :param start_time: 开始时间戳
        :param end_time: 结束时间戳
        :param time: 剩余时间
        :param id_: str，消息ID，删除时用
        :param gift_id: 礼物ID
        :param gift_name: 礼物名
        :param uid: 用户ID
        :param uname: 用户名
        :param face: 用户头像URL
        :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
        :param user_level: 用户等级
        :param background_bottom_color: 底部背景色
        :param background_color: 背景色
        :param background_icon: 背景图标
        :param background_image: 背景图
        :param background_price_color: 背景价格颜色
        """
        self.price = price
        self.message = message
        self.message_jpn = message_jpn
        self.start_time = start_time
        self.end_time = end_time
        self.time = time
        self.id = id_
        self.gift_id = gift_id
        self.gift_name = gift_name
        self.uid = uid
        self.uname = uname
        self.face = face
        self.guard_level = guard_level
        self.user_level = user_level
        self.background_bottom_color = background_bottom_color
        self.background_color = background_color
        self.background_icon = background_icon
        self.background_image = background_image
        self.background_price_color = background_price_color

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data['price'], data['message'], data['message_trans'], data['start_time'],
            data['end_time'], data['time'], data['id'], data['gift']['gift_id'],
            data['gift']['gift_name'], data['uid'], data['user_info']['uname'],
            data['user_info']['face'], data['user_info']['guard_level'],
            data['user_info']['user_level'], data['background_bottom_color'],
            data['background_color'], data['background_icon'], data['background_image'],
            data['background_price_color']
        )


class SuperChatDeleteMessage:
    def __init__(self, ids):
        """
        :param ids: 消息ID数组
        """
        self.ids = ids

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            data['ids']
        )


class BLiveClient:
    _COMMAND_HANDLERS: Dict[str, Optional[Callable[['BLiveClient', dict], Awaitable]]] = {
        # 收到弹幕
        # go-common\app\service\live\live-dm\service\v1\send.go
        'DANMU_MSG': lambda client, command: client._on_receive_danmaku(
            DanmakuMessage.from_command(command['info'])
        ),
        # 有人送礼
        'SEND_GIFT': lambda client, command: client._on_receive_gift(
            GiftMessage.from_command(command['data'])
        ),
        # 有人上舰
        'GUARD_BUY': lambda client, command: client._on_buy_guard(
            GuardBuyMessage.from_command(command['data'])
        ),
        # 醒目留言
        'SUPER_CHAT_MESSAGE': lambda client, command: client._on_super_chat(
            SuperChatMessage.from_command(command['data'])
        ),
        # 删除醒目留言
        'SUPER_CHAT_MESSAGE_DELETE': lambda client, command: client._on_super_chat_delete(
            SuperChatDeleteMessage.from_command(command['data'])
        )
    }
    for cmd in (  # 其他已知命令
        '', 'ACTIVITY_BANNER_RED_NOTICE_CLOSE', 'ACTIVITY_BANNER_UPDATE_V2', 'ACTIVITY_MATCH_GIFT',
        'ACTIVITY_RED_PACKET', 'BLOCK', 'CHANGE_ROOM_INFO', 'CLOSE', 'COMBO_END', 'COMBO_SEND',
        'CUT_OFF', 'DAILY_QUEST_NEWDAY', 'END', 'ENTRY_EFFECT', 'GUARD_LOTTERY_START',
        'GUARD_MSG', 'GUIARD_MSG', 'HOUR_RANK_AWARDS', 'LIVE', 'LOL_ACTIVITY',
        'LUCK_GIFT_AWARD_USER', 'MESSAGEBOX_USER_GAIN_MEDAL', 'new_anchor_reward', 'NOTICE_MSG',
        'PK_AGAIN', 'PK_END', 'PK_MATCH', 'PK_MIC_END', 'PK_PRE', 'PK_PROCESS', 'PK_SETTLE',
        'PK_START', 'PREPARING', 'RAFFLE_END', 'RAFFLE_START', 'REFRESH', 'ROOM_ADMINS',
        'room_admin_entrance', 'ROOM_BLOCK_INTO', 'ROOM_BLOCK_MSG', 'ROOM_BOX_MASTER',
        'ROOM_CHANGE', 'ROOM_KICKOUT', 'ROOM_LIMIT', 'ROOM_LOCK', 'ROOM_RANK',
        'ROOM_REAL_TIME_MESSAGE_UPDATE', 'ROOM_REAL_TIME_MESSAGE_UPDATE', 'ROOM_REFRESH',
        'ROOM_SHIELD', 'ROOM_SILENT_OFF', 'ROOM_SILENT_ON', 'ROOM_SKIN_MSG', 'ROUND',
        'SCORE_CARD', 'SEND_TOP', 'SPECIAL_GIFT', 'SUPER_CHAT_ENTRANCE',
        'SUPER_CHAT_MESSAGE_JPN', 'SYS_GIFT', 'SYS_MSG', 'TV_END', 'TV_START', 'USER_TOAST_MSG',
        'WARNING', 'WEEK_STAR_CLOCK', 'WELCOME', 'WELCOME_GUARD', 'WIN_ACTIVITY', 'WISH_BOTTLE'
    ):
        _COMMAND_HANDLERS[cmd] = None
    del cmd

    def __init__(self, room_id, uid=0, session: aiohttp.ClientSession=None,
                 heartbeat_interval=30, ssl=True, loop=None):
        """
        :param room_id: URL中的房间ID，可以为短ID
        :param uid: B站用户ID，0表示未登录
        :param session: cookie、连接池
        :param heartbeat_interval: 发送心跳包的间隔时间（秒）
        :param ssl: True表示用默认的SSLContext验证，False表示不验证，也可以传入SSLContext
        :param loop: 协程事件循环
        """
        # 用来init_room的临时房间ID
        self._tmp_room_id = room_id
        # 调用init_room后初始化
        self._room_id = self._room_short_id = self._room_owner_uid = None
        # [{host: "tx-bj4-live-comet-04.chat.bilibili.com", port: 2243, wss_port: 443, ws_port: 2244}, ...]
        self._host_server_list = None
        self._host_server_token = None
        self._uid = uid

        if loop is not None:
            self._loop = loop
        elif session is not None:
            # noinspection PyDeprecation
            self._loop = session.loop
        else:
            self._loop = asyncio.get_event_loop()
        self._future = None

        if session is None:
            self._session = aiohttp.ClientSession(loop=self._loop)
            self._own_session = True
        else:
            self._session = session
            self._own_session = False
            # noinspection PyDeprecation
            if self._session.loop is not self._loop:
                raise RuntimeError('BLiveClient and session has to use same event loop')

        self._heartbeat_interval = heartbeat_interval
        # noinspection PyProtectedMember
        self._ssl = ssl if ssl else ssl_._create_unverified_context()
        self._websocket = None

    @property
    def is_running(self):
        return self._future is not None

    @property
    def room_id(self):
        """
        房间ID，调用init_room后初始化
        """
        return self._room_id

    @property
    def room_short_id(self):
        """
        房间短ID，没有则为0，调用init_room后初始化
        """
        return self._room_short_id

    @property
    def room_owner_uid(self):
        """
        主播ID，调用init_room后初始化
        """
        return self._room_owner_uid

    async def close(self):
        """
        如果session是自己创建的则关闭session
        """
        if self._own_session:
            await self._session.close()

    def start(self):
        """
        创建相关的协程，不会执行事件循环
        :return: 协程的future
        """
        if self._future is not None:
            raise RuntimeError('This client is already running')
        self._future = asyncio.ensure_future(self._message_loop(), loop=self._loop)
        self._future.add_done_callback(self.__on_message_loop_done)
        return self._future

    def __on_message_loop_done(self, future):
        self._future = None
        logger.debug('room %s 消息协程结束', self.room_id)
        exception = future.exception()
        if exception is not None:
            logger.exception('room %s 消息协程异常结束：', self.room_id,
                             exc_info=(type(exception), exception, exception.__traceback__))

    def stop(self):
        """
        停止相关的协程
        :return: 协程的future
        """
        if self._future is None:
            raise RuntimeError('This client is not running')
        self._future.cancel()
        return self._future

    async def init_room(self):
        try:
            async with self._session.get(ROOM_INIT_URL, params={'id': self._tmp_room_id},
                                         ssl=self._ssl) as res:
                if res.status != 200:
                    logger.warning('room %d room_init失败：%d %s', self._tmp_room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room %d room_init失败：%s', self._tmp_room_id, data['msg'])
                    return False
                if not self._parse_room_init(data['data']):
                    return False
        except aiohttp.ClientConnectionError:
            logger.exception('room %d room_init失败：', self._tmp_room_id)
            return False

        try:
            async with self._session.get(DANMAKU_SERVER_CONF_URL, params={'room_id': self._tmp_room_id},
                                         ssl=self._ssl) as res:
                if res.status != 200:
                    logger.warning('room %d getConf失败：%d %s', self._tmp_room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room %d getConf失败：%s', self._tmp_room_id, data['msg'])
                    return False
                self._host_server_list = data['data']['host_server_list']
                self._host_server_token = data['data']['token']
                if not self._host_server_list:
                    logger.warning('room %d getConf失败：host_server_list为空')
                    return False
        except aiohttp.ClientConnectionError:
            logger.exception('room %d getConf失败：', self._tmp_room_id)
            return False
        return True

    def _parse_room_init(self, data):
        self._room_id = data['room_id']
        self._room_short_id = data['short_id']
        self._room_owner_uid = data['uid']
        return True

    def _make_packet(self, data, operation):
        body = json.dumps(data).encode('utf-8')
        header = HEADER_STRUCT.pack(
            HEADER_STRUCT.size + len(body),
            HEADER_STRUCT.size,
            1,
            operation,
            1
        )
        return header + body

    async def _send_auth(self):
        auth_params = {
            'uid':       self._uid,
            'roomid':    self._room_id,
            'protover':  2,
            'platform':  'web',
            'clientver': '1.8.2',
            'type':      2,
            'key':       self._host_server_token
        }
        await self._websocket.send_bytes(self._make_packet(auth_params, Operation.AUTH))

    async def _message_loop(self):
        # 如果之前未初始化则初始化
        if self._host_server_token is None:
            if not await self.init_room():
                raise InitError('初始化失败')

        retry_count = 0
        while True:
            heartbeat_future = None
            try:
                # 连接
                host_server = self._host_server_list[retry_count % len(self._host_server_list)]
                async with self._session.ws_connect(
                    f'wss://{host_server["host"]}:{host_server["wss_port"]}/sub',
                    ssl=self._ssl
                ) as websocket:
                    self._websocket = websocket
                    await self._send_auth()
                    heartbeat_future = asyncio.ensure_future(self._heartbeat_loop(), loop=self._loop)
                    heartbeat_future.add_done_callback(
                        lambda _future: logger.debug('room %d 心跳循环结束', self.room_id)
                    )

                    # 处理消息
                    async for message in websocket:  # type: aiohttp.WSMessage
                        retry_count = 0
                        if message.type == aiohttp.WSMsgType.BINARY:
                            try:
                                await self._handle_message(message.data)
                            except BaseException as e:
                                if type(e) in (
                                    asyncio.CancelledError, aiohttp.ClientConnectionError,
                                    asyncio.TimeoutError, ssl_.SSLError
                                ):
                                    raise
                                logger.exception('room %d 处理消息时发生错误：', self.room_id)
                        else:
                            logger.warning('room %d 未知的websocket消息：type=%s %s', self.room_id,
                                           message.type, message.data)

            except asyncio.CancelledError:
                break
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
                # 重连
                pass
            except ssl_.SSLError:
                logger.exception('SSL错误：')
                # 证书错误时无法重连
                break
            finally:
                if heartbeat_future is not None:
                    heartbeat_future.cancel()
                    try:
                        await heartbeat_future
                    except asyncio.CancelledError:
                        break
                self._websocket = None

            retry_count += 1
            logger.warning('room %d 掉线重连中%d', self.room_id, retry_count)
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    async def _heartbeat_loop(self):
        while True:
            try:
                await self._websocket.send_bytes(self._make_packet({}, Operation.HEARTBEAT))
                await asyncio.sleep(self._heartbeat_interval)

            except (asyncio.CancelledError, aiohttp.ClientConnectionError):
                break

    async def _handle_message(self, data):
        offset = 0
        while offset < len(data):
            try:
                header = HeaderTuple(*HEADER_STRUCT.unpack_from(data, offset))
            except struct.error:
                break

            if header.operation == Operation.HEARTBEAT_REPLY:
                popularity = int.from_bytes(data[offset + HEADER_STRUCT.size:
                                                 offset + HEADER_STRUCT.size + 4],
                                            'big')
                await self._on_receive_popularity(popularity)

            elif header.operation == Operation.SEND_MSG_REPLY:
                body = data[offset + HEADER_STRUCT.size: offset + header.pack_len]
                if header.ver == WS_BODY_PROTOCOL_VERSION_DEFLATE:
                    body = zlib.decompress(body)
                    await self._handle_message(body)
                else:
                    try:
                        body = json.loads(body.decode('utf-8'))
                        await self._handle_command(body)
                    except BaseException:
                        logger.error('body: %s', body)
                        raise

            elif header.operation == Operation.AUTH_REPLY:
                await self._websocket.send_bytes(self._make_packet({}, Operation.HEARTBEAT))

            else:
                body = data[offset + HEADER_STRUCT.size: offset + header.pack_len]
                logger.warning('room %d 未知包类型：operation=%d %s%s', self.room_id,
                               header.operation, header, body)

            offset += header.pack_len

    async def _handle_command(self, command):
        if isinstance(command, list):
            for one_command in command:
                await self._handle_command(one_command)
            return

        cmd = command.get('cmd', '')
        pos = cmd.find(':')  # 2019-5-29 B站弹幕升级新增了参数
        if pos != -1:
            cmd = cmd[:pos]
        if cmd in self._COMMAND_HANDLERS:
            handler = self._COMMAND_HANDLERS[cmd]
            if handler is not None:
                await handler(self, command)
        else:
            logger.warning('room %d 未知命令：cmd=%s %s', self.room_id, cmd, command)
            self._COMMAND_HANDLERS[cmd] = None

    async def _on_receive_popularity(self, popularity: int):
        """
        收到人气值
        """
        pass

    async def _on_receive_danmaku(self, danmaku: DanmakuMessage):
        """
        收到弹幕
        """
        pass

    async def _on_receive_gift(self, gift: GiftMessage):
        """
        收到礼物
        """
        pass

    async def _on_buy_guard(self, message: GuardBuyMessage):
        """
        有人上舰
        """
        pass

    async def _on_super_chat(self, message: SuperChatMessage):
        """
        醒目留言
        """
        pass

    async def _on_super_chat_delete(self, message: SuperChatDeleteMessage):
        """
        删除醒目留言
        """
        pass
