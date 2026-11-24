"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class RatingNormService(BaseModuleService):
    MODULE = "rating_norm"
    ENTITY = "归一记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["记录编号", "原始评分", "评分制式", "归一评分", "置信标记"]
    REQUIRED_FIELDS = ["记录编号", "原始评分", "评分制式"]
    STATUS_ORDER = ["待归一", "已归一", "存疑"]
    ACTION_RULES = {"执行归一": "已归一", "标记存疑": "存疑"}
    NEGATIVE_ACTIONS = []
