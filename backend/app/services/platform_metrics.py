"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PlatformMetricsService(BaseModuleService):
    MODULE = "platform_metrics"
    ENTITY = "度量项"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["度量名称", "统计窗口", "当前值", "环比值", "告警阈值"]
    REQUIRED_FIELDS = ["度量名称", "统计窗口", "当前值"]
    STATUS_ORDER = ["正常", "关注", "告警"]
    ACTION_RULES = {"刷新度量": "正常", "确认告警": "关注"}
    NEGATIVE_ACTIONS = []
