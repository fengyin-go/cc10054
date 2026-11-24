"""情感标注领域服务：管理情感记录的校验流程、状态流转与跨模块数据链路。

数据链路位置：情感标注是商品评论采集与口碑洞察平台的核心处理模块之一，负责把情感记录的
校验结果写入趋势统计，并消费页面快文摘取的产出记录，形成完整的跨模块数据流。
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


class SentimentLabelService(BaseModuleService):
    MODULE = "sentiment_label"
    ENTITY = "情感记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["记录编号", "评论文本", "情感极性", "强度分值", "标注来源"]
    REQUIRED_FIELDS = ["记录编号", "评论文本", "情感极性"]
    STATUS_ORDER = ["待标注", "已标注", "复核中"]
    ACTION_RULES = {"自动标注": "已标注", "提交复核": "复核中"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：情感标注跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把情感标注的校验结果写入趋势统计，形成情感标注→趋势统计的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"情感记录 {entry_id} 不存在"}
        rows = store.rows("trend_stat")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "统计编号": f"情感标注-{entry_id}",
            "统计周期": "sentiment_label",
            "情感占比": str(entry_id),
            "status": "待计算",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "复核中"
        entry["pending"] = False
        return {"ok": True, "message": "校验结果已写入趋势统计", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取页面快文摘取的产出记录并汇总为情感标注消费台账。"""
        up_rows = [r for r in store.rows("page_digest") if r.get("status") == "已丢弃"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "记录编号": f"消费-{r.get('id', 0)}",
                "评论文本": str(r.get("摘录编号", "")),
                "情感极性": "页面快文摘取",
                "status": "待标注",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条页面快文摘取记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理情感标注校验中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"情感记录 {entry_id} 不存在"}
        if entry.get("status") != "待标注":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已标注"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出情感标注数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"情感记录数据集",
            "operation": "校验",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
