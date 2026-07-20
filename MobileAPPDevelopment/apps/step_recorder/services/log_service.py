"""执行日志服务（M5 模块）

提供日志的：
- 增删查改（CRUD）
- 4 维过滤（任务/状态/触发源/时间范围，Q44）
- 关键字搜索（按任务名或日志ID，Q49）
- 自动清理（按保留条数，Q48）
- 按日期分组（Q47）

数据源：M5 阶段先用内存 mock 数据；M0 数据层接入后替换为 storage.py。

变更记录:
- Q42 决策：详情用独立路由 /logs/{id}，本服务返回单个日志（含步骤列表）
- Q44 决策：4 维过滤
- Q45 决策：清理策略为设置项清理（开关 + 保留条数）
- Q46 决策：列表项字段（任务名+状态+触发源+开始时间+耗时）
- Q47 决策：分组模式（date/flat）
- Q48 决策：设置项清理（独立"日志管理"区域，默认关闭，1-9999 条）
- Q49 决策：搜索 + 单条删除
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from models.log import (
    ExecutionLog,
    GroupMode,
    LogFilter,
    StepExecution,
    TimeRangeKey,
)
from services.stats_service import ExecutionStatus, TriggerSource


# ---- 默认 mock 数据 ----


def _default_mock_logs() -> list[ExecutionLog]:
    """默认 mock 执行日志（覆盖各种状态、触发源、任务、时间范围）"""
    now = datetime.now()
    return [
        # 今天 - 早晨例行程序 - 成功 - 定时触发
        ExecutionLog(
            log_id="log1",
            task_id="t1",
            task_name="早晨例行程序",
            task_icon="wb_sunny",
            trigger_source=TriggerSource.TIMER,
            status=ExecutionStatus.SUCCESS,
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(hours=2, minutes=-15),
            duration_ms=15000,
            step_executions=[
                StepExecution(
                    step_id="s1",
                    step_name="开机检查",
                    step_type="go_home",
                    icon="home",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(hours=2),
                    ended_at=now - timedelta(hours=2, seconds=-5),
                    duration_ms=5000,
                ),
                StepExecution(
                    step_id="s2",
                    step_name="喝水提醒",
                    step_type="notify",
                    icon="notifications",
                    order=2,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(hours=2, minutes=-5),
                    ended_at=now - timedelta(hours=2, minutes=-15),
                    duration_ms=10000,
                ),
            ],
        ),
        # 今天 - 工作日报 - 失败 - 手动触发
        ExecutionLog(
            log_id="log2",
            task_id="t2",
            task_name="工作日报生成",
            task_icon="work",
            trigger_source=TriggerSource.MANUAL,
            status=ExecutionStatus.FAILED,
            started_at=now - timedelta(hours=5),
            ended_at=now - timedelta(hours=5, minutes=-8),
            duration_ms=8000,
            error_message="第 2 步执行失败：网络连接超时",
            step_executions=[
                StepExecution(
                    step_id="s3",
                    step_name="收集工作内容",
                    step_type="open_app",
                    icon="apps",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(hours=5),
                    ended_at=now - timedelta(hours=5, seconds=-3),
                    duration_ms=3000,
                ),
                StepExecution(
                    step_id="s4",
                    step_name="发送日报",
                    step_type="notify",
                    icon="notifications",
                    order=2,
                    status=ExecutionStatus.FAILED,
                    started_at=now - timedelta(hours=5, minutes=-3),
                    ended_at=now - timedelta(hours=5, minutes=-8),
                    duration_ms=5000,
                    error_message="网络连接超时",
                ),
            ],
        ),
        # 昨天 - 学习计划 - 中止 - 间隔触发
        ExecutionLog(
            log_id="log3",
            task_id="t3",
            task_name="学习计划",
            task_icon="school",
            trigger_source=TriggerSource.INTERVAL,
            status=ExecutionStatus.ABORTED,
            started_at=now - timedelta(days=1, hours=3),
            ended_at=now - timedelta(days=1, hours=3, minutes=-10),
            duration_ms=10000,
            error_message="用户手动中止",
            step_executions=[
                StepExecution(
                    step_id="s5",
                    step_name="打开学习App",
                    step_type="open_app",
                    icon="apps",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=1, hours=3),
                    ended_at=now - timedelta(days=1, hours=3, seconds=-4),
                    duration_ms=4000,
                ),
                StepExecution(
                    step_id="s6",
                    step_name="开始学习",
                    step_type="delay",
                    icon="schedule",
                    order=2,
                    status=ExecutionStatus.ABORTED,
                    started_at=now - timedelta(days=1, hours=3, minutes=-4),
                    ended_at=now - timedelta(days=1, hours=3, minutes=-10),
                    duration_ms=6000,
                    error_message="用户手动中止",
                ),
            ],
        ),
        # 3 天前 - 早晨例行 - 成功 - 随机触发
        ExecutionLog(
            log_id="log4",
            task_id="t1",
            task_name="早晨例行程序",
            task_icon="wb_sunny",
            trigger_source=TriggerSource.RANDOM,
            status=ExecutionStatus.SUCCESS,
            started_at=now - timedelta(days=3, hours=1),
            ended_at=now - timedelta(days=3, hours=1, minutes=-20),
            duration_ms=20000,
            step_executions=[
                StepExecution(
                    step_id="s7",
                    step_name="开机检查",
                    step_type="go_home",
                    icon="home",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=3, hours=1),
                    ended_at=now - timedelta(days=3, hours=1, seconds=-5),
                    duration_ms=5000,
                ),
                StepExecution(
                    step_id="s8",
                    step_name="喝水提醒",
                    step_type="notify",
                    icon="notifications",
                    order=2,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=3, hours=1, minutes=-5),
                    ended_at=now - timedelta(days=3, hours=1, minutes=-20),
                    duration_ms=15000,
                ),
            ],
        ),
        # 7 天前 - 娱乐时间 - 成功 - 手动触发
        ExecutionLog(
            log_id="log5",
            task_id="t4",
            task_name="娱乐时间",
            task_icon="sports_esports",
            trigger_source=TriggerSource.MANUAL,
            status=ExecutionStatus.SUCCESS,
            started_at=now - timedelta(days=7),
            ended_at=now - timedelta(days=7, minutes=-30),
            duration_ms=30000,
            step_executions=[
                StepExecution(
                    step_id="s9",
                    step_name="打开游戏App",
                    step_type="open_app",
                    icon="apps",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=7),
                    ended_at=now - timedelta(days=7, seconds=-5),
                    duration_ms=5000,
                ),
                StepExecution(
                    step_id="s10",
                    step_name="调整音量",
                    step_type="volume",
                    icon="volume_up",
                    order=2,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=7, minutes=-5),
                    ended_at=now - timedelta(days=7, minutes=-30),
                    duration_ms=25000,
                ),
            ],
        ),
        # 15 天前 - 工作日报 - 成功 - 间隔触发（超出默认 7d 范围）
        ExecutionLog(
            log_id="log6",
            task_id="t2",
            task_name="工作日报生成",
            task_icon="work",
            trigger_source=TriggerSource.INTERVAL,
            status=ExecutionStatus.SUCCESS,
            started_at=now - timedelta(days=15),
            ended_at=now - timedelta(days=15, minutes=-25),
            duration_ms=25000,
            step_executions=[
                StepExecution(
                    step_id="s11",
                    step_name="收集工作内容",
                    step_type="open_app",
                    icon="apps",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=15),
                    ended_at=now - timedelta(days=15, seconds=-10),
                    duration_ms=10000,
                ),
                StepExecution(
                    step_id="s12",
                    step_name="发送日报",
                    step_type="notify",
                    icon="notifications",
                    order=2,
                    status=ExecutionStatus.SUCCESS,
                    started_at=now - timedelta(days=15, minutes=-10),
                    ended_at=now - timedelta(days=15, minutes=-25),
                    duration_ms=15000,
                ),
            ],
        ),
    ]


@dataclass
class LogGroup:
    """日志分组（按日期时使用）

    Attributes:
        key: 分组键（日期字符串 YYYY-MM-DD，flat 模式为 "all"）
        label: 分组显示名（如"今天"、"昨天"、"2026-07-15"、"全部日志"）
        logs: 该分组下的日志列表（按开始时间倒序）
    """

    key: str
    label: str
    logs: list[ExecutionLog] = field(default_factory=list)


class LogService:
    """执行日志服务

    提供日志的 CRUD、过滤、搜索、分组、清理能力。

    Attributes:
        logs: 内存日志列表（M0 接入后从 storage 加载）
    """

    def __init__(self, logs: list[ExecutionLog] | None = None) -> None:
        self._logs: list[ExecutionLog] = (
            logs if logs is not None else _default_mock_logs()
        )

    @property
    def logs(self) -> list[ExecutionLog]:
        """所有日志（按开始时间倒序）"""
        return sorted(self._logs, key=lambda x: x.started_at, reverse=True)

    # ---- 查询 ----

    def get_all(self) -> list[ExecutionLog]:
        """获取所有日志（按开始时间倒序）"""
        return self.logs

    def get_by_id(self, log_id: str) -> ExecutionLog | None:
        """根据 ID 获取日志"""
        for log in self._logs:
            if log.log_id == log_id:
                return log
        return None

    def get_by_task(self, task_id: str) -> list[ExecutionLog]:
        """获取指定任务的所有日志（按开始时间倒序）"""
        return sorted(
            [log for log in self._logs if log.task_id == task_id],
            key=lambda x: x.started_at,
            reverse=True,
        )

    def filter(self, filter_: LogFilter) -> list[ExecutionLog]:
        """按 4 维条件过滤日志（Q44）

        Args:
            filter_: 过滤条件

        Returns:
            过滤后的日志列表（按开始时间倒序）
        """
        result = list(self._logs)

        # 任务过滤
        if filter_.task_id:
            result = [log for log in result if log.task_id == filter_.task_id]

        # 状态过滤
        if filter_.status:
            result = [log for log in result if log.status == filter_.status]

        # 触发源过滤
        if filter_.trigger_source:
            result = [
                log for log in result if log.trigger_source == filter_.trigger_source
            ]

        # 时间范围过滤
        if filter_.time_range != "all":
            days_map = {"1d": 1, "7d": 7, "30d": 30}
            days = days_map.get(filter_.time_range, 0)
            if days > 0:
                cutoff = datetime.now() - timedelta(days=days)
                result = [log for log in result if log.started_at >= cutoff]

        # 关键字搜索（任务名或日志ID 模糊匹配）
        keyword = filter_.keyword.strip().lower()
        if keyword:
            result = [
                log
                for log in result
                if keyword in log.task_name.lower()
                or keyword in log.log_id.lower()
            ]

        return sorted(result, key=lambda x: x.started_at, reverse=True)

    def group(
        self,
        logs: list[ExecutionLog],
        mode: GroupMode = "date",
    ) -> list[LogGroup]:
        """将日志分组（Q47 两种模式）

        Args:
            logs: 待分组的日志列表
            mode: 分组模式（date 按日期 / flat 平铺）

        Returns:
            分组列表（按日期升序排列分组，分组内日志按开始时间倒序）
        """
        if mode == "flat":
            return [
                LogGroup(key="all", label="全部日志", logs=list(logs))
            ]

        # 按日期分组
        groups: dict[str, list[ExecutionLog]] = defaultdict(list)
        for log in logs:
            key = log.started_at.strftime("%Y-%m-%d")
            groups[key].append(log)

        result: list[LogGroup] = []
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        for date_str in sorted(groups.keys(), reverse=True):
            group_logs = sorted(
                groups[date_str], key=lambda x: x.started_at, reverse=True
            )
            # 生成显示标签
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                label = date_str
            else:
                if date_obj == today:
                    label = "今天"
                elif date_obj == yesterday:
                    label = "昨天"
                else:
                    label = date_str
            result.append(LogGroup(key=date_str, label=label, logs=group_logs))

        return result

    # ---- 增删改 ----

    def add(self, log: ExecutionLog) -> None:
        """添加新日志"""
        self._logs.append(log)

    def delete(self, log_id: str) -> bool:
        """删除指定日志（返回是否删除成功）"""
        for i, log in enumerate(self._logs):
            if log.log_id == log_id:
                self._logs.pop(i)
                return True
        return False

    def clear(self) -> int:
        """清空所有日志（返回删除条数）"""
        count = len(self._logs)
        self._logs.clear()
        return count

    def cleanup(self, keep_count: int) -> int:
        """自动清理：保留最近 N 条，删除其余（Q48）

        Args:
            keep_count: 保留的日志数量

        Returns:
            删除的日志数量
        """
        if keep_count < 0:
            keep_count = 0
        if len(self._logs) <= keep_count:
            return 0

        # 按开始时间倒序排序，保留前 keep_count 条
        sorted_logs = sorted(
            self._logs, key=lambda x: x.started_at, reverse=True
        )
        keep_logs = sorted_logs[:keep_count]
        removed_count = len(self._logs) - len(keep_logs)
        self._logs = keep_logs
        return removed_count

    # ---- 统计 ----

    def count(self) -> int:
        """日志总数"""
        return len(self._logs)

    def count_by_status(self) -> dict[ExecutionStatus, int]:
        """按状态分组计数"""
        result: dict[ExecutionStatus, int] = defaultdict(int)
        for log in self._logs:
            result[log.status] += 1
        return dict(result)

    def count_by_trigger_source(self) -> dict[TriggerSource, int]:
        """按触发源分组计数"""
        result: dict[TriggerSource, int] = defaultdict(int)
        for log in self._logs:
            result[log.trigger_source] += 1
        return dict(result)

    def get_unique_tasks(self) -> list[tuple[str, str, str]]:
        """获取所有出现过的任务（去重）

        Returns:
            列表，每项 (task_id, task_name, task_icon)
        """
        seen: dict[str, tuple[str, str]] = {}
        for log in self._logs:
            if log.task_id not in seen:
                seen[log.task_id] = (log.task_name, log.task_icon)
        return [
            (task_id, name, icon) for task_id, (name, icon) in seen.items()
        ]


# ---- 工具函数 ----


def format_relative_time(dt: datetime, now: datetime | None = None) -> str:
    """格式化相对时间（Q46 列表项字段）

    Args:
        dt: 待格式化的时间
        now: 当前时间（默认 datetime.now()）

    Returns:
        相对时间字符串（如"3 小时前"、"昨天"、"3 天前"、"7 月 15 日"）
    """
    if now is None:
        now = datetime.now()
    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"

    days = seconds // 86400
    if days == 1:
        return "昨天"
    if days < 7:
        return f"{days} 天前"
    if days < 30:
        return f"{days // 7} 周前"

    # 超过 30 天显示日期
    return dt.strftime("%-m 月 %-d 日") if hasattr(dt, "strftime") else str(dt)


def format_duration(duration_ms: int) -> str:
    """格式化耗时（Q46 列表项字段）

    Args:
        duration_ms: 毫秒数

    Returns:
        友好显示字符串（如"500ms"、"15s"、"1m20s"）
    """
    if duration_ms < 0:
        return "0s"
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    seconds = duration_ms // 1000
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rest_seconds = seconds % 60
    if minutes < 60:
        if rest_seconds > 0:
            return f"{minutes}m{rest_seconds}s"
        return f"{minutes}m"
    hours = minutes // 60
    rest_minutes = minutes % 60
    if rest_minutes > 0:
        return f"{hours}h{rest_minutes}m"
    return f"{hours}h"


def get_status_label(status: ExecutionStatus) -> str:
    """状态中文标签"""
    return {
        ExecutionStatus.SUCCESS: "成功",
        ExecutionStatus.FAILED: "失败",
        ExecutionStatus.ABORTED: "已中止",
        ExecutionStatus.RUNNING: "执行中",
        ExecutionStatus.SKIPPED: "已跳过",
    }.get(status, str(status))


def get_status_color(status: ExecutionStatus) -> str:
    """状态对应颜色（与 stats_view 一致）"""
    return {
        ExecutionStatus.SUCCESS: "#10b981",  # success
        ExecutionStatus.FAILED: "#ef4444",   # danger
        ExecutionStatus.ABORTED: "#6b7280",   # muted
        ExecutionStatus.RUNNING: "#2563eb",  # accent
        ExecutionStatus.SKIPPED: "#9ca3af",  # 浅灰
    }.get(status, "#6b7280")


def get_trigger_source_label(source: TriggerSource) -> str:
    """触发源中文标签"""
    return {
        TriggerSource.MANUAL: "手动",
        TriggerSource.TIMER: "定时",
        TriggerSource.INTERVAL: "间隔",
        TriggerSource.RANDOM: "随机",
    }.get(source, str(source))
