"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class CrawlQuotaService(BaseModuleService):
    MODULE = "crawl_quota"
    ENTITY = "配额记录"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["配额编号", "站点标识", "日配额上限", "已用额度", "重置周期"]
    REQUIRED_FIELDS = ["配额编号", "站点标识", "日配额上限"]
    STATUS_ORDER = ["生效中", "已触顶", "已重置"]
    ACTION_RULES = {"上调配额": "生效中", "重置配额": "已重置"}
    NEGATIVE_ACTIONS = []
