"""关键词种子池领域服务：管理关键词的校验流程、状态流转与跨模块数据链路。

数据链路位置：关键词种子池是商品评论采集与口碑洞察平台的核心处理模块之一，负责把关键词的
校验结果写入评论去重，并消费标注复核台的产出记录，形成完整的跨模块数据流。
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


class SeedKeywordService(BaseModuleService):
    MODULE = "seed_keyword"
    ENTITY = "关键词"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["关键词名称", "所属类目", "搜索意图", "优先级", "轮换周期"]
    REQUIRED_FIELDS = ["关键词名称", "所属类目", "搜索意图"]
    STATUS_ORDER = ["草稿", "生效中", "已轮换"]
    ACTION_RULES = {"启用关键词": "生效中", "轮换关键词": "已轮换"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：关键词种子池跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把关键词种子池的校验结果写入评论去重，形成关键词种子池→评论去重的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"关键词 {entry_id} 不存在"}
        rows = store.rows("review_dedup")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "记录编号": f"关键词种子池-{entry_id}",
            "评论指纹": "seed_keyword",
            "相似簇号": str(entry_id),
            "status": "待比对",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已轮换"
        entry["pending"] = False
        return {"ok": True, "message": "校验结果已写入评论去重", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取标注复核台的产出记录并汇总为关键词种子池消费台账。"""
        up_rows = [r for r in store.rows("sentiment_review") if r.get("status") == "已裁定"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "关键词名称": f"消费-{r.get('id', 0)}",
                "所属类目": str(r.get("事项编号", "")),
                "搜索意图": "标注复核台",
                "status": "草稿",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条标注复核台记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理关键词种子池校验中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"关键词 {entry_id} 不存在"}
        if entry.get("status") != "草稿":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "生效中"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出关键词种子池数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"关键词数据集",
            "operation": "校验",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
