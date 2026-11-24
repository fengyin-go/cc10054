"""验证码闸口领域服务：管理闸口记录的校验流程、状态流转与跨模块数据链路。

数据链路位置：验证码闸口是商品评论采集与口碑洞察平台的核心处理模块之一，负责把闸口记录的
校验结果写入评论站点目录，并消费投诉聚类的产出记录，形成完整的跨模块数据流。
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


class CaptchaGateService(BaseModuleService):
    MODULE = "captcha_gate"
    ENTITY = "闸口记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["闸口编号", "站点标识", "触发频率", "处置策略", "冷却时长"]
    REQUIRED_FIELDS = ["闸口编号", "站点标识", "触发频率"]
    STATUS_ORDER = ["监控中", "已触发", "已冷却"]
    ACTION_RULES = {"触发闸口": "已触发", "解除冷却": "已冷却"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：验证码闸口跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把验证码闸口的校验结果写入评论站点目录，形成验证码闸口→评论站点目录的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"闸口记录 {entry_id} 不存在"}
        rows = store.rows("review_site")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "站点名称": f"验证码闸口-{entry_id}",
            "站点类型": "captcha_gate",
            "覆盖类目": str(entry_id),
            "status": "待接入",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已冷却"
        entry["pending"] = False
        return {"ok": True, "message": "校验结果已写入评论站点目录", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取投诉聚类的产出记录并汇总为验证码闸口消费台账。"""
        up_rows = [r for r in store.rows("complaint_cluster") if r.get("status") == "已升级"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "闸口编号": f"消费-{r.get('id', 0)}",
                "站点标识": str(r.get("簇编号", "")),
                "触发频率": "投诉聚类",
                "status": "监控中",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条投诉聚类记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理验证码闸口校验中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"闸口记录 {entry_id} 不存在"}
        if entry.get("status") != "监控中":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已触发"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出验证码闸口数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"闸口记录数据集",
            "operation": "校验",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
