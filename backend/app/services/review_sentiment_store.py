"""口碑情感库领域服务：管理情感样本的查询流程、状态流转与跨模块数据链路。

数据链路位置：口碑情感库是商品评论采集与口碑洞察平台的核心处理模块之一，负责把情感样本的
查询结果写入失败重试队列，并消费情感标注的产出记录，形成完整的跨模块数据流。
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


class ReviewSentimentStoreService(BaseModuleService):
    MODULE = "review_sentiment_store"
    ENTITY = "情感样本"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["样本编号", "情感极性", "强度分值", "类目归属", "入档时间"]
    REQUIRED_FIELDS = ["样本编号", "情感极性", "强度分值"]
    STATUS_ORDER = ["暂存", "已入档", "已剔除"]
    ACTION_RULES = {"入档样本": "已入档", "剔除样本": "已剔除"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：口碑情感库跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把口碑情感库的查询结果写入失败重试队列，形成口碑情感库→失败重试队列的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"情感样本 {entry_id} 不存在"}
        rows = store.rows("crawl_retry")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "队列编号": f"口碑情感库-{entry_id}",
            "失败原因": "review_sentiment_store",
            "重试次数": str(entry_id),
            "status": "排队中",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已剔除"
        entry["pending"] = False
        return {"ok": True, "message": "查询结果已写入失败重试队列", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取情感标注的产出记录并汇总为口碑情感库消费台账。"""
        up_rows = [r for r in store.rows("sentiment_label") if r.get("status") == "复核中"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "样本编号": f"消费-{r.get('id', 0)}",
                "情感极性": str(r.get("记录编号", "")),
                "强度分值": "情感标注",
                "status": "暂存",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条情感标注记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理口碑情感库查询中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"情感样本 {entry_id} 不存在"}
        if entry.get("status") != "暂存":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已入档"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出口碑情感库数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"情感样本数据集",
            "operation": "查询",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
