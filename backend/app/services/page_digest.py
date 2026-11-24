"""页面快文摘取领域服务：管理页面摘录的抓取流程、状态流转与跨模块数据链路。

数据链路位置：页面快文摘取是商品评论采集与口碑洞察平台的核心处理模块之一，负责把页面摘录的
抓取结果写入口碑情感库，并消费评论站点目录的产出记录，形成完整的跨模块数据流。
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


class PageDigestService(BaseModuleService):
    MODULE = "page_digest"
    ENTITY = "页面摘录"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["摘录编号", "任务编号", "页面指纹", "正文摘要", "结构标记"]
    REQUIRED_FIELDS = ["摘录编号", "任务编号", "页面指纹"]
    STATUS_ORDER = ["已摘取", "已解析", "已丢弃"]
    ACTION_RULES = {"解析摘录": "已解析", "丢弃摘录": "已丢弃"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：页面快文摘取跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把页面快文摘取的抓取结果写入口碑情感库，形成页面快文摘取→口碑情感库的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"页面摘录 {entry_id} 不存在"}
        rows = store.rows("review_sentiment_store")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "样本编号": f"页面快文摘取-{entry_id}",
            "情感极性": "page_digest",
            "强度分值": str(entry_id),
            "status": "暂存",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已丢弃"
        entry["pending"] = False
        return {"ok": True, "message": "抓取结果已写入口碑情感库", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取评论站点目录的产出记录并汇总为页面快文摘取消费台账。"""
        up_rows = [r for r in store.rows("review_site") if r.get("status") == "已停用"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "摘录编号": f"消费-{r.get('id', 0)}",
                "任务编号": str(r.get("站点名称", "")),
                "页面指纹": "评论站点目录",
                "status": "已摘取",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条评论站点目录记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理页面快文摘取抓取中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"页面摘录 {entry_id} 不存在"}
        if entry.get("status") != "已摘取":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已解析"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出页面快文摘取数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"页面摘录数据集",
            "operation": "抓取",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
