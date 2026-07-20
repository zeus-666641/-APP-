"""执行日志数据模型（M5 模块）

按 PRD 第 8 章设计：
- ExecutionLog：单次任务执行日志（含元信息 + 步骤执行列表）
- StepExecution：单步执行记录（时间轴节点）

枚举复用 stats_service 中的 TriggerSource / ExecutionStatus，避免重复定义。

变更记录:
- Q42 决策：详情用独立路由 /logs/{id}
- Q43 决策：步骤列表用时间轴样式
- Q44 决策：列表过滤 4 维（状态/任务/触发源/时间范围）
- Q46 决策：列表项显示 任务名+状态+触发源+开始时间(相对)+耗时
- Q47 决策：列表两种分组模式（按日期/平铺），默认按日期
- Q49 决策：列表支持搜索 + 单条删除（按钮在卡片左下角）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from services.stats_service import ExecutionStatus, TriggerSource


# ---- 过滤器数据结构 ----

TimeRangeKey = Literal["all", "1d", "7d", "30d"]
GroupMode = Literal["date", "flat"]


@dataclass
class LogFilter:
    """日志列表过滤器（Q44 4 维过滤）

    Attributes:
        task_id: 任务过滤（None 表示不过滤）
        status: 状态过滤（None 表示不过滤）
        trigger_source: 触发源过滤（None 表示不过滤）
        time_range: 时间范围（all/1d/7d/30d）
        keyword: 搜索关键字（按任务名或日志ID 模糊匹配）
    """

    task_id: str | None = None
    status: ExecutionStatus | None = None
    trigger_source: TriggerSource | None = None
    time_range: TimeRangeKey = "all"
    keyword: str = ""


# ---- 数据模型 ----


@dataclass
class StepExecution:
    """单步执行记录（时间轴节点，Q43）

    Attributes:
        step_id: 步骤 ID（关联 step.id）
        step_name: 步骤名（冗余存储，避免历史日志因步骤改名失真）
        step_type: 步骤类型 ID（如 "click"）
        icon: 步骤图标（Material icon name）
        order: 在任务中的序号（从 1 开始）
        status: 执行状态
        started_at: 开始时间
        ended_at: 结束时间（None 表示进行中/未结束）
        duration_ms: 耗时（毫秒）
        error_message: 失败时的错误信息（成功时为空字符串）
        params_snapshot: 步骤参数快照（用于回溯，可能为空 dict）
    """

    step_id: str
    step_name: str
    step_type: str
    icon: str = "play_arrow"
    order: int = 0
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    duration_ms: int = 0
    error_message: str = ""
    params_snapshot: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_type": self.step_type,
            "icon": self.icon,
            "order": self.order,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "params_snapshot": dict(self.params_snapshot),
        }


@dataclass
class ExecutionLog:
    """单次任务执行日志（PRD 13.2 ER 图 + 步骤明细）

    Attributes:
        log_id: 日志唯一标识
        task_id: 关联的任务 ID
        task_name: 任务名（冗余存储，避免历史日志因任务改名失真）
        task_icon: 任务图标（冗余存储）
        trigger_source: 触发源（手动/定时/间隔/随机）
        status: 整体执行状态
        started_at: 开始时间
        ended_at: 结束时间（None 表示进行中）
        duration_ms: 总耗时（毫秒）
        step_executions: 步骤执行列表（按 order 升序）
        error_message: 失败时的整体错误信息
        metadata: 扩展元数据（如触发时上下文）
    """

    log_id: str
    task_id: str
    task_name: str
    task_icon: str = "play_arrow"
    trigger_source: TriggerSource = TriggerSource.MANUAL
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    duration_ms: int = 0
    step_executions: list[StepExecution] = field(default_factory=list)
    error_message: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_icon": self.task_icon,
            "trigger_source": self.trigger_source.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_ms": self.duration_ms,
            "step_executions": [s.to_dict() for s in self.step_executions],
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }

    @property
    def step_count(self) -> int:
        """步骤总数"""
        return len(self.step_executions)

    @property
    def success_step_count(self) -> int:
        """成功步骤数"""
        return sum(
            1 for s in self.step_executions if s.status == ExecutionStatus.SUCCESS
        )

    @property
    def failed_step_count(self) -> int:
        """失败步骤数"""
        return sum(
            1 for s in self.step_executions if s.status == ExecutionStatus.FAILED
        )

    def get_step(self, step_id: str) -> StepExecution | None:
        """根据 step_id 查找步骤执行记录"""
        for s in self.step_executions:
            if s.step_id == step_id:
                return s
        return None

    def is_complete(self) -> bool:
        """是否已完成（非 RUNNING 状态）"""
        return self.status != ExecutionStatus.RUNNING
