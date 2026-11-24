"""评论解析器领域服务：管理解析规则的解析流程、状态流转与跨模块数据链路。

数据链路位置：评论解析器是商品评论采集与口碑洞察平台的核心处理模块之一，负责把解析规则的
解析结果写入方面词抽取，并消费关键词种子池的产出记录，形成完整的跨模块数据流。
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


class ReviewParseService(BaseModuleService):
    MODULE = "review_parse"
    ENTITY = "解析规则"
    OPERATION_TERM = "解析"
    LIST_FIELDS = ["规则名称", "站点标识", "字段映射", "嵌套层级", "容错策略"]
    REQUIRED_FIELDS = ["规则名称", "站点标识", "字段映射"]
    STATUS_ORDER = ["草稿", "已生效", "已停用"]
    ACTION_RULES = {"生效规则": "已生效", "停用规则": "已停用"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：评论解析器跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把评论解析器的解析结果写入方面词抽取，形成评论解析器→方面词抽取的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"解析规则 {entry_id} 不存在"}
        rows = store.rows("aspect_extract")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "方面词名称": f"评论解析器-{entry_id}",
            "关联类目": "review_parse",
            "出现频次": str(entry_id),
            "status": "候选",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已停用"
        entry["pending"] = False
        return {"ok": True, "message": "解析结果已写入方面词抽取", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取关键词种子池的产出记录并汇总为评论解析器消费台账。"""
        up_rows = [r for r in store.rows("seed_keyword") if r.get("status") == "已轮换"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "规则名称": f"消费-{r.get('id', 0)}",
                "站点标识": str(r.get("关键词名称", "")),
                "字段映射": "关键词种子池",
                "status": "草稿",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条关键词种子池记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理评论解析器解析中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"解析规则 {entry_id} 不存在"}
        if entry.get("status") != "草稿":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已生效"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出评论解析器数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"解析规则数据集",
            "operation": "解析",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
