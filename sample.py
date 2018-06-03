# -*- coding: utf-8 -*-

import sys
from asyncio import get_event_loop
from ssl import SSLError

from blivedm import BLiveClient


class MyBLiveClient(BLiveClient):

    async def _on_get_popularity(self, popularity):
        print('当前人气值：', popularity)

    async def _on_get_danmaku(self, content, user_name):
        print(user_name, '说：', content)

    def _on_stop(self, exc):
        self._loop.stop()

    def _handle_error(self, exc):
        print(exc, file=sys.stderr)
        if isinstance(exc, SSLError):
            print('SSL验证失败！', file=sys.stderr)
        return False


def main():
    loop = get_event_loop()

    # 如果SSL验证失败就把第二个参数设为False
    client = MyBLiveClient(139, True)
    client.start()

    # 5秒后停止，测试用
    # loop.call_later(5, client.stop)
    # 按Ctrl+C停止
    # import signal
    # signal.signal(signal.SIGINT, lambda signum, frame: client.stop())

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == '__main__':
    main()
