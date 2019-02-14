import asyncio
import struct
import json
import sys
import aiohttp


class BaseDanmu():
    structer = struct.Struct('!I2H2I')

    def __init__(self, room_id, area_id, client_session=None):
        if client_session is None:
            self.client = aiohttp.ClientSession()
        else:
            self.client = client_session
        self.ws = None
        self._area_id = area_id
        self.room_id = room_id
        # 建立连接过程中难以处理重设置房间问题
        self.lock_for_reseting_roomid_manually = asyncio.Lock()
        self.task_main = None
        self._bytes_heartbeat = self._wrap_str(opt=2, body='')
    
    @property
    def room_id(self):
        return self._room_id
        
    @room_id.setter
    def room_id(self, room_id):
        self._room_id = room_id
        str_conn_room = f'{{"uid":0,"roomid":{room_id},"protover":1,"platform":"web","clientver":"1.3.3"}}'
        self._bytes_conn_room = self._wrap_str(opt=7, body=str_conn_room)
        
    def _wrap_str(self, opt, body, len_header=16, ver=1, seq=1):
        remain_data = body.encode('utf-8')
        len_data = len(remain_data) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        data = header + remain_data
        return data

    async def _send_bytes(self, bytes_data):
        try:
            await self.ws.send_bytes(bytes_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        return True

    async def _read_bytes(self):
        bytes_data = None
        try:
            # 如果调用aiohttp的bytes read，none的时候，会raise exception
            msg = await asyncio.wait_for(self.ws.receive(), timeout=35.0)
            bytes_data = msg.data
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0], sys.exc_info()[1])
            print('请联系开发者')
            return None
        
        return bytes_data
        
    async def open(self):
        try:
            url = 'wss://broadcastlv.chat.bilibili.com:443/sub'
            self.ws = await asyncio.wait_for(self.client.ws_connect(url), timeout=3)
        except:
            print("# 连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0], sys.exc_info()[1])
            return False
        print(f'{self._area_id}号弹幕监控已连接b站服务器')
        return (await self._send_bytes(self._bytes_conn_room))
        
    async def heart_beat(self):
        try:
            while True:
                if not (await self._send_bytes(self._bytes_heartbeat)):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
            
    async def read_datas(self):
        while True:
            datas = await self._read_bytes()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if datas is None:
                return
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l = next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.structer.unpack_from(datas[data_l:])
                len_data, len_header, ver, opt, seq = tuple_header
                body_l = data_l + len_header
                next_data_l = data_l + len_data
                body = datas[body_l:next_data_l]
                # 人气值(或者在线人数或者类似)以及心跳
                if opt == 3:
                    # UserCount, = struct.unpack('!I', remain_data)
                    # printer.debug(f'弹幕心跳检测{self._area_id}')
                    pass
                # cmd
                elif opt == 5:
                    if not self.handle_danmu(body):
                        return
                # 握手确认
                elif opt == 8:
                    print(f'{self._area_id}号弹幕监控进入房间（{self._room_id}）')
                else:
                    print(datas[data_l:next_data_l])

                data_l = next_data_l

    # 待确认
    async def close(self):
        try:
            await self.ws.close()
        except:
            print('请联系开发者', sys.exc_info()[0], sys.exc_info()[1])
        if not self.ws.closed:
            print(f'请联系开发者  {self._area_id}号弹幕收尾模块状态{self.ws.closed}')
                
    def handle_danmu(self, body):
        return True
        
    async def run_forever(self):
        while True:
            print(f'正在启动{self._area_id}号弹幕姬')
            
            async with self.lock_for_reseting_roomid_manually:
                is_open = await self.open()
            if not is_open:
                continue
            self.task_main = asyncio.ensure_future(self.read_datas())
            task_heartbeat = asyncio.ensure_future(self.heart_beat())
            tasks = [self.task_main, task_heartbeat]
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            print(f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息')
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self.close()
            await asyncio.wait(pending)
            print(f'{self._area_id}号弹幕姬退出，剩余任务处理完毕')
            
    async def reconnect(self, room_id):
        async with self.lock_for_reseting_roomid_manually:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            if self.ws is not None:
                await self.close()
            if self.task_main is not None:
                await self.task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self.room_id = room_id
            print(f'{self._area_id}号弹幕姬已经切换房间（{room_id}）')
    
    
class DanmuPrinter(BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            print(dic)
        return True

