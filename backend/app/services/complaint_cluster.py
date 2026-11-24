"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ComplaintClusterService(BaseModuleService):
    MODULE = "complaint_cluster"
    ENTITY = "投诉簇"
    OPERATION_TERM = "归并"
    LIST_FIELDS = ["簇编号", "簇主题", "簇内条数", "代表评论", "严重等级"]
    REQUIRED_FIELDS = ["簇编号", "簇主题", "簇内条数"]
    STATUS_ORDER = ["新建", "已归并", "已升级"]
    ACTION_RULES = {"归并簇": "已归并", "升级簇": "已升级"}
    NEGATIVE_ACTIONS = []
