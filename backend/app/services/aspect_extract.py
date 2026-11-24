"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class AspectExtractService(BaseModuleService):
    MODULE = "aspect_extract"
    ENTITY = "方面词"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["方面词名称", "关联类目", "出现频次", "情感倾向", "生效标记"]
    REQUIRED_FIELDS = ["方面词名称", "关联类目", "出现频次"]
    STATUS_ORDER = ["候选", "已生效", "已淘汰"]
    ACTION_RULES = {"生效方面词": "已生效", "淘汰方面词": "已淘汰"}
    NEGATIVE_ACTIONS = []
