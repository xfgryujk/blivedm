# -*- coding: utf-8 -*-

import asyncio

from blivedm import BLiveClient


class MyBLiveClient(BLiveClient):

    async def _on_get_popularity(self, popularity):
        print('当前人气值：', popularity)

    async def _on_get_danmaku(self, content, user_name):
        print(user_name, '说：', content)


async def async_main():
    # 139是黑桐谷歌的直播间
    # 如果SSL验证失败就把第二个参数设为False
    client = MyBLiveClient(139, True)
    future = client.run()
    try:
        # 5秒后停止，测试用
        # await asyncio.sleep(5)
        # future.cancel()

        await future
    finally:
        await client.close()


def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(async_main())
    finally:
        loop.close()


if __name__ == '__main__':
    main()
