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


@dataclasses.dataclass
class SendGiftV2MedalInfo(pb_msg.BaseMessage):
    target_id: Annotated[int, pb_anno.Field(1)] = 0
    anchor_roomid: Annotated[int, pb_anno.Field(4)] = 0
    medal_level: Annotated[int, pb_anno.Field(5)] = 0
    medal_name: Annotated[str, pb_anno.Field(6)] = ''


@dataclasses.dataclass
class SendGiftV2BlindGift(pb_msg.BaseMessage):
    original_gift_name: Annotated[str, pb_anno.Field(3)] = ''
    original_gift_price: Annotated[int, pb_anno.Field(6)] = 0


@dataclasses.dataclass
class SendGiftV2GiftMaterialSnapShot(pb_msg.BaseMessage):
    img_basic: Annotated[str, pb_anno.Field(1)] = ''


@dataclasses.dataclass
class SendGiftV2GiftItem(pb_msg.BaseMessage):
    gift_id: Annotated[int, pb_anno.Field(1)] = 0
    gift_name: Annotated[str, pb_anno.Field(2)] = ''
    num: Annotated[int, pb_anno.Field(3)] = 0
    gift_type: Annotated[int, pb_anno.Field(4)] = 0
    price: Annotated[int, pb_anno.Field(5)] = 0
    total_coin: Annotated[int, pb_anno.Field(7)] = 0
    coin_type: Annotated[str, pb_anno.Field(8)] = ''
    tid: Annotated[str, pb_anno.Field(9)] = ''
    timestamp: Annotated[int, pb_anno.Field(10)] = 0
    rnd: Annotated[str, pb_anno.Field(12)] = ''
    action: Annotated[str, pb_anno.Field(18)] = ''
    gift_info: Annotated[SendGiftV2GiftMaterialSnapShot, pb_anno.Field(35)] = dataclasses.field(
        default_factory=SendGiftV2GiftMaterialSnapShot
    )


@dataclasses.dataclass
class SendGiftBroadcast(pb_msg.BaseMessage):
    uid: Annotated[int, pb_anno.Field(1)] = 0
    uname: Annotated[str, pb_anno.Field(2)] = ''
    face: Annotated[str, pb_anno.Field(3)] = ''
    guard_level: Annotated[int, pb_anno.Field(5)] = 0
    medal_info: Annotated[SendGiftV2MedalInfo, pb_anno.Field(8)] = dataclasses.field(default_factory=SendGiftV2MedalInfo)
    blind_gift: Annotated[SendGiftV2BlindGift, pb_anno.Field(9)] = dataclasses.field(default_factory=SendGiftV2BlindGift)
    gift_list: Annotated[List[SendGiftV2GiftItem], pb_anno.Field(10)] = dataclasses.field(default_factory=list)
