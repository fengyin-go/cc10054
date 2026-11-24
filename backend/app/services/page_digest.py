"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PageDigestService(BaseModuleService):
    MODULE = "page_digest"
    ENTITY = "页面摘录"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["摘录编号", "任务编号", "页面指纹", "正文摘要", "结构标记"]
    REQUIRED_FIELDS = ["摘录编号", "任务编号", "页面指纹"]
    STATUS_ORDER = ["已摘取", "已解析", "已丢弃"]
    ACTION_RULES = {"解析摘录": "已解析", "丢弃摘录": "已丢弃"}
    NEGATIVE_ACTIONS = []
