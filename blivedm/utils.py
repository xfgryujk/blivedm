# -*- coding: utf-8 -*-
import random_user_agent.user_agent as ua
import random_user_agent.params as params

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
)

def randomlize_user_agent():
    """
    随机生成一个User-Agent字符串，并赋值给全局USER_AGENT变量。
    返回新的User-Agent。
    """

    software_names = [params.SoftwareName.CHROME.value]
    operating_systems = [params.OperatingSystem.WINDOWS.value]

    user_agent_rotator = ua.UserAgent(
        software_names=software_names,
        operating_systems=operating_systems
    )

    global USER_AGENT
    USER_AGENT = user_agent_rotator.get_random_user_agent()
    return USER_AGENT

def customize_user_agent(ua: str):
    """
    设置全局USER_AGENT变量为指定的ua字符串。
    返回新的User-Agent。
    """

    global USER_AGENT
    USER_AGENT = ua
    return USER_AGENT


def make_constant_retry_policy(interval: float):
    def get_interval(_retry_count: int, _total_retry_count: int):
        return interval
    return get_interval


def make_linear_retry_policy(start_interval: float, interval_step: float, max_interval: float):
    def get_interval(retry_count: int, _total_retry_count: int):
        return min(
            start_interval + (retry_count - 1) * interval_step,
            max_interval
        )
    return get_interval
