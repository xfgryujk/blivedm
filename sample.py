# -*- coding: utf-8 -*-

from asyncio import get_event_loop

from blivedm import BLiveClient


class MyBLiveClient(BLiveClient):

    async def _on_get_popularity(self, popularity):
        print('当前人气值：', popularity)

    async def _on_get_danmaku(self, content, user_name):
        print(user_name, '说：', content)


def main():
    loop = get_event_loop()

    client = MyBLiveClient(6, loop)
    client.start()
    loop.call_later(5, client.stop, loop.stop)

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == '__main__':
    main()
