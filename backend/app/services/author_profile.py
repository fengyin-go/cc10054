"""作者画像领域服务：管理作者档案的校验流程、状态流转与跨模块数据链路。

数据链路位置：作者画像是商品评论采集与口碑洞察平台的核心处理模块之一，负责把作者档案的
校验结果写入验证码闸口，并消费评分归一的产出记录，形成完整的跨模块数据流。
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


class AuthorProfileService(BaseModuleService):
    MODULE = "author_profile"
    ENTITY = "作者档案"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["作者指纹", "站点集合", "活跃度等级", "可信等级", "最近活跃"]
    REQUIRED_FIELDS = ["作者指纹", "站点集合", "活跃度等级"]
    STATUS_ORDER = ["已建档", "已更新", "已冻结"]
    ACTION_RULES = {"更新画像": "已更新", "冻结画像": "已冻结"}
    NEGATIVE_ACTIONS = []

    # ---- 业务扩展：作者画像跨模块数据链路 ----

    def push_to_downstream(self, entry_id: int) -> dict[str, Any]:
        """把作者画像的校验结果写入验证码闸口，形成作者画像→验证码闸口的跨模块数据链路。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"作者档案 {entry_id} 不存在"}
        rows = store.rows("captcha_gate")
        new_id = _next_id(rows)
        rows.append({
            "id": new_id,
            "闸口编号": f"作者画像-{entry_id}",
            "站点标识": "author_profile",
            "触发频率": str(entry_id),
            "status": "监控中",
            "pending": True,
            "abnormal": False,
        })
        entry["status"] = "已冻结"
        entry["pending"] = False
        return {"ok": True, "message": "校验结果已写入验证码闸口", "downstream_id": new_id}

    def consume_from_upstream(self) -> dict[str, Any]:
        """读取评分归一的产出记录并汇总为作者画像消费台账。"""
        up_rows = [r for r in store.rows("rating_norm") if r.get("status") == "存疑"]
        rows = store.rows(self.MODULE)
        receipt_id = _next_id(rows)
        for idx, r in enumerate(up_rows[:5], start=1):
            rows.append({
                "id": receipt_id + idx - 1,
                "作者指纹": f"消费-{r.get('id', 0)}",
                "站点集合": str(r.get("记录编号", "")),
                "活跃度等级": "评分归一",
                "status": "已建档",
                "pending": True,
                "abnormal": False,
            })
        return {"ok": True, "message": f"已消费{len(up_rows[:5])}条评分归一记录", "consumed": len(up_rows[:5])}

    def recover_interrupted(self, entry_id: int) -> dict[str, Any]:
        """处理作者画像校验中断：续写未完成记录，不覆盖上次完整结果。"""
        entry = store.find(self.MODULE, entry_id)
        if entry is None:
            return {"ok": False, "message": f"作者档案 {entry_id} 不存在"}
        if entry.get("status") != "已建档":
            return {"ok": False, "message": "仅中断中的记录可恢复"}
        entry["status"] = "已更新"
        entry["recovered_at"] = _now_iso()
        entry["pending"] = False
        return {"ok": True, "message": "已从中断点续写", "recovered": True, "entry_id": entry_id}

    def quality_snapshot(self) -> dict[str, Any]:
        """输出作者画像数据集质量快照，供跨模块审计与容量锚点回查。"""
        rows = store.rows(self.MODULE)
        by_status = {s: sum(1 for r in rows if r.get("status") == s) for s in self.STATUS_ORDER}
        return {
            "module": self.MODULE,
            "entity": self.ENTITY,
            "artifact": f"作者档案数据集",
            "operation": "校验",
            "total": len(rows),
            "by_status": by_status,
            "abnormal": sum(1 for r in rows if r.get("abnormal")),
            "snapshot_at": _now_iso(),
        }
