"""log_service 日志服务测试（M5）

覆盖：
- mock 数据完整性
- CRUD（add/delete/clear/get_by_id/get_by_task）
- 4 维过滤（task_id/status/trigger_source/time_range）
- 关键字搜索
- 分组（date/flat）
- 自动清理 cleanup
- 统计 count_by_status/count_by_trigger_source/get_unique_tasks
- 工具函数 format_relative_time/format_duration/get_status_label
"""
from datetime import datetime, timedelta

import pytest

from models.log import ExecutionLog, LogFilter, StepExecution
from services.log_service import (
    LogGroup,
    LogService,
    _default_mock_logs,
    format_duration,
    format_relative_time,
    get_status_color,
    get_status_label,
    get_trigger_source_label,
)
from services.stats_service import ExecutionStatus, TriggerSource


# ---- mock 数据 ----


class TestMockData:
    """mock 数据完整性"""

    def test_mock_logs_not_empty(self):
        logs = _default_mock_logs()
        assert len(logs) > 0

    def test_mock_logs_have_unique_ids(self):
        logs = _default_mock_logs()
        ids = [log.log_id for log in logs]
        assert len(ids) == len(set(ids))

    def test_mock_logs_cover_statuses(self):
        logs = _default_mock_logs()
        statuses = {log.status for log in logs}
        # 至少覆盖 3 种状态
        assert len(statuses) >= 3
        assert ExecutionStatus.SUCCESS in statuses
        assert ExecutionStatus.FAILED in statuses

    def test_mock_logs_cover_trigger_sources(self):
        logs = _default_mock_logs()
        sources = {log.trigger_source for log in logs}
        # 至少覆盖 3 种触发源
        assert len(sources) >= 3

    def test_mock_logs_have_step_executions(self):
        logs = _default_mock_logs()
        for log in logs:
            assert len(log.step_executions) > 0, (
                f"日志 {log.log_id} 没有步骤执行记录"
            )

    def test_mock_logs_valid_duration(self):
        """每条日志的 duration_ms 应非负"""
        logs = _default_mock_logs()
        for log in logs:
            assert log.duration_ms >= 0


# ---- CRUD ----


class TestCRUD:
    """增删改查"""

    def test_get_all_returns_sorted_by_started_at_desc(self):
        svc = LogService()
        logs = svc.get_all()
        assert len(logs) > 0
        # 检查是否按开始时间倒序
        for i in range(len(logs) - 1):
            assert logs[i].started_at >= logs[i + 1].started_at

    def test_get_by_id_existing(self):
        svc = LogService()
        log = svc.get_by_id("log1")
        assert log is not None
        assert log.log_id == "log1"
        assert log.task_id == "t1"

    def test_get_by_id_not_found(self):
        svc = LogService()
        assert svc.get_by_id("nonexistent") is None

    def test_get_by_task(self):
        svc = LogService()
        logs = svc.get_by_task("t1")
        assert len(logs) > 0
        for log in logs:
            assert log.task_id == "t1"

    def test_get_by_task_empty(self):
        svc = LogService()
        logs = svc.get_by_task("nonexistent")
        assert logs == []

    def test_add(self):
        svc = LogService(logs=[])
        new_log = ExecutionLog(
            log_id="new1",
            task_id="t1",
            task_name="测试任务",
            started_at=datetime.now(),
        )
        svc.add(new_log)
        assert svc.count() == 1
        assert svc.get_by_id("new1") is not None

    def test_delete_existing(self):
        svc = LogService()
        initial_count = svc.count()
        assert svc.delete("log1") is True
        assert svc.count() == initial_count - 1
        assert svc.get_by_id("log1") is None

    def test_delete_nonexistent(self):
        svc = LogService()
        initial_count = svc.count()
        assert svc.delete("nonexistent") is False
        assert svc.count() == initial_count

    def test_clear(self):
        svc = LogService()
        count = svc.clear()
        assert count > 0
        assert svc.count() == 0


# ---- 过滤 ----


class TestFilter:
    """4 维过滤（Q44）"""

    def test_filter_no_condition_returns_all(self):
        svc = LogService()
        result = svc.filter(LogFilter())
        assert len(result) == svc.count()

    def test_filter_by_task(self):
        svc = LogService()
        result = svc.filter(LogFilter(task_id="t1"))
        for log in result:
            assert log.task_id == "t1"

    def test_filter_by_status(self):
        svc = LogService()
        result = svc.filter(LogFilter(status=ExecutionStatus.FAILED))
        for log in result:
            assert log.status == ExecutionStatus.FAILED

    def test_filter_by_trigger_source(self):
        svc = LogService()
        result = svc.filter(LogFilter(trigger_source=TriggerSource.MANUAL))
        for log in result:
            assert log.trigger_source == TriggerSource.MANUAL

    def test_filter_by_time_range_1d(self):
        svc = LogService()
        result = svc.filter(LogFilter(time_range="1d"))
        cutoff = datetime.now() - timedelta(days=1)
        for log in result:
            assert log.started_at >= cutoff

    def test_filter_by_time_range_7d(self):
        svc = LogService()
        result = svc.filter(LogFilter(time_range="7d"))
        cutoff = datetime.now() - timedelta(days=7)
        for log in result:
            assert log.started_at >= cutoff

    def test_filter_by_time_range_30d(self):
        svc = LogService()
        result = svc.filter(LogFilter(time_range="30d"))
        cutoff = datetime.now() - timedelta(days=30)
        for log in result:
            assert log.started_at >= cutoff

    def test_filter_by_time_range_all(self):
        svc = LogService()
        result = svc.filter(LogFilter(time_range="all"))
        assert len(result) == svc.count()

    def test_filter_combined(self):
        """组合过滤：任务 + 状态"""
        svc = LogService()
        result = svc.filter(
            LogFilter(task_id="t1", status=ExecutionStatus.SUCCESS)
        )
        for log in result:
            assert log.task_id == "t1"
            assert log.status == ExecutionStatus.SUCCESS

    def test_filter_returns_sorted_desc(self):
        svc = LogService()
        result = svc.filter(LogFilter())
        for i in range(len(result) - 1):
            assert result[i].started_at >= result[i + 1].started_at


# ---- 关键字搜索 ----


class TestSearch:
    """关键字搜索（Q49）"""

    def test_search_by_task_name(self):
        svc = LogService()
        result = svc.filter(LogFilter(keyword="早晨"))
        for log in result:
            assert "早晨" in log.task_name

    def test_search_by_log_id(self):
        svc = LogService()
        result = svc.filter(LogFilter(keyword="log1"))
        assert len(result) == 1
        assert result[0].log_id == "log1"

    def test_search_case_insensitive(self):
        svc = LogService()
        # log_id 大小写不敏感
        result = svc.filter(LogFilter(keyword="LOG1"))
        assert len(result) == 1

    def test_search_empty_keyword_returns_all(self):
        svc = LogService()
        result = svc.filter(LogFilter(keyword=""))
        assert len(result) == svc.count()

    def test_search_whitespace_stripped(self):
        svc = LogService()
        result = svc.filter(LogFilter(keyword="  log1  "))
        assert len(result) == 1

    def test_search_no_match(self):
        svc = LogService()
        result = svc.filter(LogFilter(keyword="不存在的关键字xxx"))
        assert result == []


# ---- 分组 ----


class TestGroup:
    """分组（Q47）"""

    def test_group_flat_mode(self):
        svc = LogService()
        logs = svc.get_all()
        groups = svc.group(logs, mode="flat")
        assert len(groups) == 1
        assert groups[0].key == "all"
        assert len(groups[0].logs) == len(logs)

    def test_group_date_mode_multiple_groups(self):
        svc = LogService()
        logs = svc.get_all()
        groups = svc.group(logs, mode="date")
        # mock 数据跨多天，至少有 2 个分组
        assert len(groups) >= 2

    def test_group_date_mode_groups_sorted_desc(self):
        svc = LogService()
        logs = svc.get_all()
        groups = svc.group(logs, mode="date")
        # 检查分组按日期倒序
        for i in range(len(groups) - 1):
            assert groups[i].key >= groups[i + 1].key

    def test_group_date_mode_today_label(self):
        svc = LogService()
        today_log = ExecutionLog(
            log_id="today_log",
            task_id="t1",
            task_name="今天的任务",
            started_at=datetime.now(),
        )
        svc.add(today_log)
        groups = svc.group(svc.get_all(), mode="date")
        today_group = next((g for g in groups if g.key == datetime.now().strftime("%Y-%m-%d")), None)
        assert today_group is not None
        assert today_group.label == "今天"

    def test_group_date_mode_yesterday_label(self):
        svc = LogService()
        yesterday_log = ExecutionLog(
            log_id="yesterday_log",
            task_id="t1",
            task_name="昨天的任务",
            started_at=datetime.now() - timedelta(days=1),
        )
        svc.add(yesterday_log)
        groups = svc.group(svc.get_all(), mode="date")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_group = next((g for g in groups if g.key == yesterday_str), None)
        assert yesterday_group is not None
        assert yesterday_group.label == "昨天"

    def test_group_logs_within_group_sorted_desc(self):
        svc = LogService()
        # 添加两条同一天的日志，时间不同
        now = datetime.now()
        svc.add(ExecutionLog(log_id="t_a", task_id="t1", task_name="A", started_at=now - timedelta(hours=1)))
        svc.add(ExecutionLog(log_id="t_b", task_id="t1", task_name="B", started_at=now))
        groups = svc.group(svc.get_all(), mode="date")
        today_group = next(g for g in groups if g.key == now.strftime("%Y-%m-%d"))
        for i in range(len(today_group.logs) - 1):
            assert today_group.logs[i].started_at >= today_group.logs[i + 1].started_at


# ---- 清理 ----


class TestCleanup:
    """自动清理（Q48）"""

    def test_cleanup_keep_more_than_count(self):
        svc = LogService()
        initial = svc.count()
        removed = svc.cleanup(keep_count=initial + 100)
        assert removed == 0
        assert svc.count() == initial

    def test_cleanup_keep_zero(self):
        svc = LogService()
        initial = svc.count()
        removed = svc.cleanup(keep_count=0)
        assert removed == initial
        assert svc.count() == 0

    def test_cleanup_keep_partial(self):
        svc = LogService()
        initial = svc.count()
        keep = max(1, initial // 2)
        removed = svc.cleanup(keep_count=keep)
        assert removed == initial - keep
        assert svc.count() == keep

    def test_cleanup_keeps_most_recent(self):
        svc = LogService()
        svc.clear()
        # 添加 5 条不同时间的日志
        now = datetime.now()
        for i in range(5):
            svc.add(ExecutionLog(
                log_id=f"keep_{i}",
                task_id="t1",
                task_name=f"任务 {i}",
                started_at=now - timedelta(days=i),
            ))
        svc.cleanup(keep_count=2)
        assert svc.count() == 2
        # 保留的应该是最近 2 条
        kept_ids = {log.log_id for log in svc.get_all()}
        assert "keep_0" in kept_ids
        assert "keep_1" in kept_ids

    def test_cleanup_negative_keep(self):
        svc = LogService()
        initial = svc.count()
        removed = svc.cleanup(keep_count=-10)
        assert removed == initial
        assert svc.count() == 0


# ---- 统计 ----


class TestStatistics:
    """统计"""

    def test_count(self):
        svc = LogService()
        assert svc.count() > 0

    def test_count_by_status(self):
        svc = LogService()
        counts = svc.count_by_status()
        assert sum(counts.values()) == svc.count()
        assert ExecutionStatus.SUCCESS in counts

    def test_count_by_trigger_source(self):
        svc = LogService()
        counts = svc.count_by_trigger_source()
        assert sum(counts.values()) == svc.count()

    def test_get_unique_tasks(self):
        svc = LogService()
        tasks = svc.get_unique_tasks()
        assert len(tasks) > 0
        # 每项是三元组 (task_id, task_name, task_icon)
        for task in tasks:
            assert len(task) == 3
        # 去重检查
        task_ids = [t[0] for t in tasks]
        assert len(task_ids) == len(set(task_ids))


# ---- ExecutionLog 模型 ----


class TestExecutionLogModel:
    """ExecutionLog 模型方法"""

    def test_step_count(self):
        log = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            step_executions=[
                StepExecution(step_id="s1", step_name="A", step_type="click"),
                StepExecution(step_id="s2", step_name="B", step_type="delay"),
            ],
        )
        assert log.step_count == 2

    def test_success_step_count(self):
        log = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            step_executions=[
                StepExecution(step_id="s1", step_name="A", step_type="click", status=ExecutionStatus.SUCCESS),
                StepExecution(step_id="s2", step_name="B", step_type="delay", status=ExecutionStatus.FAILED),
                StepExecution(step_id="s3", step_name="C", step_type="delay", status=ExecutionStatus.SUCCESS),
            ],
        )
        assert log.success_step_count == 2
        assert log.failed_step_count == 1

    def test_get_step(self):
        log = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            step_executions=[
                StepExecution(step_id="s1", step_name="A", step_type="click"),
            ],
        )
        assert log.get_step("s1") is not None
        assert log.get_step("nonexistent") is None

    def test_is_complete(self):
        log_running = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            status=ExecutionStatus.RUNNING,
        )
        assert not log_running.is_complete()

        log_success = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            status=ExecutionStatus.SUCCESS,
        )
        assert log_success.is_complete()

    def test_to_dict(self):
        log = ExecutionLog(
            log_id="t",
            task_id="t1",
            task_name="test",
            status=ExecutionStatus.FAILED,
            error_message="测试错误",
        )
        d = log.to_dict()
        assert d["log_id"] == "t"
        assert d["status"] == "failed"
        assert d["error_message"] == "测试错误"
        assert d["step_executions"] == []

    def test_step_execution_to_dict(self):
        step = StepExecution(
            step_id="s1",
            step_name="测试",
            step_type="click",
            status=ExecutionStatus.SUCCESS,
        )
        d = step.to_dict()
        assert d["step_id"] == "s1"
        assert d["step_name"] == "测试"
        assert d["status"] == "success"


# ---- 工具函数 ----


class TestFormatFunctions:
    """格式化工具函数"""

    def test_format_duration_zero(self):
        assert format_duration(0) == "0ms"

    def test_format_duration_ms(self):
        assert format_duration(500) == "500ms"

    def test_format_duration_seconds(self):
        assert format_duration(1500) == "1s"
        assert format_duration(59000) == "59s"

    def test_format_duration_minutes(self):
        assert format_duration(60000) == "1m"
        assert format_duration(80000) == "1m20s"

    def test_format_duration_hours(self):
        assert format_duration(3600000) == "1h"
        assert format_duration(3660000) == "1h1m"

    def test_format_duration_negative(self):
        assert format_duration(-100) == "0s"

    def test_format_relative_time_just_now(self):
        now = datetime.now()
        # 30 秒前
        dt = now - timedelta(seconds=30)
        assert format_relative_time(dt, now=now) == "刚刚"

    def test_format_relative_time_minutes(self):
        now = datetime.now()
        dt = now - timedelta(minutes=5)
        assert format_relative_time(dt, now=now) == "5 分钟前"

    def test_format_relative_time_hours(self):
        now = datetime.now()
        dt = now - timedelta(hours=3)
        assert format_relative_time(dt, now=now) == "3 小时前"

    def test_format_relative_time_yesterday(self):
        now = datetime.now()
        dt = now - timedelta(days=1)
        assert format_relative_time(dt, now=now) == "昨天"

    def test_format_relative_time_days(self):
        now = datetime.now()
        dt = now - timedelta(days=3)
        assert format_relative_time(dt, now=now) == "3 天前"

    def test_format_relative_time_weeks(self):
        now = datetime.now()
        dt = now - timedelta(days=14)
        assert format_relative_time(dt, now=now) == "2 周前"

    def test_get_status_label(self):
        assert get_status_label(ExecutionStatus.SUCCESS) == "成功"
        assert get_status_label(ExecutionStatus.FAILED) == "失败"
        assert get_status_label(ExecutionStatus.ABORTED) == "已中止"
        assert get_status_label(ExecutionStatus.RUNNING) == "执行中"

    def test_get_status_color(self):
        assert get_status_color(ExecutionStatus.SUCCESS) == "#10b981"
        assert get_status_color(ExecutionStatus.FAILED) == "#ef4444"
        assert get_status_color(ExecutionStatus.RUNNING) == "#2563eb"

    def test_get_trigger_source_label(self):
        assert get_trigger_source_label(TriggerSource.MANUAL) == "手动"
        assert get_trigger_source_label(TriggerSource.TIMER) == "定时"
        assert get_trigger_source_label(TriggerSource.INTERVAL) == "间隔"
        assert get_trigger_source_label(TriggerSource.RANDOM) == "随机"


# ---- LogFilter 数据结构 ----


class TestLogFilter:
    """LogFilter 默认值"""

    def test_default_filter(self):
        f = LogFilter()
        assert f.task_id is None
        assert f.status is None
        assert f.trigger_source is None
        assert f.time_range == "all"
        assert f.keyword == ""
