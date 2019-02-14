# -*- coding: utf-8 -*-

from asyncio import get_event_loop
from blivedm import DanmuPrinter


def main():
    loop = get_event_loop()
    loop.run_until_complete(DanmuPrinter(23058, 0).run_forever())
    loop.close()


if __name__ == '__main__':
    main()
