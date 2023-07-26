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


@dataclasses.dataclass
class SimpleUser(pb_msg.BaseMessage):
    face: Annotated[str, pb_anno.Field(4)] = ''


@dataclasses.dataclass
class SimpleDm(pb_msg.BaseMessage):
    user: Annotated[SimpleUser, pb_anno.Field(20)] = dataclasses.field(default_factory=SimpleUser)


#
# 以下代码是预防以后全量使用Protobuf协议
#

class BizScene(enum.IntEnum):
    None_ = 0
    Lottery = 1
    Survive = 2
    VoiceConn = 3
    PlayBack = 4
    Vote = 5


@dataclasses.dataclass
class Bubble(pb_msg.BaseMessage):
    id: Annotated[int, pb_anno.Field(1)] = 0
    color: Annotated[str, pb_anno.Field(2)] = ''
    id_v2: Annotated[int, pb_anno.Field(3)] = 0


class DmType(enum.IntEnum):
    Normal = 0
    Emoticon = 1
    Voice = 2


@dataclasses.dataclass
class Emoticon(pb_msg.BaseMessage):
    unique: Annotated[str, pb_anno.Field(1)] = ''
    url: Annotated[str, pb_anno.Field(2)] = ''
    is_dynamic: Annotated[bool, pb_anno.Field(3)] = False
    in_player_area: Annotated[int, pb_anno.Field(4)] = 0
    bulge_display: Annotated[int, pb_anno.Field(5)] = 0
    height: Annotated[int, pb_anno.Field(6)] = 0
    width: Annotated[int, pb_anno.Field(7)] = 0


# pure_protobuf不支持map的临时解决方案
@dataclasses.dataclass
class EmoticonMapEntry(pb_msg.BaseMessage):
    key: Annotated[str, pb_anno.Field(1)] = ''
    value: Annotated[Emoticon, pb_anno.Field(2)] = dataclasses.field(default_factory=Emoticon)


@dataclasses.dataclass
class Voice(pb_msg.BaseMessage):
    url: Annotated[str, pb_anno.Field(1)] = ''
    file_format: Annotated[str, pb_anno.Field(2)] = ''
    text: Annotated[str, pb_anno.Field(3)] = ''
    file_duration: Annotated[int, pb_anno.Field(4)] = 0
    file_id: Annotated[str, pb_anno.Field(5)] = ''


@dataclasses.dataclass
class Aggregation(pb_msg.BaseMessage):
    is_aggregation: Annotated[bool, pb_anno.Field(1)] = False
    activity_source: Annotated[int, pb_anno.Field(2)] = 0
    activity_identity: Annotated[str, pb_anno.Field(3)] = ''
    not_show: Annotated[int, pb_anno.Field(4)] = 0


@dataclasses.dataclass
class Check(pb_msg.BaseMessage):
    token: Annotated[str, pb_anno.Field(1)] = ''
    ts: Annotated[int, pb_anno.Field(2)] = 0


@dataclasses.dataclass
class Medal(pb_msg.BaseMessage):
    level: Annotated[int, pb_anno.Field(1)] = 0
    name: Annotated[str, pb_anno.Field(2)] = ''
    special: Annotated[str, pb_anno.Field(3)] = ''
    color: Annotated[int, pb_anno.Field(4)] = 0
    icon_id: Annotated[int, pb_anno.Field(5)] = 0
    border_color: Annotated[int, pb_anno.Field(6)] = 0
    gradient_start_color: Annotated[int, pb_anno.Field(7)] = 0
    gradient_end_color: Annotated[int, pb_anno.Field(8)] = 0
    privilege: Annotated[int, pb_anno.Field(9)] = 0
    light: Annotated[int, pb_anno.Field(10)] = 0


@dataclasses.dataclass
class UserLevel(pb_msg.BaseMessage):
    level: Annotated[int, pb_anno.Field(1)] = 0
    color: Annotated[int, pb_anno.Field(2)] = 0
    rank: Annotated[str, pb_anno.Field(3)] = ''
    online_rank: Annotated[int, pb_anno.Field(4)] = 0


@dataclasses.dataclass
class Title(pb_msg.BaseMessage):
    title: Annotated[str, pb_anno.Field(1)] = ''
    old_title: Annotated[str, pb_anno.Field(2)] = ''


@dataclasses.dataclass
class Identify(pb_msg.BaseMessage):
    beginning_url: Annotated[str, pb_anno.Field(1)] = ''
    ending_url: Annotated[str, pb_anno.Field(2)] = ''
    jump_to_url: Annotated[str, pb_anno.Field(3)] = ''


@dataclasses.dataclass
class Wealth(pb_msg.BaseMessage):
    level: Annotated[int, pb_anno.Field(1)] = 0


@dataclasses.dataclass
class User(pb_msg.BaseMessage):
    uid: Annotated[int, pb_anno.Field(1)] = 0
    name: Annotated[str, pb_anno.Field(2)] = ''
    name_color: Annotated[str, pb_anno.Field(3)] = ''
    face: Annotated[str, pb_anno.Field(4)] = ''
    vip: Annotated[int, pb_anno.Field(5)] = 0
    svip: Annotated[int, pb_anno.Field(6)] = 0
    rank: Annotated[int, pb_anno.Field(7)] = 0
    mobile_verify: Annotated[int, pb_anno.Field(8)] = 0
    lpl_status: Annotated[int, pb_anno.Field(9)] = 0
    attr: Annotated[int, pb_anno.Field(10)] = 0
    medal: Annotated[Medal, pb_anno.Field(11)] = dataclasses.field(default_factory=Medal)
    level: Annotated[UserLevel, pb_anno.Field(12)] = dataclasses.field(default_factory=UserLevel)
    title: Annotated[Title, pb_anno.Field(13)] = dataclasses.field(default_factory=Title)
    identify: Annotated[Identify, pb_anno.Field(14)] = dataclasses.field(default_factory=Identify)
    wealth: Annotated[Wealth, pb_anno.Field(15)] = dataclasses.field(default_factory=Wealth)


@dataclasses.dataclass
class Room(pb_msg.BaseMessage):
    uid: Annotated[int, pb_anno.Field(1)] = 0
    name: Annotated[str, pb_anno.Field(2)] = ''


@dataclasses.dataclass
class Prefix(pb_msg.BaseMessage):
    type: Annotated[int, pb_anno.Field(1)] = 0
    resource: Annotated[str, pb_anno.Field(2)] = ''


@dataclasses.dataclass
class Icon(pb_msg.BaseMessage):
    prefix: Annotated[Prefix, pb_anno.Field(1)] = dataclasses.field(default_factory=Prefix)


@dataclasses.dataclass
class Dm(pb_msg.BaseMessage):
    id_str: Annotated[str, pb_anno.Field(1)] = ''
    mode: Annotated[int, pb_anno.Field(2)] = 0
    fontsize: Annotated[int, pb_anno.Field(3)] = 0
    color: Annotated[pb_anno.uint, pb_anno.Field(4)] = 0
    mid_hash: Annotated[str, pb_anno.Field(5)] = ''
    content: Annotated[str, pb_anno.Field(6)] = ''
    ctime: Annotated[int, pb_anno.Field(7)] = 0
    weight: Annotated[int, pb_anno.Field(8)] = 0
    rnd: Annotated[int, pb_anno.Field(9)] = 0
    attr: Annotated[int, pb_anno.Field(10)] = 0
    # 为了防止加新枚举后不兼容，还是用int了
    # biz_scene: Annotated[BizScene, pb_anno.Field(11)] = BizScene.None_
    biz_scene: Annotated[int, pb_anno.Field(11)] = 0
    bubble: Annotated[Bubble, pb_anno.Field(12)] = dataclasses.field(default_factory=Bubble)
    # dm_type: Annotated[DmType, pb_anno.Field(13)] = DmType.Normal
    dm_type: Annotated[int, pb_anno.Field(13)] = 0
    emoticons: Annotated[List[EmoticonMapEntry], pb_anno.Field(14)] = dataclasses.field(default_factory=list)
    voice: Annotated[Voice, pb_anno.Field(15)] = dataclasses.field(default_factory=Voice)
    animation: Annotated[str, pb_anno.Field(16)] = ''
    aggregation: Annotated[Aggregation, pb_anno.Field(17)] = dataclasses.field(default_factory=Aggregation)
    send_from_me: Annotated[bool, pb_anno.Field(18)] = False
    check: Annotated[Check, pb_anno.Field(19)] = dataclasses.field(default_factory=Check)
    user: Annotated[User, pb_anno.Field(20)] = dataclasses.field(default_factory=User)
    room: Annotated[Room, pb_anno.Field(21)] = dataclasses.field(default_factory=Room)
    icon: Annotated[Icon, pb_anno.Field(22)] = dataclasses.field(default_factory=Icon)
