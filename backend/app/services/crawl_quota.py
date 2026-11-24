"""抓取配额领域服务：管理配额记录的抓取流程、状态流转与跨模块数据链路。

数据链路位置：抓取配额是商品评论采集与口碑洞察平台的核心处理模块之一，负责把配额记录的
抓取结果写入采集度量总览，并消费方面词抽取的产出记录，形成完整的跨模块数据流。
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


class CrawlQuotaService(BaseModuleService):
    MODULE = "crawl_quota"
    ENTITY = "配额记录"
    OPERATION_TERM = "抓取"
    LIST_FIELDS = ["配额编号", "站点标识", "日配额上限", "已用额度", "重置周期"]
    REQUIRED_FIELDS = ["配额编号", "站点标识", "日配额上限"]
    STATUS_ORDER = ["生效中", "已触顶", "已重置"]
    ACTION_RULES = {"上调配额": "生效中", "重置配额": "已重置"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：抓取配额跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把抓取配额的抓取结果写入采集度量总览，形成抓取配额→采集度量总览的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"配额记录 {entry_id} 不存在"}
        rows = store.rows("platform_metrics")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "度量名称": f"抓取配额-{entry_id}",
            "统计窗口": "crawl_quota",
            "当前值": str(entry_id),
            "status": "正常",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已重置"
        entry["pending"] = False
        return {"ok": True, "message": "抓取结果已写入采集度量总览", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取方面词抽取的产出记录并汇总为抓取配额消费台账。"""
        up_rows = [r for r in store.rows("aspect_extract") if r.get("status") == "已淘汰"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "配额编号": f"消费-{r.get('id', 0)}",
                "站点标识": str(r.get("方面词名称", "")),
                "日配额上限": "方面词抽取",
                "status": "生效中",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条方面词抽取记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理抓取配额抓取中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"配额记录 {entry_id} 不存在"}
        if entry.get("status") != "生效中":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已触顶"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出抓取配额数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"配额记录数据集",
            "operation": "抓取",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
