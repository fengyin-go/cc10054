"""评论抓取任务领域服务：管理抓取任务的抓取流程、状态流转与跨模块数据链路。

数据链路位置：评论抓取任务是商品评论采集与口碑洞察平台的核心处理模块之一，负责把抓取任务的
抓取结果写入作者画像，并消费采集度量总览的产出记录，形成完整的跨模块数据流。
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


class ReviewCrawlService(BaseModuleService):
    MODULE = "review_crawl"
    ENTITY = "抓取任务"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["任务编号", "站点标识", "关键词标识", "抓取深度", "会话票据"]
    REQUIRED_FIELDS = ["任务编号", "站点标识", "关键词标识"]
    STATUS_ORDER = ["待执行", "执行中", "已完成", "失败待重试"]
    ACTION_RULES = {"启动任务": "执行中", "标记完成": "已完成", "重试任务": "执行中"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：评论抓取任务跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把评论抓取任务的抓取结果写入作者画像，形成评论抓取任务→作者画像的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"抓取任务 {entry_id} 不存在"}
        rows = store.rows("author_profile")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "作者指纹": f"评论抓取任务-{entry_id}",
            "站点集合": "review_crawl",
            "活跃度等级": str(entry_id),
            "status": "已建档",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "失败待重试"
        entry["pending"] = False
        return {"ok": True, "message": "抓取结果已写入作者画像", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取采集度量总览的产出记录并汇总为评论抓取任务消费台账。"""
        up_rows = [r for r in store.rows("platform_metrics") if r.get("status") == "告警"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "任务编号": f"消费-{r.get('id', 0)}",
                "站点标识": str(r.get("度量名称", "")),
                "关键词标识": "采集度量总览",
                "status": "待执行",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条采集度量总览记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理评论抓取任务抓取中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"抓取任务 {entry_id} 不存在"}
        if entry.get("status") != "待执行":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "执行中"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出评论抓取任务数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"抓取任务数据集",
            "operation": "抓取",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
