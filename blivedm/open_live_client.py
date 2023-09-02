# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import hashlib
import hmac
import logging
import random
import ssl as ssl_
import time
import json
from hashlib import sha256
from typing import *

logger = logging.getLogger('open-live-client')

OPEN_LIVE_START_URL = 'https://live-open.biliapi.com/v2/app/start'
OPEN_LIVE_HEARTBEAT_URL = 'https://live-open.biliapi.com/v2/app/heartbeat'
OPEN_LIVE_END_URL = 'https://live-open.biliapi.com/v2/app/end'

class OpenLiveClient:
    def __init__(
        self,
        app_id: int,
        access_key: str,
        access_secret: str,
        session: Optional[aiohttp.ClientSession] = None,
        ssl: Union[bool, ssl_.SSLContext] = True,
    ):
        self.app_id = app_id
        self.access_key = access_key
        self.access_secret = access_secret
        self.session = session
    
        if session is None:
          self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
          self._own_session = True
        else:
          self._session = session
          self._own_session = False
          assert self._session.loop is asyncio.get_event_loop()  # noqa
        self._ssl = ssl if ssl else ssl_._create_unverified_context()  # noqa

    @property
    def game_id(self) -> Optional[int]:
        return self._game_id
    
    @property
    def ws_auth_body(self) -> Optional[Dict]:
        return self._ws_auth_body
    
    @property
    def wss_link(self) -> Optional[List[str]]:
        return self._wss_link
    
    @property
    def anchor_room_id(self) -> Optional[int]:
        return self._anchor_room_id
    
    @property
    def anchor_uname(self) -> Optional[str]:
        return self._anchor_uname
    
    @property
    def anchor_uface(self) -> Optional[str]:
        return self._anchor_uface
    
    @property
    def anchor_uid(self) -> Optional[int]:
        return self._anchor_uid
    
    def _sign_request_header(
        self,
        body: str,
    ):
        md5 = hashlib.md5()
        md5.update(body.encode())
        ts = time.time()
        nonce = random.randint(1,100000)+time.time()
        md5data = md5.hexdigest()
        headerMap = {
            "x-bili-timestamp": str(int(ts)),
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": str(nonce),
            "x-bili-accesskeyid": self.access_key,
            "x-bili-signature-version": "1.0",
            "x-bili-content-md5": md5data,
        }
        headerList = sorted(headerMap)
        headerStr = ''

        for key in headerList:
            headerStr = headerStr+ key+":"+str(headerMap[key])+"\n"
        headerStr = headerStr.rstrip("\n")

        appsecret = self.access_secret.encode()
        data = headerStr.encode()

        signature = hmac.new(appsecret, data, digestmod=sha256).hexdigest()
        headerMap["Authorization"] = signature
        headerMap["Content-Type"] = "application/json"
        headerMap["Accept"] = "application/json"
        return headerMap
    
    # 通过身份码获取直播间及wss连接信息
    async def start(
        self,
        code: str
    ):
        try:
            params = f'{{"code":"{code}","app_id":{self.app_id}}}'
            headers = self._sign_request_header(params)
            async with self._session.post(
                OPEN_LIVE_START_URL, headers=headers, data=params, ssl=self._ssl
            ) as res:
                if res.status != 200:
                    logger.warning('app=%d start failed, status=%d, reason=%s', self.app_id, res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('app=%d start failed, code=%d, message=%s', self.app_id, data['code'], data['message'])
                    return False
                if not self._parse_start_data(
                    data
                ):
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('app=%d start failed', self.app_id)
            return False
        return True
    
    def _parse_start_data(
        self,
        data: dict
    ):
        self._game_id = data['data']['game_info']['game_id']
        self._ws_auth_body = json.loads(data['data']['websocket_info']['auth_body'])
        self._wss_link = data['data']['websocket_info']['wss_link']
        self._anchor_room_id = data['data']['anchor_info']['room_id']
        self._anchor_uname = data['data']['anchor_info']['uname']
        self._anchor_uface = data['data']['anchor_info']['uface']
        self._anchor_uid = data['data']['anchor_info']['uid']
        return True

    async def end(
        self
    ):
        if not self._game_id:
            logger.warning('app=%d end failed, game_id not found', self.app_id)
            return False

        try:
            params = f'{{"game_id":"{self._game_id}", "app_id":{self.app_id}}}'
            headers = self._sign_request_header(params)
            async with self._session.post(
                OPEN_LIVE_END_URL, headers=headers, data=params, ssl=self._ssl
            ) as res:
                if res.status != 200:
                    logger.warning('app=%d end failed, status=%d, reason=%s', self.app_id, res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('app=%d end failed, code=%d, message=%s', self.app_id, data['code'], data['message'])
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('app=%d end failed', self.app_id)
            return False
        return True
    
    # 开放平台互动玩法心跳, 用于维持直播间内定制礼物及统计使用数据, 非互动玩法类暂时不需要
    async def heartbeat(
        self
    ):
        if not self._game_id:
            logger.warning('game=%d heartbeat failed, game_id not found', self._game_id)
            return False
        
        try:
            params = f'{{"game_id":"{self._game_id}"}}'
            headers = self._sign_request_header(params)
            async with self._session.post(
                OPEN_LIVE_HEARTBEAT_URL, headers=headers, data=params, ssl=self._ssl
            ) as res:
                if res.status != 200:
                    logger.warning('game=%d heartbeat failed, status=%d, reason=%s', self._game_id, res.status, res.reason)
                    return False
                data = await res.json()
                if data['code'] != 0:
                    logger.warning('game=%d heartbeat failed, code=%d, message=%s', self._game_id, data['code'], data['message'])
                    return False
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            logger.exception('game=%d heartbeat failed', self._game_id)
            return False
        return True