"""log_detail_view 视图测试（M5）"""
from datetime import datetime, timedelta

import flet as ft
import pytest

from models.log import ExecutionLog, StepExecution
from services.log_service import _default_mock_logs
from services.stats_service import ExecutionStatus, TriggerSource
from views.log_detail_view import LogDetailView


class _FakePage:
    """简易 page mock"""

    def __init__(self):
        self.views = []
        self._last_route = None
        self.overlay = []

    def go(self, route):
        self._last_route = route

    def update(self):
        pass


class _FakeEvent:
    """简易 ControlEvent mock"""

    def __init__(self, page=None):
        self.page = page
        self.stop_propagation = False
        self.data = None


class TestLogDetailView:
    """LogDetailView 视图"""

    def test_create_with_log(self):
        """传入 log 时正常创建"""
        logs = _default_mock_logs()
        view = LogDetailView(_FakePage(), logs[0].log_id, log=logs[0])
        assert view is not None
        assert view._log is not None
        assert view._log.log_id == logs[0].log_id

    def test_create_with_not_found_log_id(self):
        """log_id 不存在时显示占位"""
        view = LogDetailView(_FakePage(), "nonexistent")
        assert view._log is None
        # 应该有 AppBar 或者 SafeArea
        assert len(view.controls) > 0

    def test_inject_log(self):
        """注入完整 log 对象"""
        log = ExecutionLog(
            log_id="custom_log",
            task_id="t1",
            task_name="自定义任务",
            task_icon="work",
            trigger_source=TriggerSource.MANUAL,
            status=ExecutionStatus.SUCCESS,
            duration_ms=10000,
            step_executions=[
                StepExecution(
                    step_id="s1",
                    step_name="步骤1",
                    step_type="click",
                    icon="ads_click",
                    order=1,
                    status=ExecutionStatus.SUCCESS,
                    duration_ms=5000,
                ),
                StepExecution(
                    step_id="s2",
                    step_name="步骤2",
                    step_type="delay",
                    icon="schedule",
                    order=2,
                    status=ExecutionStatus.SUCCESS,
                    duration_ms=5000,
                ),
            ],
        )
        view = LogDetailView(_FakePage(), "custom_log", log=log)
        assert view._log is log

    def test_failed_log_displays_error(self):
        """失败日志显示错误信息"""
        log = ExecutionLog(
            log_id="failed_log",
            task_id="t1",
            task_name="失败任务",
            status=ExecutionStatus.FAILED,
            error_message="测试错误信息",
        )
        view = LogDetailView(_FakePage(), "failed_log", log=log)
        # 应该包含错误信息卡片
        # 提取所有 text
        all_text = _extract_all_text(view)
        assert "错误信息" in all_text
        assert "测试错误信息" in all_text

    def test_aborted_log_displays_error(self):
        """中止日志也显示错误信息"""
        log = ExecutionLog(
            log_id="aborted_log",
            task_id="t1",
            task_name="中止任务",
            status=ExecutionStatus.ABORTED,
            error_message="用户中止",
        )
        view = LogDetailView(_FakePage(), "aborted_log", log=log)
        all_text = _extract_all_text(view)
        assert "用户中止" in all_text

    def test_success_log_no_error_block(self):
        """成功日志不显示错误信息"""
        log = ExecutionLog(
            log_id="success_log",
            task_id="t1",
            task_name="成功任务",
            status=ExecutionStatus.SUCCESS,
        )
        view = LogDetailView(_FakePage(), "success_log", log=log)
        all_text = _extract_all_text(view)
        assert "错误信息" not in all_text

    def test_step_timeline_rendered(self):
        """步骤时间轴被渲染"""
        log = ExecutionLog(
            log_id="log_with_steps",
            task_id="t1",
            task_name="任务",
            step_executions=[
                StepExecution(
                    step_id="s1", step_name="步骤A", step_type="click",
                    icon="ads_click", order=1, duration_ms=1000,
                ),
                StepExecution(
                    step_id="s2", step_name="步骤B", step_type="delay",
                    icon="schedule", order=2, duration_ms=2000,
                ),
            ],
        )
        view = LogDetailView(_FakePage(), "log_with_steps", log=log)
        all_text = _extract_all_text(view)
        assert "步骤A" in all_text
        assert "步骤B" in all_text
        assert "步骤执行时间轴" in all_text

    def test_empty_steps(self):
        """无步骤执行记录时显示占位"""
        log = ExecutionLog(
            log_id="empty_log",
            task_id="t1",
            task_name="任务",
            step_executions=[],
        )
        view = LogDetailView(_FakePage(), "empty_log", log=log)
        all_text = _extract_all_text(view)
        assert "暂无步骤执行记录" in all_text

    def test_back_navigates_to_logs(self):
        page = _FakePage()
        log = _default_mock_logs()[0]
        view = LogDetailView(page, log.log_id, log=log)
        view._handle_back(_FakeEvent())
        assert page._last_route == "/logs"

    def test_delete_callback_called_when_no_page(self):
        """无 page 时直接调用 on_delete"""
        deleted = []

        def on_delete(log_id):
            deleted.append(log_id)

        log = _default_mock_logs()[0]
        view = LogDetailView(_FakePage(), log.log_id, log=log, on_delete=on_delete)
        view._handle_delete_click(_FakeEvent())
        assert deleted == [log.log_id]

    def test_delete_no_callback_no_error(self):
        """无回调时不报错"""
        log = _default_mock_logs()[0]
        view = LogDetailView(_FakePage(), log.log_id, log=log)
        view._handle_delete_click(_FakeEvent())

    def test_overview_shows_task_name(self):
        log = ExecutionLog(
            log_id="test",
            task_id="t1",
            task_name="任务名ABC",
        )
        view = LogDetailView(_FakePage(), "test", log=log)
        all_text = _extract_all_text(view)
        assert "任务名ABC" in all_text

    def test_overview_shows_step_count(self):
        log = ExecutionLog(
            log_id="test",
            task_id="t1",
            task_name="任务",
            step_executions=[
                StepExecution(step_id="s1", step_name="A", step_type="click", order=1),
                StepExecution(step_id="s2", step_name="B", step_type="click", order=2),
                StepExecution(step_id="s3", step_name="C", step_type="click", order=3),
            ],
        )
        view = LogDetailView(_FakePage(), "test", log=log)
        all_text = _extract_all_text(view)
        # 步骤数 = 3
        assert "3" in all_text

    def test_route_attribute(self):
        log = _default_mock_logs()[0]
        view = LogDetailView(_FakePage(), log.log_id, log=log)
        assert view.route == f"/logs/{log.log_id}"


# ---- 工具函数 ----


def _extract_all_text(control) -> str:
    """递归提取所有 Text 内容（含 Button.text）"""
    texts = []

    def extract(ctrl):
        if isinstance(ctrl, ft.Text):
            texts.append(ctrl.value or "")
        elif isinstance(ctrl, (ft.Button, ft.TextButton)):
            texts.append(ctrl.text or "")
            if hasattr(ctrl, "icon") and ctrl.icon:
                pass
        if hasattr(ctrl, "content") and ctrl.content:
            extract(ctrl.content)
        if hasattr(ctrl, "controls") and ctrl.controls:
            for c in ctrl.controls:
                extract(c)

    extract(control)
    return " ".join(texts)
