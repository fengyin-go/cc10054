"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SeedKeywordService(BaseModuleService):
    MODULE = "seed_keyword"
    ENTITY = "关键词"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["关键词名称", "所属类目", "搜索意图", "优先级", "轮换周期"]
    REQUIRED_FIELDS = ["关键词名称", "所属类目", "搜索意图"]
    STATUS_ORDER = ["草稿", "生效中", "已轮换"]
    ACTION_RULES = {"启用关键词": "生效中", "轮换关键词": "已轮换"}
    NEGATIVE_ACTIONS = []
