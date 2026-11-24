"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SentimentLabelService(BaseModuleService):
    MODULE = "sentiment_label"
    ENTITY = "情感记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["记录编号", "评论文本", "情感极性", "强度分值", "标注来源"]
    REQUIRED_FIELDS = ["记录编号", "评论文本", "情感极性"]
    STATUS_ORDER = ["待标注", "已标注", "复核中"]
    ACTION_RULES = {"自动标注": "已标注", "提交复核": "复核中"}
    NEGATIVE_ACTIONS = []
