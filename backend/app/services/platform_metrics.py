"""采集度量总览领域服务：管理度量项的采集流程、状态流转与跨模块数据链路。

数据链路位置：采集度量总览是商品评论采集与口碑洞察平台的核心处理模块之一，负责把度量项的
采集结果写入评分归一，并消费口碑导出中心的产出记录，形成完整的跨模块数据流。
"""
from __future__ import annotations


from datetime import datetime, timezone
from typing import Any

from app.services.base import BaseModuleService
from app.store import store


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id(rows: list) -> int:
    return max((int(r.get("id", 0)) for r in rows), default=0) + 1


class PlatformMetricsService(BaseModuleService):
    MODULE = "platform_metrics"
    ENTITY = "度量项"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["度量名称", "统计窗口", "当前值", "环比值", "告警阈值"]
    REQUIRED_FIELDS = ["度量名称", "统计窗口", "当前值"]
    STATUS_ORDER = ["正常", "关注", "告警"]
    ACTION_RULES = {"刷新度量": "正常", "确认告警": "关注"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：采集度量总览跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把采集度量总览的采集结果写入评分归一，形成采集度量总览→评分归一的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"度量项 {entry_id} 不存在"}
        rows = store.rows("rating_norm")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "记录编号": f"采集度量总览-{entry_id}",
            "原始评分": "platform_metrics",
            "评分制式": str(entry_id),
            "status": "待归一",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "告警"
        entry["pending"] = False
        return {"ok": True, "message": "采集结果已写入评分归一", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取口碑导出中心的产出记录并汇总为采集度量总览消费台账。"""
        up_rows = [r for r in store.rows("review_export") if r.get("status") == "已完成"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "度量名称": f"消费-{r.get('id', 0)}",
                "统计窗口": str(r.get("导出编号", "")),
                "当前值": "口碑导出中心",
                "status": "正常",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条口碑导出中心记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理采集度量总览采集中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"度量项 {entry_id} 不存在"}
        if entry.get("status") != "正常":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "关注"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出采集度量总览数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"度量项数据集",
            "operation": "采集",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
