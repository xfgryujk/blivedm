# -*- coding: utf-8 -*-
import asyncio
import http.cookies
import random
from typing import *
from pyttsx3Speech import text_to_speech

import aiohttp

import blivedm
import blivedm.models.web as web_models

# 直播间ID的取值看直播间URL
TEST_ROOM_IDS = [
    12235923,
    14327465,
    21396545,
    21449083,
    23105590,
]

# 这里填一个已登录账号的cookie。不填cookie也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = ''

session: Optional[aiohttp.ClientSession] = None

async def main():
    init_session()
    try:
        await run_single_client()
        await run_multi_clients()
    finally:
        await session.close()


def init_session():
    cookies = http.cookies.SimpleCookie()
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    global session
    session = aiohttp.ClientSession()
    session.cookie_jar.update_cookies(cookies)


async def run_single_client():
    """
    演示监听一个直播间
    """
    room_id = random.choice(TEST_ROOM_IDS)
    client = blivedm.BLiveClient(room_id, session=session)
    handler = MyHandler()
    client.set_handler(handler)

    client.start()
    try:
        # 演示5秒后停止
        await asyncio.sleep(5)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()


async def run_multi_clients():
    """
    演示同时监听多个直播间
    """
    clients = [blivedm.BLiveClient(room_id, session=session) for room_id in TEST_ROOM_IDS]
    handler = MyHandler()
    for client in clients:
        client.set_handler(handler)
        client.start()

    try:
        await asyncio.gather(*(
            client.join() for client in clients
        ))
    finally:
        await asyncio.gather(*(
            client.stop_and_close() for client in clients
        ))


class MyHandler(blivedm.BaseHandler):    # 类变量，将被所有类的实例共享

    # 心跳监听
    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        print(f'[{client.room_id}] 心跳')

    # 进入直播间
    def _on_inter(self, client: blivedm.BLiveClient, data: web_models.UserInData):
        print(f'[{client.room_id}] {data.uname} 进入直播间了')
        text_to_speech(f'欢迎 {data.uname} 进入直播间，老板常来玩啊！')

    # 弹幕消息
    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        print(f'[{client.room_id}] {message.uname}：{message.msg}')
        msg = message.msg
        try:
            msg = split_and_reassemble(int(message.msg))
        except (ValueError, TypeError):
            msg = msg
        finally:
            text_to_speech(f'{message.uname} 说：{msg}')


    # 特殊弹幕通知
    def _on_spacial_danmaku(self, client: blivedm.BLiveClient, message: web_models.SpacialDanMaku):
        # 使用 for 循环输出 content_segments 中的 text 属性
        for content in message.content_segments:
            print(f'[{content.text}')
            text_to_speech(f'{content.text}')

    # 礼物信息
    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        print(f'[{client.room_id}] {message.uname} 赠送{message.gift_name}x{message.num}'
              f' （{message.coin_type}瓜子x{message.total_coin}）')
        text_to_speech(f'感谢 {message.uname} 赠送的 {message.num}个 {message.gift_name}，谢谢老板，老板大气！')

    # 舰长？
    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        print(f'[{client.room_id}] {message.username} 购买{message.gift_name}')

    # 点赞消息处理：PS：可能存在并发问题
    def _click_like(self, client:blivedm.BLiveClient, data: web_models.ClickData):
        if len(data.uname) != 0:
            print(f'[{client.room_id}] {data.uname} {data.like_text}')
            text_to_speech(f'感谢 {data.uname} {data.like_text}')
        else:
            # 点赞数量更新，本场直播的总点赞数量
            print(f'[{client.room_id}] 本次直播点赞数量达到 {data.click_count} 次')
            text_to_speech(f'本次直播点赞数量达到 {data.click_count} 次')


    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        print(f'[{client.room_id}] 醒目留言 ¥{message.price} {message.uname}：{message.message}')


def split_and_reassemble(number):
    # 将数字转换为字符串
    num_str = str(number)
    # 将每个字符转换为字符串列表
    digits = [char for char in num_str]
    # 重新组装成带逗号的字符串
    result_str = ",".join(digits)
    return result_str


if __name__ == '__main__':
    asyncio.run(main())
