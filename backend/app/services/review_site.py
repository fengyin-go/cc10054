"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReviewSiteService(BaseModuleService):
    MODULE = "review_site"
    ENTITY = "站点配置"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["站点名称", "站点类型", "覆盖类目", "评论语言", "抓取配额"]
    REQUIRED_FIELDS = ["站点名称", "站点类型", "覆盖类目"]
    STATUS_ORDER = ["待接入", "已接入", "已停用"]
    ACTION_RULES = {"接入站点": "已接入", "停用站点": "已停用"}
    NEGATIVE_ACTIONS = ["停用站点"]
