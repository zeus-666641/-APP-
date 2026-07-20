"""log_card 组件测试（M5）"""
from datetime import datetime, timedelta

import flet as ft
import pytest

from models.log import ExecutionLog, StepExecution
from services.stats_service import ExecutionStatus, TriggerSource
from views.components.log_card import LogCard, LogCardData


class _FakeEvent:
    """简易 ControlEvent mock"""

    def __init__(self, page=None):
        self.page = page
        self.stop_propagation = False
        self.data = None


class _FakePage:
    def __init__(self):
        self.overlay = []
        self._last_route = None

    def go(self, route):
        self._last_route = route

    def update(self):
        pass


class TestLogCardData:
    """LogCardData 数据结构"""

    def test_default_construction(self):
        data = LogCardData(
            log_id="log1",
            task_id="t1",
            task_name="测试任务",
        )
        assert data.log_id == "log1"
        assert data.task_id == "t1"
        assert data.task_name == "测试任务"
        assert data.task_icon == "play_arrow"
        assert data.status == "success"
        assert data.trigger_source == "manual"
        assert data.duration_ms == 0
        assert data.step_count == 0
        assert data.error_message == ""

    def test_from_log(self):
        log = ExecutionLog(
            log_id="log1",
            task_id="t1",
            task_name="任务A",
            task_icon="work",
            trigger_source=TriggerSource.TIMER,
            status=ExecutionStatus.FAILED,
            duration_ms=15000,
            error_message="失败原因",
            step_executions=[
                StepExecution(step_id="s1", step_name="A", step_type="click"),
                StepExecution(step_id="s2", step_name="B", step_type="delay"),
            ],
        )
        data = LogCardData.from_log(log)
        assert data.log_id == "log1"
        assert data.task_name == "任务A"
        assert data.task_icon == "work"
        assert data.status == "failed"
        assert data.trigger_source == "timer"
        assert data.duration_ms == 15000
        assert data.step_count == 2
        assert data.error_message == "失败原因"


class TestLogCard:
    """LogCard 组件"""

    def test_create_basic(self):
        data = LogCardData(
            log_id="log1",
            task_id="t1",
            task_name="测试任务",
        )
        card = LogCard(data)
        assert card.card_data.log_id == "log1"
        assert card.card_data.task_name == "测试任务"

    def test_create_with_started_at(self):
        data = LogCardData(
            log_id="log1",
            task_id="t1",
            task_name="测试",
            started_at=datetime.now() - timedelta(hours=1),
        )
        card = LogCard(data)
        assert card.card_data.started_at is not None

    def test_create_failed_status(self):
        data = LogCardData(
            log_id="log1",
            task_id="t1",
            task_name="测试",
            status="failed",
            error_message="出错了",
        )
        card = LogCard(data)
        assert card.card_data.status == "failed"

    def test_on_click_callback_called(self):
        """点击卡片触发 on_click 回调"""
        clicked = []

        def on_click(log_id):
            clicked.append(log_id)

        data = LogCardData(log_id="log1", task_id="t1", task_name="测试")
        card = LogCard(data, on_click=on_click)
        card._handle_card_click(_FakeEvent())
        assert clicked == ["log1"]

    def test_on_delete_callback_called_no_page(self):
        """无 page 时删除直接执行"""
        deleted = []

        def on_delete(log_id):
            deleted.append(log_id)

        data = LogCardData(log_id="log1", task_id="t1", task_name="测试")
        card = LogCard(data, on_delete=on_delete)
        card._handle_delete_click(_FakeEvent())
        assert deleted == ["log1"]

    def test_on_delete_no_callback(self):
        """无回调时不报错"""
        data = LogCardData(log_id="log1", task_id="t1", task_name="测试")
        card = LogCard(data)
        # 应该不抛异常
        card._handle_delete_click(_FakeEvent())

    def test_on_click_no_callback(self):
        """无回调时不报错"""
        data = LogCardData(log_id="log1", task_id="t1", task_name="测试")
        card = LogCard(data)
        # 应该不抛异常
        card._handle_card_click(_FakeEvent())
