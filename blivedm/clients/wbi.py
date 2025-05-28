import hashlib
import logging
import time
import urllib.parse
from typing import Any, Dict

import aiohttp

from ..utils import USER_AGENT

logger = logging.getLogger("blivedm")

UID_INIT_URL = "https://api.bilibili.com/x/web-interface/nav"

WTS = "wts"
W_RID = "w_rid"

KEY_LENGTH = 32

# fmt: off
KEY_MAP = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]
# fmt: on

INVALID_CHARS = ["!", "'", "(", ")", "*"]


def filtered_string(s: str) -> str:
    return "".join(c for c in s if c not in INVALID_CHARS)


def extract_key_part(url: str) -> str:
    slash = url.rfind("/")
    if slash == -1:
        raise ValueError("missing url slash")
    dot = url[slash:].find(".")
    if dot == -1:
        raise ValueError("missing url dot")
    return url[slash + 1 : slash + dot]


def sign_content_with_key(content: str, key: str) -> str:
    hasher = hashlib.md5()
    hasher.update(f"{content}{key}".encode())
    return hasher.hexdigest()


async def get_wbi_key(session: aiohttp.ClientSession) -> str:
    async with session.get(
        UID_INIT_URL,
        headers={"User-Agent": USER_AGENT},
    ) as response:
        data = await response.json()

        wbi_img = data["data"]["wbi_img"]
        img = extract_key_part(wbi_img["img_url"])
        sub = extract_key_part(wbi_img["sub_url"])

        if not img or not sub:
            raise ValueError("missing wbi key")

        full = img + sub
        key_chars = ["\0"] * KEY_LENGTH
        for i, index in enumerate(KEY_MAP[:KEY_LENGTH]):
            key_chars[i] = full[index] if index < len(full) else "\0"

        return "".join(key_chars)


async def signed_query(
    session: aiohttp.ClientSession, query: Dict[str, Any]
) -> Dict[str, str]:
    ts = str(int(time.time()))

    filtered_query = []
    for k, v in query.items():
        filtered_query.append((k, filtered_string(str(v))))

    filtered_query.append((WTS, ts))
    filtered_query.sort(key=lambda x: x[0])

    content = urllib.parse.urlencode(filtered_query)

    try:
        key = await get_wbi_key(session)
    except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError, ValueError):
        logger.exception("get_wbi_key() failed:")
        return query

    query_sign = sign_content_with_key(content, key)

    signed_query = {
        **query,
        WTS: ts,
        W_RID: query_sign,
    }

    return signed_query
