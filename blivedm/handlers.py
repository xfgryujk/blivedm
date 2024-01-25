# -*- coding: utf-8 -*-
import logging
from typing import *

from .clients import ws_base
from .models import web as web_models, open_live as open_models

__all__ = (
    'HandlerInterface',
    'BaseHandler',
)

logger = logging.getLogger('blivedm')

logged_unknown_cmds = {
    'ANCHOR_HELPER_DANMU', # 直播小助手 command={'cmd': 'ANCHOR_HELPER_DANMU', 'data': {'sender': '直播小助手', 'msg': '开播获得100个弹幕！邀请观众连麦互动，直播间氛围更活跃哦', 'platform': 1, 'button_platform': 3, 'button_name': '去连麦', 'button_target': 'bililive://blink/open_voicelink', 'button_label': 0, 'report_type': 'milestone', 'report': 'session_danmu:6:100'}}
    'ANCHOR_BROADCAST', # 直播小助手 command={'cmd': 'ANCHOR_BROADCAST', 'data': {'sender': '直播小助手', 'msg': '开播获得100个弹幕！邀请观众连麦互动，直播间氛围更活跃哦', 'platform': 1, 'button_info': {'button_name': '去连麦', 'blink_button_type': '', 'blink_button_target': '', 'blink_button_extra': '', 'blink_button_label': 0, 'hime_button_type': 'panel', 'hime_button_target': '1000', 'hime_button_extra': '', 'hime_button_h5_type': '0', 'hime_button_label': 0}, 'milestone_type': 'session_danmu', 'milestone_value': 100, 'milestone_index': 6}}
    'COMBO_SEND',
    'COMBO_END', # command={'cmd': 'COMBO_END', 'data': {'uid': 3494366419093890, 'ruid': 412847209, 'uname': 'thuGreth', 'r_uname': '老狗自闭', 'combo_num': 1, 'gift_id': 31164, 'gift_num': 1, 'batch_combo_num': 1, 'gift_name': '粉丝团灯牌', 'action': '投喂', 'send_master': None, 'price': 1000, 'start_time': 1706173240, 'end_time': 1706173240, 'guard_level': 0, 'name_color': '', 'combo_total_coin': 1000, 'coin_type': 'gold', 'is_mystery': False}}
    # 'COMMON_NOTICE_DANMAKU', # 特殊通知弹幕 command={'cmd': 'COMMON_NOTICE_DANMAKU', 'data': {'terminals': [4, 5], 'content_segments': [{'type': 1, 'font_color': '#61666d', 'font_color_dark': '#a2a7ae', 'text': '恭喜 <%thuGreth%> 成为 <%小花花%> 星球守护者~', 'highlight_font_color': '#FFB027', 'highlight_font_color_dark': '#FFB027'}]}}
    'WATCHED_CHANGE', # 本次直播观众数量改变触发 command={'cmd': 'WATCHED_CHANGE', 'data': {'num': 14, 'text_small': '14', 'text_large': '14人看过'}}
    'ENTRY_EFFECT',
    'HOT_RANK_CHANGED',
    'HOT_RANK_CHANGED_V2',
    # 'INTERACT_WORD', # 进入直播间 command={'cmd': 'INTERACT_WORD', 'data': {'contribution': {'grade': 3}, 'contribution_v2': {'grade': 2, 'rank_type': 'monthly_rank', 'text': '月榜前3用户'}, 'core_user_type': 0, 'dmscore': 28, 'fans_medal': {'anchor_roomid': 0, 'guard_level': 0, 'icon_id': 0, 'is_lighted': 0, 'medal_color': 0, 'medal_color_border': 0, 'medal_color_end': 0, 'medal_color_start': 0, 'medal_level': 0, 'medal_name': '', 'score': 0, 'special': '', 'target_id': 0}, 'group_medal': None, 'identities': [1], 'is_mystery': False, 'is_spread': 0, 'msg_type': 1, 'privilege_type': 0, 'roomid': 30886597, 'score': 1706174295693, 'spread_desc': '', 'spread_info': '', 'tail_icon': 0, 'tail_text': '', 'timestamp': 1706174295, 'trigger_time': 1706174294633680000, 'uid': 90383004, 'uinfo': {'base': {'face': 'https://i0.hdslb.com/bfs/face/a3720664af7a993fc45ce48f190d02913d1f2c85.jpg', 'is_mystery': False, 'name': '月上小狗', 'name_color': 0, 'official_info': {'desc': '', 'role': 0, 'title': '', 'type': -1}, 'origin_info': {'face': 'https://i0.hdslb.com/bfs/face/a3720664af7a993fc45ce48f190d02913d1f2c85.jpg', 'name': '月上小狗'}, 'risk_ctrl_info': {'face': 'https://i0.hdslb.com/bfs/face/a3720664af7a993fc45ce48f190d02913d1f2c85.jpg', 'name': '月上小狗'}}, 'guard': None, 'guard_leader': None, 'medal': None, 'title': None, 'uhead_frame': None, 'uid': 90383004, 'wealth': None}, 'uname': '月上小狗', 'uname_color': ''}}
    'LIVE',
    'LIVE_INTERACTIVE_GAME',
    'NOTICE_MSG',
    'ONLINE_RANK_COUNT',
    'ONLINE_RANK_TOP3',
    'ONLINE_RANK_V2',
    'PK_BATTLE_END',
    'PK_BATTLE_FINAL_PROCESS',
    'PK_BATTLE_PROCESS',
    'PK_BATTLE_PROCESS_NEW',
    'PK_BATTLE_SETTLE',
    'PK_BATTLE_SETTLE_USER',
    'PK_BATTLE_SETTLE_V2',
    'PREPARING',
    'ROOM_REAL_TIME_MESSAGE_UPDATE',
    'STOP_LIVE_ROOM_LIST',
    'SUPER_CHAT_MESSAGE_JPN',
    'WIDGET_BANNER',
    'TRADING_SCORE', # command={'cmd': 'TRADING_SCORE', 'data': {'bubble_show_time': 3, 'num': 2, 'score_id': 3, 'uid': 412847209, 'update_time': 1706173741, 'update_type': 1}}
    'SPREAD_ORDER_START', # command={'cmd': 'SPREAD_ORDER_START', 'data': {'order_id': 5862464, 'order_status': 1, 'roomid': 30886597, 'timestamp': 1706173750, 'uid': 412847209}}
    'SPREAD_ORDER_OVER', # command={'cmd': 'SPREAD_ORDER_OVER', 'data': {'order_id': 5862464, 'order_status': 0, 'timestamp': 1706175599, 'uid': 412847209}}
    'SPREAD_SHOW_FEET', # 修改直播组件事件触发 command={'cmd': 'SPREAD_SHOW_FEET', 'data': {'click': 0, 'coin_cost': 0, 'coin_num': 5, 'order_id': 5862464, 'plan_percent': 0, 'show': 1, 'timestamp': 1706173762, 'title': '流量包推广', 'total_online': 0, 'uid': 412847209}}
    'SPREAD_SHOW_FEET_V2', # command={'cmd': 'SPREAD_SHOW_FEET_V2', 'data': {'click': 0, 'coin_cost': 0, 'coin_num': 5, 'cover_btn': '', 'cover_url': '', 'live_key': '459756646836947653', 'order_id': 5862464, 'order_type': 3, 'plan_percent': 0, 'show': 1, 'status': 1, 'timestamp': 1706173762, 'title': '流量包推广', 'total_online': 0, 'uid': 412847209}}
}
"""已打日志的未知cmd"""


class HandlerInterface:
    """
    直播消息处理器接口
    """

    def handle(self, client: ws_base.WebSocketClientBase, command: dict):
        raise NotImplementedError

    def on_client_stopped(self, client: ws_base.WebSocketClientBase, exception: Optional[Exception]):
        """
        当客户端停止时调用。可以在这里close或者重新start
        """


def _make_msg_callback(method_name, message_cls):
    def callback(self: 'BaseHandler', client: ws_base.WebSocketClientBase, command: dict):
        method = getattr(self, method_name)
        return method(client, message_cls.from_command(command['data']))
    return callback


class BaseHandler(HandlerInterface):
    """
    一个简单的消息处理器实现，带消息分发和消息类型转换。继承并重写_on_xxx方法即可实现自己的处理器
    """

    def __danmu_msg_callback(self, client: ws_base.WebSocketClientBase, command: dict):
        return self._on_danmaku(client, web_models.DanmakuMessage.from_command(command['info']))

    _CMD_CALLBACK_DICT: Dict[
        str,
        Optional[Callable[
            ['BaseHandler', ws_base.WebSocketClientBase, dict],
            Any
        ]]
    ] = {
        # 收到心跳包，这是blivedm自造的消息，原本的心跳包格式不一样
        '_HEARTBEAT': _make_msg_callback('_on_heartbeat', web_models.HeartbeatMessage),
        # 'ENTRY_EFFECT':
        # 收到弹幕
        # go-common\app\service\live\live-dm\service\v1\send.go
        'DANMU_MSG': __danmu_msg_callback,
        # 有人送礼
        'SEND_GIFT': _make_msg_callback('_on_gift', web_models.GiftMessage),
        # 特殊弹幕通知
        'COMMON_NOTICE_DANMAKU': _make_msg_callback('_on_spacial_danmaku', web_models.SpacialDanMaku),
        # 进入直播间
        'INTERACT_WORD': _make_msg_callback('_on_inter', web_models.UserInData),
        # 有人上舰
        'GUARD_BUY': _make_msg_callback('_on_buy_guard', web_models.GuardBuyMessage),
        # 醒目留言
        'SUPER_CHAT_MESSAGE': _make_msg_callback('_on_super_chat', web_models.SuperChatMessage),
        # 删除醒目留言
        'SUPER_CHAT_MESSAGE_DELETE': _make_msg_callback('_on_super_chat_delete', web_models.SuperChatDeleteMessage),
        # 点赞开始触发：command={'cmd': 'LIKE_INFO_V3_CLICK', 'data': {'show_area': 1, 'msg_type': 6, 'like_icon': 'https://i0.hdslb.com/bfs/live/23678e3d90402bea6a65251b3e728044c21b1f0f.png', 'uid': 90383004, 'like_text': '为主播点赞了', 'uname': '月上小狗', 'uname_color': '', 'identities': [1], 'fans_medal': {'target_id': 0, 'medal_level': 0, 'medal_name': '', 'medal_color': 0, 'medal_color_start': 12632256, 'medal_color_end': 12632256, 'medal_color_border': 12632256, 'is_lighted': 0, 'guard_level': 0, 'special': '', 'icon_id': 0, 'anchor_roomid': 0, 'score': 0}, 'contribution_info': {'grade': 0}, 'dmscore': 20, 'group_medal': None, 'is_mystery': False, 'uinfo': {'uid': 90383004, 'base': {'name': '月上小狗', 'face': 'https://i0.hdslb.com/bfs/face/a3720664af7a993fc45ce48f190d02913d1f2c85.jpg', 'name_color': 0, 'is_mystery': False, 'risk_ctrl_info': None, 'origin_info': {'name': '月上小狗', 'face': 'https://i0.hdslb.com/bfs/face/a3720664af7a993fc45ce48f190d02913d1f2c85.jpg'}, 'official_info': {'role': 0, 'title': '', 'desc': '', 'type': -1}}, 'medal': None, 'wealth': None, 'title': None, 'guard': {'level': 0, 'expired_str': ''}}}}
        'LIKE_INFO_V3_CLICK': _make_msg_callback('_click_like', web_models.ClickData),
        # 点赞结束触发：command = {'cmd': 'LIKE_INFO_V3_UPDATE', 'data': {'click_count': 171}}  应该是该点赞观众在本次直播中的汇总次数，不分时间
        'LIKE_INFO_V3_UPDATE': _make_msg_callback('_click_like', web_models.ClickData),

        #
        # 开放平台消息
        #

        # 收到弹幕
        'LIVE_OPEN_PLATFORM_DM': _make_msg_callback('_on_open_live_danmaku', open_models.DanmakuMessage),
        # 有人送礼
        'LIVE_OPEN_PLATFORM_SEND_GIFT': _make_msg_callback('_on_open_live_gift', open_models.GiftMessage),
        # 有人上舰
        'LIVE_OPEN_PLATFORM_GUARD': _make_msg_callback('_on_open_live_buy_guard', open_models.GuardBuyMessage),
        # 醒目留言
        'LIVE_OPEN_PLATFORM_SUPER_CHAT': _make_msg_callback('_on_open_live_super_chat', open_models.SuperChatMessage),
        # 删除醒目留言
        'LIVE_OPEN_PLATFORM_SUPER_CHAT_DEL': _make_msg_callback(
            '_on_open_live_super_chat_delete', open_models.SuperChatDeleteMessage
        ),
        # 点赞
        'LIVE_OPEN_PLATFORM_LIKE': _make_msg_callback('_on_open_live_like', open_models.LikeMessage),
    }
    """cmd -> 处理回调"""

    def handle(self, client: ws_base.WebSocketClientBase, command: dict):
        cmd = command.get('cmd', '')
        pos = cmd.find(':')  # 2019-5-29 B站弹幕升级新增了参数
        if pos != -1:
            cmd = cmd[:pos]

        if cmd not in self._CMD_CALLBACK_DICT:
            # 只有第一次遇到未知cmd时打日志
            if cmd not in logged_unknown_cmds:
                logger.warning('room=%d unknown cmd=%s, command=%s', client.room_id, cmd, command)
                logged_unknown_cmds.add(cmd)
            return

        callback = self._CMD_CALLBACK_DICT[cmd]
        if callback is not None:
            callback(self, client, command)

    def _on_heartbeat(self, client: ws_base.WebSocketClientBase, message: web_models.HeartbeatMessage):
        """
        收到心跳包
        """

    def _on_danmaku(self, client: ws_base.WebSocketClientBase, message: web_models.DanmakuMessage):
        """
        收到弹幕
        """

    def _on_gift(self, client: ws_base.WebSocketClientBase, message: web_models.GiftMessage):
        """
        收到礼物
        """

    def _on_buy_guard(self, client: ws_base.WebSocketClientBase, message: web_models.GuardBuyMessage):
        """
        有人上舰
        """

    def _on_super_chat(self, client: ws_base.WebSocketClientBase, message: web_models.SuperChatMessage):
        """
        醒目留言
        """

    def _on_super_chat_delete(
        self, client: ws_base.WebSocketClientBase, message: web_models.SuperChatDeleteMessage
    ):
        """
        删除醒目留言
        """

    #
    # 开放平台消息
    #

    def _on_open_live_danmaku(self, client: ws_base.WebSocketClientBase, message: open_models.DanmakuMessage):
        """
        收到弹幕
        """

    def _on_open_live_gift(self, client: ws_base.WebSocketClientBase, message: open_models.GiftMessage):
        """
        收到礼物
        """

    def _on_open_live_buy_guard(self, client: ws_base.WebSocketClientBase, message: open_models.GuardBuyMessage):
        """
        有人上舰
        """

    def _on_open_live_super_chat(
        self, client: ws_base.WebSocketClientBase, message: open_models.SuperChatMessage
    ):
        """
        醒目留言
        """

    def _on_open_live_super_chat_delete(
        self, client: ws_base.WebSocketClientBase, message: open_models.SuperChatDeleteMessage
    ):
        """
        删除醒目留言
        """

    def _on_open_live_like(self, client: ws_base.WebSocketClientBase, message: open_models.LikeMessage):
        """
        点赞
        """
