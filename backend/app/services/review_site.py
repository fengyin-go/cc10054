"""评论站点目录领域服务：管理站点配置的接入流程、状态流转与跨模块数据链路。

数据链路位置：评论站点目录是商品评论采集与口碑洞察平台的核心处理模块之一，负责把站点配置的
接入结果写入情感标注，并消费口碑报告的产出记录，形成完整的跨模块数据流。
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


class ReviewSiteService(BaseModuleService):
    MODULE = "review_site"
    ENTITY = "站点配置"
    OPERATION_TERM = "接入"
    LIST_FIELDS = ["站点名称", "站点类型", "覆盖类目", "评论语言", "抓取配额"]
    REQUIRED_FIELDS = ["站点名称", "站点类型", "覆盖类目"]
    STATUS_ORDER = ["待接入", "已接入", "已停用"]
    ACTION_RULES = {"接入站点": "已接入", "停用站点": "已停用"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：评论站点目录跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把评论站点目录的接入结果写入情感标注，形成评论站点目录→情感标注的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"站点配置 {entry_id} 不存在"}
        rows = store.rows("sentiment_label")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "记录编号": f"评论站点目录-{entry_id}",
            "评论文本": "review_site",
            "情感极性": str(entry_id),
            "status": "待标注",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已停用"
        entry["pending"] = False
        return {"ok": True, "message": "接入结果已写入情感标注", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取口碑报告的产出记录并汇总为评论站点目录消费台账。"""
        up_rows = [r for r in store.rows("opinion_report") if r.get("status") == "已归档"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "站点名称": f"消费-{r.get('id', 0)}",
                "站点类型": str(r.get("报告编号", "")),
                "覆盖类目": "口碑报告",
                "status": "待接入",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条口碑报告记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理评论站点目录接入中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"站点配置 {entry_id} 不存在"}
        if entry.get("status") != "待接入":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已接入"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出评论站点目录数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"站点配置数据集",
            "operation": "接入",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
