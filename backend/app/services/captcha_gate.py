"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CaptchaGateService(BaseModuleService):
    MODULE = "captcha_gate"
    ENTITY = "闸口记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["闸口编号", "站点标识", "触发频率", "处置策略", "冷却时长"]
    REQUIRED_FIELDS = ["闸口编号", "站点标识", "触发频率"]
    STATUS_ORDER = ["监控中", "已触发", "已冷却"]
    ACTION_RULES = {"触发闸口": "已触发", "解除冷却": "已冷却"}
    NEGATIVE_ACTIONS = []
