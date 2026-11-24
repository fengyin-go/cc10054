"""投诉聚类领域服务：管理投诉簇的归并流程、状态流转与跨模块数据链路。

数据链路位置：投诉聚类是商品评论采集与口碑洞察平台的核心处理模块之一，负责把投诉簇的
归并结果写入口碑报告，并消费作者画像的产出记录，形成完整的跨模块数据流。
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


class ComplaintClusterService(BaseModuleService):
    MODULE = "complaint_cluster"
    ENTITY = "投诉簇"
    OPERATION_TERM = "归并"
    LIST_FIELDS = ["簇编号", "簇主题", "簇内条数", "代表评论", "严重等级"]
    REQUIRED_FIELDS = ["簇编号", "簇主题", "簇内条数"]
    STATUS_ORDER = ["新建", "已归并", "已升级"]
    ACTION_RULES = {"归并簇": "已归并", "升级簇": "已升级"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：投诉聚类跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把投诉聚类的归并结果写入口碑报告，形成投诉聚类→口碑报告的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"投诉簇 {entry_id} 不存在"}
        rows = store.rows("opinion_report")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "报告编号": f"投诉聚类-{entry_id}",
            "覆盖周期": "complaint_cluster",
            "正面要点": str(entry_id),
            "status": "草稿",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已升级"
        entry["pending"] = False
        return {"ok": True, "message": "归并结果已写入口碑报告", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取作者画像的产出记录并汇总为投诉聚类消费台账。"""
        up_rows = [r for r in store.rows("author_profile") if r.get("status") == "已冻结"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "簇编号": f"消费-{r.get('id', 0)}",
                "簇主题": str(r.get("作者指纹", "")),
                "簇内条数": "作者画像",
                "status": "新建",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条作者画像记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理投诉聚类归并中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"投诉簇 {entry_id} 不存在"}
        if entry.get("status") != "新建":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已归并"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出投诉聚类数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"投诉簇数据集",
            "operation": "归并",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
