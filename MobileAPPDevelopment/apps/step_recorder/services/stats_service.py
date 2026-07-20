"""执行统计服务（M4 模块）

按 PRD 第 7 章实现 3 维统计：
- 按任务统计（每个任务的执行次数/成功率/平均时长）
- 按天统计（每日执行次数/成功率）
- 按触发源统计（手动/定时/间隔/随机）

变更记录:
- Q37 后续：M4 在本次对话内完成（Q41 确认）
- 数据源：M5 日志模块（log_service）尚未实现，本模块先用 mock 数据
- M0 数据层接入后替换为真实日志查询
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class TriggerSource(str, Enum):
    """触发源（PRD 第 6 章）"""

    MANUAL = "manual"            # 手动触发
    TIMER = "timer"              # 定时触发
    INTERVAL = "interval"        # 间隔触发
    RANDOM = "random"           # 随机触发


class ExecutionStatus(str, Enum):
    """执行状态"""

    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"
    RUNNING = "running"
    SKIPPED = "skipped"  # 占位步骤跳过


@dataclass
class ExecutionRecord:
    """单次执行记录（mock 数据，M5 实现真实日志后可移除）"""

    execution_id: str
    task_id: str
    task_name: str
    start_time: datetime
    end_time: datetime | None = None
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    trigger_source: TriggerSource = TriggerSource.MANUAL
    duration_ms: int = 0


@dataclass
class TaskStats:
    """按任务统计"""

    task_id: str
    task_name: str
    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0
    aborted_count: int = 0
    success_rate: float = 0.0
    avg_duration_ms: int = 0
    last_execution_time: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "aborted_count": self.aborted_count,
            "success_rate": round(self.success_rate, 4),
            "avg_duration_ms": self.avg_duration_ms,
            "last_execution_time": (
                self.last_execution_time.isoformat() if self.last_execution_time else None
            ),
        }


@dataclass
class DailyStats:
    """按天统计"""

    date: str  # YYYY-MM-DD
    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": round(self.success_rate, 4),
        }


@dataclass
class TriggerSourceStats:
    """按触发源统计"""

    trigger_source: TriggerSource
    total_executions: int = 0
    success_count: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "trigger_source": self.trigger_source.value,
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "success_rate": round(self.success_rate, 4),
        }


@dataclass
class OverallStats:
    """汇总统计"""

    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0
    aborted_count: int = 0
    overall_success_rate: float = 0.0
    avg_duration_ms: int = 0
    unique_tasks: int = 0

    def to_dict(self) -> dict:
        return {
            "total_executions": self.total_executions,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "aborted_count": self.aborted_count,
            "overall_success_rate": round(self.overall_success_rate, 4),
            "avg_duration_ms": self.avg_duration_ms,
            "unique_tasks": self.unique_tasks,
        }


def _default_mock_records() -> list[ExecutionRecord]:
    """mock 执行记录数据（M5 接入后替换）"""
    now = datetime.now()
    return [
        ExecutionRecord(
            execution_id="e1",
            task_id="t1",
            task_name="早晨例行程序",
            start_time=now - timedelta(days=1, hours=2),
            end_time=now - timedelta(days=1, hours=2, minutes=-15),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.TIMER,
            duration_ms=15000,
        ),
        ExecutionRecord(
            execution_id="e2",
            task_id="t1",
            task_name="早晨例行程序",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=3, minutes=-12),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.TIMER,
            duration_ms=12000,
        ),
        ExecutionRecord(
            execution_id="e3",
            task_id="t1",
            task_name="早晨例行程序",
            start_time=now - timedelta(hours=1),
            end_time=now - timedelta(hours=1, minutes=-5),
            status=ExecutionStatus.FAILED,
            trigger_source=TriggerSource.MANUAL,
            duration_ms=5000,
        ),
        ExecutionRecord(
            execution_id="e4",
            task_id="t2",
            task_name="工作日报生成",
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=2, minutes=-30),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.MANUAL,
            duration_ms=30000,
        ),
        ExecutionRecord(
            execution_id="e5",
            task_id="t2",
            task_name="工作日报生成",
            start_time=now - timedelta(days=1),
            end_time=now - timedelta(days=1, minutes=-28),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.INTERVAL,
            duration_ms=28000,
        ),
        ExecutionRecord(
            execution_id="e6",
            task_id="t3",
            task_name="学习计划",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=3, minutes=-20),
            status=ExecutionStatus.ABORTED,
            trigger_source=TriggerSource.MANUAL,
            duration_ms=20000,
        ),
        ExecutionRecord(
            execution_id="e7",
            task_id="t3",
            task_name="学习计划",
            start_time=now - timedelta(hours=5),
            end_time=now - timedelta(hours=5, minutes=-18),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.RANDOM,
            duration_ms=18000,
        ),
        ExecutionRecord(
            execution_id="e8",
            task_id="t4",
            task_name="娱乐时间",
            start_time=now - timedelta(days=4),
            end_time=now - timedelta(days=4, minutes=-45),
            status=ExecutionStatus.SUCCESS,
            trigger_source=TriggerSource.MANUAL,
            duration_ms=45000,
        ),
    ]


class StatsService:
    """统计服务

    提供 3 维统计查询接口。

    Attributes:
        records: 执行记录列表（M5 接入后从 log_service 加载）
    """

    def __init__(self, records: list[ExecutionRecord] | None = None) -> None:
        self._records = records if records is not None else _default_mock_records()

    @property
    def records(self) -> list[ExecutionRecord]:
        return self._records

    def get_overall_stats(self) -> OverallStats:
        """获取汇总统计"""
        if not self._records:
            return OverallStats()

        total = len(self._records)
        success = sum(1 for r in self._records if r.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for r in self._records if r.status == ExecutionStatus.FAILED)
        aborted = sum(1 for r in self._records if r.status == ExecutionStatus.ABORTED)
        durations = [r.duration_ms for r in self._records if r.duration_ms > 0]
        avg_duration = int(sum(durations) / len(durations)) if durations else 0
        unique_tasks = len({r.task_id for r in self._records})
        success_rate = success / total if total > 0 else 0.0

        return OverallStats(
            total_executions=total,
            success_count=success,
            failed_count=failed,
            aborted_count=aborted,
            overall_success_rate=success_rate,
            avg_duration_ms=avg_duration,
            unique_tasks=unique_tasks,
        )

    def get_stats_by_task(self) -> list[TaskStats]:
        """按任务统计"""
        task_map: dict[str, list[ExecutionRecord]] = {}
        for r in self._records:
            task_map.setdefault(r.task_id, []).append(r)

        result: list[TaskStats] = []
        for task_id, records in task_map.items():
            total = len(records)
            success = sum(1 for r in records if r.status == ExecutionStatus.SUCCESS)
            failed = sum(1 for r in records if r.status == ExecutionStatus.FAILED)
            aborted = sum(1 for r in records if r.status == ExecutionStatus.ABORTED)
            durations = [r.duration_ms for r in records if r.duration_ms > 0]
            avg_duration = int(sum(durations) / len(durations)) if durations else 0
            last_time = max((r.start_time for r in records), default=None)
            success_rate = success / total if total > 0 else 0.0

            result.append(
                TaskStats(
                    task_id=task_id,
                    task_name=records[0].task_name,
                    total_executions=total,
                    success_count=success,
                    failed_count=failed,
                    aborted_count=aborted,
                    success_rate=success_rate,
                    avg_duration_ms=avg_duration,
                    last_execution_time=last_time,
                )
            )

        # 按执行次数降序
        result.sort(key=lambda x: x.total_executions, reverse=True)
        return result

    def get_stats_by_day(self, days: int = 7) -> list[DailyStats]:
        """按天统计（最近 N 天）

        Args:
            days: 统计天数（默认 7 天）

        Returns:
            每日统计列表（按日期升序）
        """
        now = datetime.now()
        start_date = (now - timedelta(days=days - 1)).date()

        date_map: dict[str, list[ExecutionRecord]] = {}
        for r in self._records:
            if r.start_time.date() >= start_date:
                date_str = r.start_time.strftime("%Y-%m-%d")
                date_map.setdefault(date_str, []).append(r)

        result: list[DailyStats] = []
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            records = date_map.get(date, [])
            total = len(records)
            success = sum(1 for r in records if r.status == ExecutionStatus.SUCCESS)
            failed = sum(1 for r in records if r.status == ExecutionStatus.FAILED)
            success_rate = success / total if total > 0 else 0.0
            result.append(
                DailyStats(
                    date=date,
                    total_executions=total,
                    success_count=success,
                    failed_count=failed,
                    success_rate=success_rate,
                )
            )

        return result

    def get_stats_by_trigger_source(self) -> list[TriggerSourceStats]:
        """按触发源统计"""
        source_map: dict[TriggerSource, list[ExecutionRecord]] = {}
        for r in self._records:
            source_map.setdefault(r.trigger_source, []).append(r)

        result: list[TriggerSourceStats] = []
        for source in TriggerSource:
            records = source_map.get(source, [])
            total = len(records)
            success = sum(1 for r in records if r.status == ExecutionStatus.SUCCESS)
            success_rate = success / total if total > 0 else 0.0
            result.append(
                TriggerSourceStats(
                    trigger_source=source,
                    total_executions=total,
                    success_count=success,
                    success_rate=success_rate,
                )
            )

        return result

    def get_top_tasks(self, limit: int = 5) -> list[TaskStats]:
        """获取执行次数最多的 N 个任务"""
        all_stats = self.get_stats_by_task()
        return all_stats[:limit]
