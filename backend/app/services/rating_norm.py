"""评分归一领域服务：管理归一记录的校验流程、状态流转与跨模块数据链路。

数据链路位置：评分归一是商品评论采集与口碑洞察平台的核心处理模块之一，负责把归一记录的
校验结果写入投诉聚类，并消费评论抓取任务的产出记录，形成完整的跨模块数据流。
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


class RatingNormService(BaseModuleService):
    MODULE = "rating_norm"
    ENTITY = "归一记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["记录编号", "原始评分", "评分制式", "归一评分", "置信标记"]
    REQUIRED_FIELDS = ["记录编号", "原始评分", "评分制式"]
    STATUS_ORDER = ["待归一", "已归一", "存疑"]
    ACTION_RULES = {"执行归一": "已归一", "标记存疑": "存疑"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：评分归一跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把评分归一的校验结果写入投诉聚类，形成评分归一→投诉聚类的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"归一记录 {entry_id} 不存在"}
        rows = store.rows("complaint_cluster")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "簇编号": f"评分归一-{entry_id}",
            "簇主题": "rating_norm",
            "簇内条数": str(entry_id),
            "status": "新建",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "存疑"
        entry["pending"] = False
        return {"ok": True, "message": "校验结果已写入投诉聚类", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取评论抓取任务的产出记录并汇总为评分归一消费台账。"""
        up_rows = [r for r in store.rows("review_crawl") if r.get("status") == "失败待重试"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "记录编号": f"消费-{r.get('id', 0)}",
                "原始评分": str(r.get("任务编号", "")),
                "评分制式": "评论抓取任务",
                "status": "待归一",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条评论抓取任务记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理评分归一校验中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"归一记录 {entry_id} 不存在"}
        if entry.get("status") != "待归一":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已归一"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出评分归一数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"归一记录数据集",
            "operation": "校验",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
