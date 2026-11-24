"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TrendStatService(BaseModuleService):
    MODULE = "trend_stat"
    ENTITY = "趋势点"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["统计编号", "统计周期", "情感占比", "环比变化", "口径版本"]
    REQUIRED_FIELDS = ["统计编号", "统计周期", "情感占比"]
    STATUS_ORDER = ["待计算", "已计算", "已重算"]
    ACTION_RULES = {"执行计算": "已计算", "触发重算": "已重算"}
    NEGATIVE_ACTIONS = []
