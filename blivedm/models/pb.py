# -*- coding: utf-8 -*-
import dataclasses
import enum
from typing import *

import pure_protobuf.annotations as pb_anno
import pure_protobuf.message as pb_msg

try:
    Annotated
except NameError:
    from typing_extensions import Annotated  # Python < 3.9


class InteractWordV2MsgType(enum.IntEnum):
    Unknown = 0
    EnterRoom = 1
    Follow = 2
    ShareRoom = 3


@dataclasses.dataclass
class InteractWordV2UserBaseInfo(pb_msg.BaseMessage):
    face: Annotated[str, pb_anno.Field(2)] = ''


@dataclasses.dataclass
class InteractWordV2UserInfo(pb_msg.BaseMessage):
    base: Annotated[InteractWordV2UserBaseInfo, pb_anno.Field(2)] = dataclasses.field(default_factory=InteractWordV2UserBaseInfo)


@dataclasses.dataclass
class InteractWordV2(pb_msg.BaseMessage):
    uid: Annotated[int, pb_anno.Field(1)] = 0
    uname: Annotated[str, pb_anno.Field(2)] = ''
    # 为了防止加新枚举后不兼容，还是用int了
    # msg_type: Annotated[InteractWordV2MsgType, pb_anno.Field(5)] = InteractWordV2MsgType.Unknown
    msg_type: Annotated[int, pb_anno.Field(5)] = 0
    timestamp: Annotated[int, pb_anno.Field(7)] = 0
    uinfo: Annotated[InteractWordV2UserInfo, pb_anno.Field(22)] = dataclasses.field(default_factory=InteractWordV2UserInfo)


# SEND_GIFT_V2（2026-07 灰度的新协议），结构通过逆向所得，字段号可能有缺失，未知字段会被跳过
# 逆向端口来源（MIT License）：https://github.com/lovelyyoshino/Bilibili-Live-API/blob/master/API.live_websocket.md
@dataclasses.dataclass
class SendGiftV2MedalInfo(pb_msg.BaseMessage):
    anchor_uid: Annotated[int, pb_anno.Field(1)] = 0
    medal_level: Annotated[int, pb_anno.Field(5)] = 0
    medal_name: Annotated[str, pb_anno.Field(6)] = ''
    # ? 大航海等级（逆向推断）
    guard_level: Annotated[int, pb_anno.Field(11)] = 0


@dataclasses.dataclass
class SendGiftV2BlindGift(pb_msg.BaseMessage):
    """仅盲盒礼物存在"""
    original_gift_name: Annotated[str, pb_anno.Field(3)] = ''
    blind_price: Annotated[int, pb_anno.Field(6)] = 0


@dataclasses.dataclass
class SendGiftV2GiftEffect(pb_msg.BaseMessage):
    img_basic: Annotated[str, pb_anno.Field(1)] = ''


@dataclasses.dataclass
class SendGiftV2GiftData(pb_msg.BaseMessage):
    gift_id: Annotated[int, pb_anno.Field(1)] = 0
    gift_name: Annotated[str, pb_anno.Field(2)] = ''
    num: Annotated[int, pb_anno.Field(3)] = 0
    gift_type: Annotated[int, pb_anno.Field(4)] = 0
    price: Annotated[int, pb_anno.Field(5)] = 0
    total_coin: Annotated[int, pb_anno.Field(6)] = 0
    coin_type: Annotated[str, pb_anno.Field(8)] = ''
    tid: Annotated[str, pb_anno.Field(9)] = ''
    timestamp: Annotated[int, pb_anno.Field(10)] = 0
    rnd: Annotated[str, pb_anno.Field(12)] = ''
    action: Annotated[str, pb_anno.Field(18)] = ''
    effect: Annotated[SendGiftV2GiftEffect, pb_anno.Field(35)] = dataclasses.field(
        default_factory=SendGiftV2GiftEffect
    )


@dataclasses.dataclass
class SendGiftV2(pb_msg.BaseMessage):
    uid: Annotated[int, pb_anno.Field(1)] = 0
    uname: Annotated[str, pb_anno.Field(2)] = ''
    face: Annotated[str, pb_anno.Field(3)] = ''
    medal: Annotated[SendGiftV2MedalInfo, pb_anno.Field(8)] = dataclasses.field(default_factory=SendGiftV2MedalInfo)
    blind: Annotated[SendGiftV2BlindGift, pb_anno.Field(9)] = dataclasses.field(default_factory=SendGiftV2BlindGift)
    gift: Annotated[SendGiftV2GiftData, pb_anno.Field(10)] = dataclasses.field(default_factory=SendGiftV2GiftData)
