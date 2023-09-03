# -*- coding: utf-8 -*-
import asyncio

import blivedm
import blivedm.open_live_client as open_live_client

ACCESS_KEY = ''
ACCESS_SECRET = ''
APP_ID = 0
ROOM_OWNER_AUTH_CODE = ''


async def main():
    await run_single_client()


async def run_single_client():
    """
    演示监听一个直播间
    """
    client = open_live_client.OpenLiveClient(
        access_key=ACCESS_KEY,
        access_secret=ACCESS_SECRET,
        app_id=APP_ID,
        room_owner_auth_code=ROOM_OWNER_AUTH_CODE,
    )
    handler = MyHandler()
    client.add_handler(handler)

    client.start()
    try:
        # 演示70秒后停止
        await asyncio.sleep(70)
        client.stop()

        await client.join()
    finally:
        await client.stop_and_close()


class MyHandler(blivedm.HandlerInterface):
    async def handle(self, client: open_live_client.OpenLiveClient, command: dict):
        print(command)


if __name__ == '__main__':
    asyncio.run(main())
