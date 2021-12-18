# -*- coding: utf-8 -*-
import json
from typing import *

__all__ = (
    'HeartbeatMessage',
    'DanmakuMessage',
    'GiftMessage',
    'GuardBuyMessage',
    'SuperChatMessage',
    'SuperChatDeleteMessage',
)


class HeartbeatMessage:
    """
    心跳消息

    :param popularity: 人气值
    """

    def __init__(
        self,
        popularity: int = None,
    ):
        self.popularity: int = popularity

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            popularity=data['popularity'],
        )


class DanmakuMessage:
    """
    弹幕消息

    :param mode: 弹幕显示模式（滚动、顶部、底部）
    :param font_size: 字体尺寸
    :param color: 颜色
    :param timestamp: 时间戳（毫秒）
    :param rnd: 随机数，前端叫作弹幕ID，可能是去重用的
    :param uid_crc32: 用户ID文本的CRC32
    :param msg_type: 是否礼物弹幕（节奏风暴）
    :param bubble: 右侧评论栏气泡
    :param dm_type: 弹幕类型，0文本，1表情，2语音
    :param emoticon_options: 表情参数
    :param voice_config: 语音参数
    :param mode_info: 一些附加参数

    :param msg: 弹幕内容

    :param uid: 用户ID
    :param uname: 用户名
    :param admin: 是否房管
    :param vip: 是否月费老爷
    :param svip: 是否年费老爷
    :param urank: 用户身份，用来判断是否正式会员，猜测非正式会员为5000，正式会员为10000
    :param mobile_verify: 是否绑定手机
    :param uname_color: 用户名颜色

    :param medal_level: 勋章等级
    :param medal_name: 勋章名
    :param runame: 勋章房间主播名
    :param medal_room_id: 勋章房间ID
    :param mcolor: 勋章颜色
    :param special_medal: 特殊勋章

    :param user_level: 用户等级
    :param ulevel_color: 用户等级颜色
    :param ulevel_rank: 用户等级排名，>50000时为'>50000'

    :param old_title: 旧头衔
    :param title: 头衔

    :param privilege_type: 舰队类型，0非舰队，1总督，2提督，3舰长
    """

    def __init__(
        self,
        mode: int = None,
        font_size: int = None,
        color: int = None,
        timestamp: int = None,
        rnd: int = None,
        uid_crc32: str = None,
        msg_type: int = None,
        bubble: int = None,
        dm_type: int = None,
        emoticon_options: Union[dict, str] = None,
        voice_config: Union[dict, str] = None,
        mode_info: dict = None,

        msg: str = None,

        uid: int = None,
        uname: str = None,
        admin: int = None,
        vip: int = None,
        svip: int = None,
        urank: int = None,
        mobile_verify: int = None,
        uname_color: str = None,

        medal_level: str = None,
        medal_name: str = None,
        runame: str = None,
        medal_room_id: int = None,
        mcolor: int = None,
        special_medal: str = None,

        user_level: int = None,
        ulevel_color: int = None,
        ulevel_rank: str = None,

        old_title: str = None,
        title: str = None,

        privilege_type: int = None,
    ):
        self.mode: int = mode
        self.font_size: int = font_size
        self.color: int = color
        self.timestamp: int = timestamp
        self.rnd: int = rnd
        self.uid_crc32: str = uid_crc32
        self.msg_type: int = msg_type
        self.bubble: int = bubble
        self.dm_type: int = dm_type
        self.emoticon_options: Union[dict, str] = emoticon_options
        self.voice_config: Union[dict, str] = voice_config
        self.mode_info: dict = mode_info

        self.msg: str = msg

        self.uid: int = uid
        self.uname: str = uname
        self.admin: int = admin
        self.vip: int = vip
        self.svip: int = svip
        self.urank: int = urank
        self.mobile_verify: int = mobile_verify
        self.uname_color: str = uname_color

        self.medal_level: str = medal_level
        self.medal_name: str = medal_name
        self.runame: str = runame
        self.medal_room_id: int = medal_room_id
        self.mcolor: int = mcolor
        self.special_medal: str = special_medal

        self.user_level: int = user_level
        self.ulevel_color: int = ulevel_color
        self.ulevel_rank: str = ulevel_rank

        self.old_title: str = old_title
        self.title: str = title

        self.privilege_type: int = privilege_type

    @classmethod
    def from_command(cls, info: dict):
        if len(info[3]) != 0:
            medal_level = info[3][0]
            medal_name = info[3][1]
            runame = info[3][2]
            room_id = info[3][3]
            mcolor = info[3][4]
            special_medal = info[3][5]
        else:
            medal_level = 0
            medal_name = ''
            runame = ''
            room_id = 0
            mcolor = 0
            special_medal = 0

        return cls(
            mode=info[0][1],
            font_size=info[0][2],
            color=info[0][3],
            timestamp=info[0][4],
            rnd=info[0][5],
            uid_crc32=info[0][7],
            msg_type=info[0][9],
            bubble=info[0][10],
            dm_type=info[0][12],
            emoticon_options=info[0][13],
            voice_config=info[0][14],
            mode_info=info[0][15],

            msg=info[1],

            uid=info[2][0],
            uname=info[2][1],
            admin=info[2][2],
            vip=info[2][3],
            svip=info[2][4],
            urank=info[2][5],
            mobile_verify=info[2][6],
            uname_color=info[2][7],

            medal_level=medal_level,
            medal_name=medal_name,
            runame=runame,
            medal_room_id=room_id,
            mcolor=mcolor,
            special_medal=special_medal,

            user_level=info[4][0],
            ulevel_color=info[4][2],
            ulevel_rank=info[4][3],

            old_title=info[5][0],
            title=info[5][1],

            privilege_type=info[7],
        )

    @property
    def emoticon_options_dict(self) -> dict:
        """
        示例：
        {'bulge_display': 0, 'emoticon_unique': 'official_13', 'height': 60, 'in_player_area': 1, 'is_dynamic': 1,
         'url': 'https://i0.hdslb.com/bfs/live/a98e35996545509188fe4d24bd1a56518ea5af48.png', 'width': 183}
        """
        if isinstance(self.emoticon_options, dict):
            return self.emoticon_options
        try:
            return json.loads(self.emoticon_options)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def voice_config_dict(self) -> dict:
        """
        示例：
        {'voice_url': 'https%3A%2F%2Fboss.hdslb.com%2Flive-dm-voice%2Fb5b26e48b556915cbf3312a59d3bb2561627725945.wav
         %3FX-Amz-Algorithm%3DAWS4-HMAC-SHA256%26X-Amz-Credential%3D2663ba902868f12f%252F20210731%252Fshjd%252Fs3%25
         2Faws4_request%26X-Amz-Date%3D20210731T100545Z%26X-Amz-Expires%3D600000%26X-Amz-SignedHeaders%3Dhost%26
         X-Amz-Signature%3D114e7cb5ac91c72e231c26d8ca211e53914722f36309b861a6409ffb20f07ab8',
         'file_format': 'wav', 'text': '汤，下午好。', 'file_duration': 1}
        """
        if isinstance(self.voice_config, dict):
            return self.voice_config
        try:
            return json.loads(self.voice_config)
        except (json.JSONDecodeError, TypeError):
            return {}


class GiftMessage:
    """
    礼物消息

    :param gift_name: 礼物名
    :param num: 数量
    :param uname: 用户名
    :param face: 用户头像URL
    :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
    :param uid: 用户ID
    :param timestamp: 时间戳
    :param gift_id: 礼物ID
    :param gift_type: 礼物类型（未知）
    :param action: 目前遇到的有'喂食'、'赠送'
    :param price: 礼物单价瓜子数
    :param rnd: 随机数，可能是去重用的。有时是时间戳+去重ID，有时是UUID
    :param coin_type: 瓜子类型，'silver'或'gold'，1000金瓜子 = 1元
    :param total_coin: 总瓜子数
    :param tid: 可能是事务ID，有时和rnd相同
    """

    def __init__(
        self,
        gift_name: str = None,
        num: int = None,
        uname: str = None,
        face: str = None,
        guard_level: int = None,
        uid: int = None,
        timestamp: int = None,
        gift_id: int = None,
        gift_type: int = None,
        action: str = None,
        price: int = None,
        rnd: str = None,
        coin_type: str = None,
        total_coin: int = None,
        tid: str = None,
    ):
        self.gift_name = gift_name
        self.num = num
        self.uname = uname
        self.face = face
        self.guard_level = guard_level
        self.uid = uid
        self.timestamp = timestamp
        self.gift_id = gift_id
        self.gift_type = gift_type
        self.action = action
        self.price = price
        self.rnd = rnd
        self.coin_type = coin_type
        self.total_coin = total_coin
        self.tid = tid

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            gift_name=data['giftName'],
            num=data['num'],
            uname=data['uname'],
            face=data['face'],
            guard_level=data['guard_level'],
            uid=data['uid'],
            timestamp=data['timestamp'],
            gift_id=data['giftId'],
            gift_type=data['giftType'],
            action=data['action'],
            price=data['price'],
            rnd=data['rnd'],
            coin_type=data['coin_type'],
            total_coin=data['total_coin'],
            tid=data['tid'],
        )


class GuardBuyMessage:
    """
    上舰消息

    :param uid: 用户ID
    :param username: 用户名
    :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
    :param num: 数量
    :param price: 单价金瓜子数
    :param gift_id: 礼物ID
    :param gift_name: 礼物名
    :param start_time: 开始时间戳，和结束时间戳相同
    :param end_time: 结束时间戳，和开始时间戳相同
    """

    def __init__(
        self,
        uid: int = None,
        username: str = None,
        guard_level: int = None,
        num: int = None,
        price: int = None,
        gift_id: int = None,
        gift_name: str = None,
        start_time: int = None,
        end_time: int = None,
    ):
        self.uid: int = uid
        self.username: str = username
        self.guard_level: int = guard_level
        self.num: int = num
        self.price: int = price
        self.gift_id: int = gift_id
        self.gift_name: str = gift_name
        self.start_time: int = start_time
        self.end_time: int = end_time

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            uid=data['uid'],
            username=data['username'],
            guard_level=data['guard_level'],
            num=data['num'],
            price=data['price'],
            gift_id=data['gift_id'],
            gift_name=data['gift_name'],
            start_time=data['start_time'],
            end_time=data['end_time'],
        )


class SuperChatMessage:
    """
    醒目留言消息

    :param price: 价格（人民币）
    :param message: 消息
    :param message_trans: 消息日文翻译（目前只出现在SUPER_CHAT_MESSAGE_JPN）
    :param start_time: 开始时间戳
    :param end_time: 结束时间戳
    :param time: 剩余时间（约等于 结束时间戳 - 开始时间戳）
    :param id_: str，醒目留言ID，删除时用
    :param gift_id: 礼物ID
    :param gift_name: 礼物名
    :param uid: 用户ID
    :param uname: 用户名
    :param face: 用户头像URL
    :param guard_level: 舰队等级，0非舰队，1总督，2提督，3舰长
    :param user_level: 用户等级
    :param background_bottom_color: 底部背景色，'#rrggbb'
    :param background_color: 背景色，'#rrggbb'
    :param background_icon: 背景图标
    :param background_image: 背景图URL
    :param background_price_color: 背景价格颜色，'#rrggbb'
    """

    def __init__(
        self,
        price: int = None,
        message: str = None,
        message_trans: str = None,
        start_time: int = None,
        end_time: int = None,
        time: int = None,
        id_: int = None,
        gift_id: int = None,
        gift_name: str = None,
        uid: int = None,
        uname: str = None,
        face: str = None,
        guard_level: int = None,
        user_level: int = None,
        background_bottom_color: str = None,
        background_color: str = None,
        background_icon: str = None,
        background_image: str = None,
        background_price_color: str = None,
    ):
        self.price: int = price
        self.message: str = message
        self.message_trans: str = message_trans
        self.start_time: int = start_time
        self.end_time: int = end_time
        self.time: int = time
        self.id: int = id_
        self.gift_id: int = gift_id
        self.gift_name: str = gift_name
        self.uid: int = uid
        self.uname: str = uname
        self.face: str = face
        self.guard_level: int = guard_level
        self.user_level: int = user_level
        self.background_bottom_color: str = background_bottom_color
        self.background_color: str = background_color
        self.background_icon: str = background_icon
        self.background_image: str = background_image
        self.background_price_color: str = background_price_color

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            price=data['price'],
            message=data['message'],
            message_trans=data['message_trans'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            time=data['time'],
            id_=data['id'],
            gift_id=data['gift']['gift_id'],
            gift_name=data['gift']['gift_name'],
            uid=data['uid'],
            uname=data['user_info']['uname'],
            face=data['user_info']['face'],
            guard_level=data['user_info']['guard_level'],
            user_level=data['user_info']['user_level'],
            background_bottom_color=data['background_bottom_color'],
            background_color=data['background_color'],
            background_icon=data['background_icon'],
            background_image=data['background_image'],
            background_price_color=data['background_price_color'],
        )


class SuperChatDeleteMessage:
    """
    删除醒目留言消息

    :param ids: 醒目留言ID数组
    """

    def __init__(
        self,
        ids: List[int] = None,
    ):
        self.ids: List[int] = ids

    @classmethod
    def from_command(cls, data: dict):
        return cls(
            ids=data['ids'],
        )
