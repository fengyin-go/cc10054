"""方面词抽取领域服务：管理方面词的关联流程、状态流转与跨模块数据链路。

数据链路位置：方面词抽取是商品评论采集与口碑洞察平台的核心处理模块之一，负责把方面词的
关联结果写入口碑导出中心，并消费评论去重的产出记录，形成完整的跨模块数据流。
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


class AspectExtractService(BaseModuleService):
    MODULE = "aspect_extract"
    ENTITY = "方面词"
    OPERATION_TERM = "关联"
    LIST_FIELDS = ["方面词名称", "关联类目", "出现频次", "情感倾向", "生效标记"]
    REQUIRED_FIELDS = ["方面词名称", "关联类目", "出现频次"]
    STATUS_ORDER = ["候选", "已生效", "已淘汰"]
    ACTION_RULES = {"生效方面词": "已生效", "淘汰方面词": "已淘汰"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：方面词抽取跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把方面词抽取的关联结果写入口碑导出中心，形成方面词抽取→口碑导出中心的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"方面词 {entry_id} 不存在"}
        rows = store.rows("review_export")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "导出编号": f"方面词抽取-{entry_id}",
            "数据范围": "aspect_extract",
            "字段清单": str(entry_id),
            "status": "排队中",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已淘汰"
        entry["pending"] = False
        return {"ok": True, "message": "关联结果已写入口碑导出中心", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取评论去重的产出记录并汇总为方面词抽取消费台账。"""
        up_rows = [r for r in store.rows("review_dedup") if r.get("status") == "已合并"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "方面词名称": f"消费-{r.get('id', 0)}",
                "关联类目": str(r.get("记录编号", "")),
                "出现频次": "评论去重",
                "status": "候选",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条评论去重记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理方面词抽取关联中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"方面词 {entry_id} 不存在"}
        if entry.get("status") != "候选":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已生效"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出方面词抽取数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"方面词数据集",
            "operation": "关联",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
