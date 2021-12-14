# -*- coding: utf-8 -*-
import asyncio

import blivedm


async def main():
    # 直播间ID的取值看直播间URL
    # 如果SSL验证失败就把ssl设为False，B站真的有过忘续证书的情况
    client = blivedm.BLiveClient(room_id=21449083, ssl=True)
    handler = MyHandler()
    client.add_handler(handler)

    client.start()
    try:
        # 5秒后停止，测试用
        # await asyncio.sleep(5)
        # client.stop()

        await client.join()
    finally:
        await client.close()


class MyHandler(blivedm.BaseHandler):
    # 演示如何添加自定义回调
    _CMD_CALLBACK_DICT = blivedm.BaseHandler._CMD_CALLBACK_DICT.copy()

    # 入场消息回调
    async def __interact_word_callback(self, client: blivedm.BLiveClient, command: dict):
        print(f"INTERACT_WORD: self_type={type(self).__name__}, room_id={client.room_id},"
              f" uname={command['data']['uname']}")
    _CMD_CALLBACK_DICT['INTERACT_WORD'] = __interact_word_callback  # noqa

    async def _on_heartbeat(self, client: blivedm.BLiveClient, message: blivedm.HeartbeatMessage):
        print(f'当前人气值：{message.popularity}')

    async def _on_danmaku(self, client: blivedm.BLiveClient, message: blivedm.DanmakuMessage):
        print(f'{message.uname}：{message.msg}')

    async def _on_gift(self, client: blivedm.BLiveClient, message: blivedm.GiftMessage):
        print(f'{message.uname} 赠送{message.gift_name}x{message.num} （{message.coin_type}币x{message.total_coin}）')

    async def _on_buy_guard(self, client: blivedm.BLiveClient, message: blivedm.GuardBuyMessage):
        print(f'{message.username} 购买{message.gift_name}')

    async def _on_super_chat(self, client: blivedm.BLiveClient, message: blivedm.SuperChatMessage):
        print(f'醒目留言 ¥{message.price} {message.uname}：{message.message}')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
