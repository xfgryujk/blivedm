# -*- coding: utf-8 -*-
import asyncio
import blivedm

TEST_AUTH_CODE = ''
APP_ID = ''
ACCESS_KEY = ''
ACCESS_KEY_SECRET = ''

class OpenLiveHandlerInterface:
    """
    开放平台直播消息处理器接口
    """

    async def handle(self, client: blivedm.BLiveClient, command: dict):
        print(f'{command}')

async def main():
    await run_start()

async def run_start():
    client = blivedm.BLiveClient(use_open_live=True, open_live_app_id=APP_ID, open_live_access_key=ACCESS_KEY, open_live_access_secret=ACCESS_KEY_SECRET, open_live_code=TEST_AUTH_CODE, ssl=True)
    handler = OpenLiveHandlerInterface()
    client.add_handler(handler)

    client.start()
    try:
        # 演示60秒后停止
        await asyncio.sleep(600)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()

if __name__ == '__main__':
    asyncio.run(main())