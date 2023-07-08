# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing_extensions import Annotated

from pure_protobuf.annotations import Field
from pure_protobuf.message import BaseMessage

__all__ = (
    'DanmakuMessageV2',
)


@dataclass
class UserInfo(BaseMessage):
    face: Annotated[str, Field(4)] = None


@dataclass
class DanmakuMessageV2(BaseMessage):
    user: Annotated[UserInfo, Field(20)] = field(default_factory=UserInfo)
