"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class AuthorProfileService(BaseModuleService):
    MODULE = "author_profile"
    ENTITY = "作者档案"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["作者指纹", "站点集合", "活跃度等级", "可信等级", "最近活跃"]
    REQUIRED_FIELDS = ["作者指纹", "站点集合", "活跃度等级"]
    STATUS_ORDER = ["已建档", "已更新", "已冻结"]
    ACTION_RULES = {"更新画像": "已更新", "冻结画像": "已冻结"}
    NEGATIVE_ACTIONS = []
