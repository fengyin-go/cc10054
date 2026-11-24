"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReviewParseService(BaseModuleService):
    MODULE = "review_parse"
    ENTITY = "解析规则"
    OPERATION_TERM = "解析"
    LIST_FIELDS = ["规则名称", "站点标识", "字段映射", "嵌套层级", "容错策略"]
    REQUIRED_FIELDS = ["规则名称", "站点标识", "字段映射"]
    STATUS_ORDER = ["草稿", "已生效", "已停用"]
    ACTION_RULES = {"生效规则": "已生效", "停用规则": "已停用"}
    NEGATIVE_ACTIONS = ["停用规则"]
