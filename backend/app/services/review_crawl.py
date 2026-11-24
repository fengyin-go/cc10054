"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ReviewCrawlService(BaseModuleService):
    MODULE = "review_crawl"
    ENTITY = "抓取任务"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["任务编号", "站点标识", "关键词标识", "抓取深度", "会话票据"]
    REQUIRED_FIELDS = ["任务编号", "站点标识", "关键词标识"]
    STATUS_ORDER = ["待执行", "执行中", "已完成", "失败待重试"]
    ACTION_RULES = {"启动任务": "执行中", "标记完成": "已完成", "重试任务": "执行中"}
    NEGATIVE_ACTIONS = []
