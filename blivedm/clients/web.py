# -*- coding: utf-8 -*-
import asyncio
import datetime
import hashlib
import logging
import urllib
import weakref
from typing import *

import aiohttp
import yarl

from . import ws_base
from .. import utils

__all__ = (
    'BLiveClient',
)

logger = logging.getLogger('blivedm')

UID_INIT_URL = 'https://api.bilibili.com/x/web-interface/nav'
WBI_INIT_URL = UID_INIT_URL
BUVID_INIT_URL = 'https://www.bilibili.com/'
ROOM_INIT_URL = 'https://api.live.bilibili.com/room/v1/Room/get_info'
DANMAKU_SERVER_CONF_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo'
DEFAULT_DANMAKU_SERVER_LIST = [
    {'host': 'broadcastlv.chat.bilibili.com', 'port': 2243, 'wss_port': 443, 'ws_port': 2244}
]

_session_to_wbi_signer = weakref.WeakKeyDictionary()


def _get_wbi_signer(session: aiohttp.ClientSession) -> '_WbiSigner':
    wbi_signer = _session_to_wbi_signer.get(session, None)
    if wbi_signer is None:
        wbi_signer = _session_to_wbi_signer[session] = _WbiSigner(session)
    return wbi_signer


class _WbiSigner:
    WBI_KEY_INDEX_TABLE = [
        46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
        27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13
    ]
    """wbi密码表"""
    WBI_KEY_TTL = datetime.timedelta(hours=11, minutes=59, seconds=30)

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

        self._wbi_key = ''
        """缓存的wbi鉴权口令"""
        self._refresh_future: Optional[Awaitable] = None
        """用来避免同时刷新"""
        self._last_refresh_time: Optional[datetime.datetime] = None

    @property
    def wbi_key(self):
        """
        缓存的wbi鉴权口令
        """
        return self._wbi_key

    def reset(self):
        self._wbi_key = ''
        self._last_refresh_time = None

    @property
    def need_refresh_wbi_key(self):
        return self._wbi_key == '' or (
            self._last_refresh_time is not None
            and datetime.datetime.now() - self._last_refresh_time >= self.WBI_KEY_TTL
        )

    def refresh_wbi_key(self) -> Awaitable:
        if self._refresh_future is None:
            self._refresh_future = asyncio.create_task(self._do_refresh_wbi_key())

            def on_done(_fu):
                self._refresh_future = None
            self._refresh_future.add_done_callback(on_done)

        return self._refresh_future

    async def _do_refresh_wbi_key(self):
        wbi_key = await self._get_wbi_key()
        if wbi_key == '':
            return

        self._wbi_key = wbi_key
        self._last_refresh_time = datetime.datetime.now()

    async def _get_wbi_key(self):
        try:
            async with self._session.get(
                WBI_INIT_URL,
                headers={'User-Agent': utils.USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('WbiSigner failed to get wbi key: status=%d %s', res.status, res.reason)
                    return ''
                data = await res.json()
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('WbiSigner failed to get wbi key:')
            return ''

        try:
            wbi_img = data['data']['wbi_img']
            img_key = wbi_img['img_url'].rpartition('/')[2].partition('.')[0]
            sub_key = wbi_img['sub_url'].rpartition('/')[2].partition('.')[0]
        except KeyError:
            logger.warning('WbiSigner failed to get wbi key: data=%s', data)
            return ''

        shuffled_key = img_key + sub_key
        wbi_key = []
        for index in self.WBI_KEY_INDEX_TABLE:
            if index < len(shuffled_key):
                wbi_key.append(shuffled_key[index])
        return ''.join(wbi_key)

    def add_wbi_sign(self, params: dict):
        if self._wbi_key == '':
            return params

        wts = str(int(datetime.datetime.now().timestamp()))
        params_to_sign = {**params, 'wts': wts}

        # 按key字典序排序
        params_to_sign = {
            key: params_to_sign[key]
            for key in sorted(params_to_sign.keys())
        }
        # 过滤一些字符
        for key, value in params_to_sign.items():
            value = ''.join(
                ch
                for ch in str(value)
                if ch not in "!'()*"
            )
            params_to_sign[key] = value

        str_to_sign = urllib.parse.urlencode(params_to_sign) + self._wbi_key
        w_rid = hashlib.md5(str_to_sign.encode('utf-8')).hexdigest()
        return {
            **params,
            'wts': wts,
            'w_rid': w_rid
        }


class BLiveClient(ws_base.WebSocketClientBase):
    """
    web端客户端

    :param room_id: URL中的房间ID，可以用短ID
    :param uid: B站用户ID，0表示未登录，None表示自动获取
    :param session: cookie、连接池
    :param heartbeat_interval: 发送心跳包的间隔时间（秒）
    """

    def __init__(
        self,
        room_id: int,
        *,
        uid: Optional[int] = None,
        session: Optional[aiohttp.ClientSession] = None,
        heartbeat_interval=30,
    ):
        super().__init__(session, heartbeat_interval)
        self._wbi_signer = _get_wbi_signer(self._session)

        self._tmp_room_id = room_id
        """用来init_room的临时房间ID，可以用短ID"""
        self._uid = uid

        # 在调用init_room后初始化的字段
        self._room_owner_uid: Optional[int] = None
        """主播用户ID"""
        self._host_server_list: Optional[List[dict]] = None
        """
        弹幕服务器列表

        `[{host: "tx-bj4-live-comet-04.chat.bilibili.com", port: 2243, wss_port: 443, ws_port: 2244}, ...]`
        """
        self._host_server_token: Optional[str] = None
        """连接弹幕服务器用的token"""

    @property
    def tmp_room_id(self) -> int:
        """
        构造时传进来的room_id参数
        """
        return self._tmp_room_id

    @property
    def room_owner_uid(self) -> Optional[int]:
        """
        主播用户ID，调用init_room后初始化
        """
        return self._room_owner_uid

    @property
    def uid(self) -> Optional[int]:
        """
        当前登录的用户ID，未登录则为0，调用init_room后初始化
        """
        return self._uid

    async def init_room(self):
        """
        初始化连接房间需要的字段

        :return: True代表没有降级，如果需要降级后还可用，重载这个函数返回True
        """
        if self._uid is None:
            if not await self._init_uid():
                logger.warning('room=%d _init_uid() failed', self._tmp_room_id)
                self._uid = 0

        if self._get_buvid() == '':
            if not await self._init_buvid():
                logger.warning('room=%d _init_buvid() failed', self._tmp_room_id)

        res = True
        if not await self._init_room_id_and_owner():
            res = False
            # 失败了则降级
            self._room_id = self._tmp_room_id
            self._room_owner_uid = 0

        if not await self._init_host_server():
            res = False
            # 失败了则降级
            self._host_server_list = DEFAULT_DANMAKU_SERVER_LIST
            self._host_server_token = None
        return res

    async def _init_uid(self):
        cookies = self._session.cookie_jar.filter_cookies(yarl.URL(UID_INIT_URL))
        sessdata_cookie = cookies.get('SESSDATA', None)
        if sessdata_cookie is None or sessdata_cookie.value == '':
            # cookie都没有，不用请求了
            self._uid = 0
            return True

        try:
            async with self._session.get(
                UID_INIT_URL,
                headers={'User-Agent': utils.USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_uid() failed, status=%d, reason=%s', self._tmp_room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    if data['code'] == -101:
                        # 未登录
                        self._uid = 0
                        return True
                    logger.warning('room=%d _init_uid() failed, message=%s', self._tmp_room_id,
                                   data['message'])
                    return False

                data = data['data']
                if not data['isLogin']:
                    # 未登录
                    self._uid = 0
                else:
                    self._uid = data['mid']
                return True
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_uid() failed:', self._tmp_room_id)
            return False

    def _get_buvid(self):
        cookies = self._session.cookie_jar.filter_cookies(yarl.URL(BUVID_INIT_URL))
        buvid_cookie = cookies.get('buvid3', None)
        if buvid_cookie is None:
            return ''
        return buvid_cookie.value

    async def _init_buvid(self):
        try:
            async with self._session.get(
                BUVID_INIT_URL,
                headers={'User-Agent': utils.USER_AGENT},
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_buvid() status error, status=%d, reason=%s',
                                   self._tmp_room_id, res.status, res.reason)
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_buvid() exception:', self._tmp_room_id)
        return self._get_buvid() != ''

    async def _init_room_id_and_owner(self):
        try:
            async with self._session.get(
                ROOM_INIT_URL,
                headers={'User-Agent': utils.USER_AGENT},
                params={
                    'room_id': self._tmp_room_id
                },
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_room_id_and_owner() failed, status=%d, reason=%s', self._tmp_room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('room=%d _init_room_id_and_owner() failed, message=%s', self._tmp_room_id,
                                   data['message'])
                    return False
                if not self._parse_room_init(data['data']):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_room_id_and_owner() failed:', self._tmp_room_id)
            return False
        return True

    def _parse_room_init(self, data):
        self._room_id = data['room_id']
        self._room_owner_uid = data['uid']
        return True

    async def _init_host_server(self):
        if self._wbi_signer.need_refresh_wbi_key:
            await self._wbi_signer.refresh_wbi_key()
            # 如果没刷新成功先用旧的key
            if self._wbi_signer.wbi_key == '':
                logger.exception('room=%d _init_host_server() failed: no wbi key', self._room_id)
                return False

        try:
            async with self._session.get(
                DANMAKU_SERVER_CONF_URL,
                headers={'User-Agent': utils.USER_AGENT},
                params=self._wbi_signer.add_wbi_sign({
                    'id': self._room_id,
                    'type': 0
                }),
            ) as res:
                if res.status != 200:
                    logger.warning('room=%d _init_host_server() failed, status=%d, reason=%s', self._room_id,
                                   res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    if data['code'] == -352:
                        # wbi签名错误
                        self._wbi_signer.reset()
                    logger.warning('room=%d _init_host_server() failed, message=%s', self._room_id, data['message'])
                    return False
                if not self._parse_danmaku_server_conf(data['data']):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('room=%d _init_host_server() failed:', self._room_id)
            return False
        return True

    def _parse_danmaku_server_conf(self, data):
        self._host_server_list = data['host_list']
        self._host_server_token = data['token']
        if not self._host_server_list:
            logger.warning('room=%d _parse_danmaku_server_conf() failed: host_server_list is empty', self._room_id)
            return False
        return True

    async def _on_before_ws_connect(self, retry_count):
        """
        在每次建立连接之前调用，可以用来初始化房间
        """
        # 重连次数太多则重新init_room，保险
        reinit_period = max(3, len(self._host_server_list or ()))
        if retry_count > 0 and retry_count % reinit_period == 0:
            self._need_init_room = True
        await super()._on_before_ws_connect(retry_count)

    def _get_ws_url(self, retry_count) -> str:
        """
        返回WebSocket连接的URL，可以在这里做故障转移和负载均衡
        """
        host_server = self._host_server_list[retry_count % len(self._host_server_list)]
        return f"wss://{host_server['host']}:{host_server['wss_port']}/sub"

    async def _send_auth(self):
        """
        发送认证包
        """
        auth_params = {
            'uid': self._uid,
            'roomid': self._room_id,
            'protover': 3,
            'platform': 'web',
            'type': 2,
            'buvid': self._get_buvid(),
        }
        if self._host_server_token is not None:
            auth_params['key'] = self._host_server_token
        await self._websocket.send_bytes(self._make_packet(auth_params, ws_base.Operation.AUTH))
