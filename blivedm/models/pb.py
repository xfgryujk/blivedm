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
