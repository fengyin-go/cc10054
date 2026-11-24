"""口碑导出中心领域服务：管理导出任务的导出流程、状态流转与跨模块数据链路。

数据链路位置：口碑导出中心是商品评论采集与口碑洞察平台的核心处理模块之一，负责把导出任务的
导出结果写入评论抓取任务，并消费抓取配额的产出记录，形成完整的跨模块数据流。
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


class ReviewExportService(BaseModuleService):
    MODULE = "review_export"
    ENTITY = "导出任务"
    OPERATION_TERM = "导出"
    LIST_FIELDS = ["导出编号", "数据范围", "字段清单", "文件指纹", "导出状态"]
    REQUIRED_FIELDS = ["导出编号", "数据范围", "字段清单"]
    STATUS_ORDER = ["排队中", "导出中", "已完成"]
    ACTION_RULES = {"开始导出": "导出中", "标记完成": "已完成"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：口碑导出中心跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把口碑导出中心的导出结果写入评论抓取任务，形成口碑导出中心→评论抓取任务的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"导出任务 {entry_id} 不存在"}
        rows = store.rows("review_crawl")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "任务编号": f"口碑导出中心-{entry_id}",
            "站点标识": "review_export",
            "关键词标识": str(entry_id),
            "status": "待执行",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已完成"
        entry["pending"] = False
        return {"ok": True, "message": "导出结果已写入评论抓取任务", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取抓取配额的产出记录并汇总为口碑导出中心消费台账。"""
        up_rows = [r for r in store.rows("crawl_quota") if r.get("status") == "已重置"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "导出编号": f"消费-{r.get('id', 0)}",
                "数据范围": str(r.get("配额编号", "")),
                "字段清单": "抓取配额",
                "status": "排队中",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条抓取配额记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理口碑导出中心导出中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"导出任务 {entry_id} 不存在"}
        if entry.get("status") != "排队中":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "导出中"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出口碑导出中心数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"导出任务数据集",
            "operation": "导出",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
