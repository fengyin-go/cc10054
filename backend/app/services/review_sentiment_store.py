"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReviewSentimentStoreService(BaseModuleService):
    MODULE = "review_sentiment_store"
    ENTITY = "情感样本"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["样本编号", "情感极性", "强度分值", "类目归属", "入档时间"]
    REQUIRED_FIELDS = ["样本编号", "情感极性", "强度分值"]
    STATUS_ORDER = ["暂存", "已入档", "已剔除"]
    ACTION_RULES = {"入档样本": "已入档", "剔除样本": "已剔除"}
    NEGATIVE_ACTIONS = []
