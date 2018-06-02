# -*- coding: utf-8 -*-

import json
import struct
from asyncio import gather, sleep, CancelledError
from collections import namedtuple
from enum import IntEnum
# noinspection PyProtectedMember
from ssl import _create_unverified_context

import requests
import websockets
from websockets.exceptions import ConnectionClosed


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

    def __init__(self, room_id, ssl=True, loop=None):
        """
        :param room_id: URL中的房间ID
        :param ssl: True表示用默认的SSLContext验证，False表示不验证，也可以传入SSLContext
        :param loop: 协程事件循环
        """
        self._short_id = room_id
        self._room_id = None
        self._ssl = ssl if ssl else _create_unverified_context()
        self._websocket = None
        # 未登录
        self._uid = 0

        self._loop = loop
        self._future = None

    def start(self):
        """
        创建相关的协程，不会执行事件循环
        :raise ConnectionError: 获取房间ID失败
        :return: True表示成功创建协程，False表示之前创建的协程未结束
        """
        if self._future is not None:
            return False

        # 获取房间ID
        if self._room_id is None:
            res = requests.get(self.ROOM_INIT_URL, {'id': self._short_id})
            if res.status_code != 200:
                raise ConnectionError()
            else:
                self._room_id = res.json()['data']['room_id']

        # 创建协程
        self._future = gather(
            self._message_loop(),
            self._heartbeat_loop(),
            loop=self._loop
        )

        def on_done(_future):
            self._future = None
        self._future.add_done_callback(on_done)
        return True

    def stop(self, callback=None):
        """
        取消相关的协程，不会停止事件循环
        :param callback: 协程结束后调用
        """
        if self._future is None or self._future.cancelled():
            return

        if callback is not None:
            self._future.add_done_callback(lambda future: callback())
        self._future.cancel()

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

    async def _message_loop(self):
        while True:
            try:
                # 连接
                async with websockets.connect(self.WEBSOCKET_URL, ssl=self._ssl, loop=self._loop) as websocket:
                    self._websocket = websocket
                    await self._send_auth()

                    # 处理消息
                    async for message in websocket:
                        await self._handle_message(message)

            except CancelledError:
                break
            except ConnectionClosed:
                self._websocket = None
                # 重连
                print('掉线重连中')
                try:
                    await sleep(5)
                except CancelledError:
                    break
                continue
            finally:
                self._websocket = None

    async def _send_auth(self):
        auth_params = {
            'uid':       self._uid,
            'roomid':    self._room_id,
            'protover':  1,
            'platform':  'web',
            'clientver': '1.4.0'
        }
        await self._websocket.send(self._make_packet(auth_params, Operation.AUTH))

    async def _heartbeat_loop(self):
        while True:
            try:
                if self._websocket is None:
                    await sleep(0.5)
                else:
                    await self._websocket.send(self._make_packet({}, Operation.SEND_HEARTBEAT))
                    await sleep(30)

            except CancelledError:
                break
            except ConnectionClosed:
                # 等待重连
                continue

    async def _handle_message(self, message):
        offset = 0
        while offset < len(message):
            try:
                header = self.HeaderTuple(*self.HEADER_STRUCT.unpack_from(message, offset))
            except struct.error:
                break

            if header.operation == Operation.POPULARITY:
                popularity = int.from_bytes(message[offset + self.HEADER_STRUCT.size:
                                                    offset + self.HEADER_STRUCT.size + 4]
                                            , 'big')
                await self._on_get_popularity(popularity)

            elif header.operation == Operation.COMMAND:
                body = message[offset + self.HEADER_STRUCT.size: offset + header.total_len]
                body = json.loads(body.decode('utf-8'))
                await self._handle_command(body)

            elif header.operation == Operation.RECV_HEARTBEAT:
                await self._websocket.send(self._make_packet({}, Operation.SEND_HEARTBEAT))

            else:
                body = message[offset + self.HEADER_STRUCT.size: offset + header.total_len]
                print('未知包类型：', header, body)

            offset += header.total_len

    async def _handle_command(self, command):
        if isinstance(command, list):
            for one_command in command:
                await self._handle_command(one_command)
            return

        cmd = command['cmd']
        # print(command)

        if cmd == 'DANMU_MSG':        # 收到弹幕
            await self._on_get_danmaku(command['info'][1], command['info'][2][1])

        elif cmd == 'SEND_GIFT':      # 送礼物
            pass

        elif cmd == 'WELCOME':        # 欢迎
            pass

        elif cmd == 'WELCOME_GUARD':  # 欢迎房管
            pass

        elif cmd == 'SYS_MSG':        # 系统消息
            pass

        elif cmd == 'PREPARING':      # 房主准备中
            pass

        elif cmd == 'LIVE':           # 直播开始
            pass

        elif cmd == 'WISH_BOTTLE':    # 许愿瓶？
            pass

        else:
            print('未知命令：', command)

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
