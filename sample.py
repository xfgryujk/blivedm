# -*- coding: utf-8 -*-

import asyncio
from time import time
from blivedm import DanmuPrinter

async def test1():
    connection = DanmuPrinter(23058, 0)
    task_run = asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(30)
    print(time(), 'closing')
    await connection.close()
    print(time(), 'closed')
    await task_run
    print(time(), 'all done')


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test1())
    loop.close()


if __name__ == '__main__':
    main()
