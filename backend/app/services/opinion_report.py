"""口碑报告领域服务：管理报告文档的聚合流程、状态流转与跨模块数据链路。

数据链路位置：口碑报告是商品评论采集与口碑洞察平台的核心处理模块之一，负责把报告文档的
聚合结果写入页面快文摘取，并消费验证码闸口的产出记录，形成完整的跨模块数据流。
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


class OpinionReportService(BaseModuleService):
    MODULE = "opinion_report"
    ENTITY = "报告文档"
    OPERATION_TERM = "聚合"
    LIST_FIELDS = ["报告编号", "覆盖周期", "正面要点", "负面要点", "发布版本"]
    REQUIRED_FIELDS = ["报告编号", "覆盖周期", "正面要点"]
    STATUS_ORDER = ["草稿", "已发布", "已归档"]
    ACTION_RULES = {"发布报告": "已发布", "归档报告": "已归档"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：口碑报告跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把口碑报告的聚合结果写入页面快文摘取，形成口碑报告→页面快文摘取的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"报告文档 {entry_id} 不存在"}
        rows = store.rows("page_digest")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "摘录编号": f"口碑报告-{entry_id}",
            "任务编号": "opinion_report",
            "页面指纹": str(entry_id),
            "status": "已摘取",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已归档"
        entry["pending"] = False
        return {"ok": True, "message": "聚合结果已写入页面快文摘取", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取验证码闸口的产出记录并汇总为口碑报告消费台账。"""
        up_rows = [r for r in store.rows("captcha_gate") if r.get("status") == "已冷却"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "报告编号": f"消费-{r.get('id', 0)}",
                "覆盖周期": str(r.get("闸口编号", "")),
                "正面要点": "验证码闸口",
                "status": "草稿",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条验证码闸口记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理口碑报告聚合中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"报告文档 {entry_id} 不存在"}
        if entry.get("status") != "草稿":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已发布"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出口碑报告数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"报告文档数据集",
            "operation": "聚合",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
