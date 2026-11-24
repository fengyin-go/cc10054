"""趋势统计领域服务：管理趋势点的计算流程、状态流转与跨模块数据链路。

数据链路位置：趋势统计是商品评论采集与口碑洞察平台的核心处理模块之一，负责把趋势点的
计算结果写入标注复核台，并消费口碑情感库的产出记录，形成完整的跨模块数据流。
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


class TrendStatService(BaseModuleService):
    MODULE = "trend_stat"
    ENTITY = "趋势点"
    OPERATION_TERM = "计算"
    LIST_FIELDS = ["统计编号", "统计周期", "情感占比", "环比变化", "口径版本"]
    REQUIRED_FIELDS = ["统计编号", "统计周期", "情感占比"]
    STATUS_ORDER = ["待计算", "已计算", "已重算"]
    ACTION_RULES = {"执行计算": "已计算", "触发重算": "已重算"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：趋势统计跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把趋势统计的计算结果写入标注复核台，形成趋势统计→标注复核台的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"趋势点 {entry_id} 不存在"}
        rows = store.rows("sentiment_review")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "事项编号": f"趋势统计-{entry_id}",
            "争议样本": "trend_stat",
            "原标注": str(entry_id),
            "status": "待复核",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已重算"
        entry["pending"] = False
        return {"ok": True, "message": "计算结果已写入标注复核台", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取口碑情感库的产出记录并汇总为趋势统计消费台账。"""
        up_rows = [r for r in store.rows("review_sentiment_store") if r.get("status") == "已剔除"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "统计编号": f"消费-{r.get('id', 0)}",
                "统计周期": str(r.get("样本编号", "")),
                "情感占比": "口碑情感库",
                "status": "待计算",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条口碑情感库记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理趋势统计计算中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"趋势点 {entry_id} 不存在"}
        if entry.get("status") != "待计算":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已计算"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出趋势统计数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"趋势点数据集",
            "operation": "计算",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
