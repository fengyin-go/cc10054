"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class OpinionReportService(BaseModuleService):
    MODULE = "opinion_report"
    ENTITY = "报告文档"
    OPERATION_TERM = "聚合"
    LIST_FIELDS = ["报告编号", "覆盖周期", "正面要点", "负面要点", "发布版本"]
    REQUIRED_FIELDS = ["报告编号", "覆盖周期", "正面要点"]
    STATUS_ORDER = ["草稿", "已发布", "已归档"]
    ACTION_RULES = {"发布报告": "已发布", "归档报告": "已归档"}
    NEGATIVE_ACTIONS = []
