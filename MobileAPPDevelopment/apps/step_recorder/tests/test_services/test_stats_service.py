"""stats_service 统计服务测试"""
from datetime import datetime, timedelta

import pytest

from services.stats_service import (
    ExecutionRecord,
    ExecutionStatus,
    StatsService,
    TriggerSource,
    _default_mock_records,
)


class TestMockData:
    """mock 数据完整性"""

    def test_mock_records_not_empty(self):
        records = _default_mock_records()
        assert len(records) > 0

    def test_mock_records_have_valid_ids(self):
        records = _default_mock_records()
        ids = [r.execution_id for r in records]
        assert len(ids) == len(set(ids))

    def test_mock_records_cover_statuses(self):
        records = _default_mock_records()
        statuses = {r.status for r in records}
        # 至少覆盖 3 种状态
        assert len(statuses) >= 3

    def test_mock_records_cover_trigger_sources(self):
        records = _default_mock_records()
        sources = {r.trigger_source for r in records}
        # 至少覆盖 3 种触发源
        assert len(sources) >= 3


class TestOverallStats:
    """汇总统计"""

    def test_empty_records_returns_zero(self):
        service = StatsService(records=[])
        stats = service.get_overall_stats()
        assert stats.total_executions == 0
        assert stats.success_count == 0
        assert stats.overall_success_rate == 0.0
        assert stats.unique_tasks == 0

    def test_overall_counts_correct(self):
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                status=ExecutionStatus.SUCCESS,
                duration_ms=1000,
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                status=ExecutionStatus.FAILED,
                duration_ms=500,
            ),
            ExecutionRecord(
                execution_id="e3",
                task_id="t2",
                task_name="任务2",
                start_time=datetime.now(),
                status=ExecutionStatus.ABORTED,
                duration_ms=200,
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_overall_stats()
        assert stats.total_executions == 3
        assert stats.success_count == 1
        assert stats.failed_count == 1
        assert stats.aborted_count == 1
        assert stats.unique_tasks == 2
        assert stats.overall_success_rate == pytest.approx(1 / 3, abs=0.01)

    def test_avg_duration_excludes_zero(self):
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                duration_ms=1000,
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                duration_ms=0,  # 应被排除
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_overall_stats()
        assert stats.avg_duration_ms == 1000  # (1000 + 0 排除) / 1 = 1000


class TestTaskStats:
    """按任务统计"""

    def test_empty_records_returns_empty_list(self):
        service = StatsService(records=[])
        stats = service.get_stats_by_task()
        assert stats == []

    def test_stats_grouped_by_task(self):
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                status=ExecutionStatus.SUCCESS,
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                status=ExecutionStatus.FAILED,
            ),
            ExecutionRecord(
                execution_id="e3",
                task_id="t2",
                task_name="任务2",
                start_time=datetime.now(),
                status=ExecutionStatus.SUCCESS,
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_stats_by_task()
        assert len(stats) == 2

    def test_stats_sorted_by_execution_count_desc(self):
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="少任务",
                start_time=datetime.now(),
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t2",
                task_name="多任务",
                start_time=datetime.now(),
            ),
            ExecutionRecord(
                execution_id="e3",
                task_id="t2",
                task_name="多任务",
                start_time=datetime.now(),
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_stats_by_task()
        assert stats[0].task_name == "多任务"
        assert stats[0].total_executions == 2
        assert stats[1].task_name == "少任务"
        assert stats[1].total_executions == 1

    def test_last_execution_time_is_max(self):
        now = datetime.now()
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="任务1",
                start_time=now - timedelta(hours=3),
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t1",
                task_name="任务1",
                start_time=now - timedelta(hours=1),
            ),
            ExecutionRecord(
                execution_id="e3",
                task_id="t1",
                task_name="任务1",
                start_time=now - timedelta(hours=2),
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_stats_by_task()
        assert stats[0].last_execution_time == now - timedelta(hours=1)


class TestDailyStats:
    """按天统计"""

    def test_returns_specified_days_count(self):
        records = []
        service = StatsService(records=records)
        stats = service.get_stats_by_day(days=7)
        assert len(stats) == 7

    def test_empty_records_returns_zero_counts(self):
        service = StatsService(records=[])
        stats = service.get_stats_by_day(days=7)
        for daily in stats:
            assert daily.total_executions == 0

    def test_records_outside_window_excluded(self):
        # 30 天前的记录应被排除
        old_record = ExecutionRecord(
            execution_id="old",
            task_id="t1",
            task_name="任务1",
            start_time=datetime.now() - timedelta(days=30),
            status=ExecutionStatus.SUCCESS,
        )
        service = StatsService(records=[old_record])
        stats = service.get_stats_by_day(days=7)
        total = sum(d.total_executions for d in stats)
        assert total == 0

    def test_today_record_counted(self):
        today_record = ExecutionRecord(
            execution_id="e1",
            task_id="t1",
            task_name="任务1",
            start_time=datetime.now(),
            status=ExecutionStatus.SUCCESS,
        )
        service = StatsService(records=[today_record])
        stats = service.get_stats_by_day(days=7)
        # 最后一天应有 1 条
        assert stats[-1].total_executions == 1

    def test_sorted_by_date_ascending(self):
        service = StatsService(records=[])
        stats = service.get_stats_by_day(days=7)
        dates = [d.date for d in stats]
        assert dates == sorted(dates)


class TestTriggerSourceStats:
    """按触发源统计"""

    def test_returns_all_trigger_sources(self):
        service = StatsService(records=[])
        stats = service.get_stats_by_trigger_source()
        sources = {s.trigger_source for s in stats}
        assert sources == set(TriggerSource)

    def test_counts_by_source(self):
        records = [
            ExecutionRecord(
                execution_id="e1",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                trigger_source=TriggerSource.MANUAL,
                status=ExecutionStatus.SUCCESS,
            ),
            ExecutionRecord(
                execution_id="e2",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                trigger_source=TriggerSource.MANUAL,
                status=ExecutionStatus.FAILED,
            ),
            ExecutionRecord(
                execution_id="e3",
                task_id="t1",
                task_name="任务1",
                start_time=datetime.now(),
                trigger_source=TriggerSource.TIMER,
                status=ExecutionStatus.SUCCESS,
            ),
        ]
        service = StatsService(records=records)
        stats = service.get_stats_by_trigger_source()
        manual_stat = next(s for s in stats if s.trigger_source == TriggerSource.MANUAL)
        timer_stat = next(s for s in stats if s.trigger_source == TriggerSource.TIMER)
        assert manual_stat.total_executions == 2
        assert manual_stat.success_count == 1
        assert timer_stat.total_executions == 1
        assert timer_stat.success_count == 1


class TestTopTasks:
    """Top 任务"""

    def test_returns_top_n(self):
        records = [
            ExecutionRecord(
                execution_id=f"e{i}",
                task_id=f"t{i}",
                task_name=f"任务{i}",
                start_time=datetime.now(),
            )
            for i in range(10)
        ]
        service = StatsService(records=records)
        top = service.get_top_tasks(limit=3)
        assert len(top) == 3

    def test_empty_records_returns_empty(self):
        service = StatsService(records=[])
        top = service.get_top_tasks(limit=5)
        assert top == []
