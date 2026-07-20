"""logs_view 视图测试（M5）"""
from datetime import datetime, timedelta

import flet as ft
import pytest

from models.log import ExecutionLog, LogFilter
from services.log_service import LogService, _default_mock_logs
from services.stats_service import ExecutionStatus, TriggerSource
from views.logs_view import LogsView


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


class _FakeControl:
    """简易 control mock（用于 ControlEvent）"""

    def __init__(self, value=None, selected=None):
        self.value = value
        self.selected = selected or []


class _FakeEvent:
    """简易 ControlEvent mock"""

    def __init__(self, value=None, selected=None, page=None):
        self.control = _FakeControl(value=value, selected=selected)
        self.page = page
        self.stop_propagation = False
        self.data = None


class TestLogsView:
    """LogsView 视图"""

    def test_create_default(self):
        view = LogsView(_FakePage())
        assert view is not None
        assert view._service is not None
        assert view._filter.keyword == ""

    def test_initial_list_has_logs(self):
        view = LogsView(_FakePage())
        # mock 数据有 6 条日志
        assert len(view._list_container.controls) > 0

    def test_section_count_displays(self):
        view = LogsView(_FakePage())
        # section_count 应显示 "共 N 项"
        assert "共" in view._section_count.value
        assert "项" in view._section_count.value

    def test_search_filter(self):
        view = LogsView(_FakePage())
        # 触发搜索事件
        view._handle_search_change(_FakeEvent(value="早晨"))
        # 列表中应只有"早晨例行程序"相关日志
        # mock 数据中 t1（早晨例行程序）有 3 条日志
        assert len(view._list_container.controls) > 0

    def test_search_no_match(self):
        view = LogsView(_FakePage())
        view._handle_search_change(_FakeEvent(value="不存在的关键字xxx"))
        # 应显示空状态
        # 空状态是一个 Container with expand=True
        assert len(view._list_container.controls) == 1

    def test_status_filter(self):
        view = LogsView(_FakePage())
        view._handle_status_change(_FakeEvent(value="failed"))
        # mock 中只有 log2 是 FAILED
        # 但分组模式下，每个分组有 header + cards
        all_controls = view._list_container.controls
        # 不为空
        assert len(all_controls) > 0

    def test_status_filter_clear(self):
        view = LogsView(_FakePage())
        # 设置过滤
        view._handle_status_change(_FakeEvent(value="failed"))
        # 清除过滤
        view._handle_status_change(_FakeEvent(value=""))
        assert view._filter.status is None

    def test_trigger_filter(self):
        view = LogsView(_FakePage())
        view._handle_trigger_change(_FakeEvent(value="manual"))
        assert view._filter.trigger_source == TriggerSource.MANUAL

    def test_trigger_filter_clear(self):
        view = LogsView(_FakePage())
        view._handle_trigger_change(_FakeEvent(value="manual"))
        view._handle_trigger_change(_FakeEvent(value=""))
        assert view._filter.trigger_source is None

    def test_time_range_filter_1d(self):
        view = LogsView(_FakePage())
        view._handle_time_range_change(_FakeEvent(value="1d"))
        assert view._filter.time_range == "1d"

    def test_time_range_filter_7d(self):
        view = LogsView(_FakePage())
        view._handle_time_range_change(_FakeEvent(value="7d"))
        assert view._filter.time_range == "7d"

    def test_time_range_filter_all(self):
        view = LogsView(_FakePage())
        view._handle_time_range_change(_FakeEvent(value="all"))
        assert view._filter.time_range == "all"

    def test_task_filter(self):
        view = LogsView(_FakePage())
        view._handle_task_change(_FakeEvent(value="t1"))
        assert view._filter.task_id == "t1"

    def test_task_filter_clear(self):
        view = LogsView(_FakePage())
        view._handle_task_change(_FakeEvent(value="t1"))
        view._handle_task_change(_FakeEvent(value=""))
        assert view._filter.task_id is None

    def test_group_mode_change_to_flat(self):
        view = LogsView(_FakePage())
        # 默认是 date 模式
        assert view._group_mode == "date"
        # 切换到 flat
        view._handle_group_mode_change(_FakeEvent(selected=["flat"]))
        assert view._group_mode == "flat"

    def test_group_mode_change_to_date(self):
        view = LogsView(_FakePage())
        view._handle_group_mode_change(_FakeEvent(selected=["flat"]))
        view._handle_group_mode_change(_FakeEvent(selected=["date"]))
        assert view._group_mode == "date"

    def test_card_click_navigates_to_detail(self):
        page = _FakePage()
        view = LogsView(page)
        view._handle_card_click("log1")
        assert page._last_route == "/logs/log1"

    def test_card_click_with_callback(self):
        called = []

        def on_nav(log_id):
            called.append(log_id)

        view = LogsView(_FakePage(), on_navigate_detail=on_nav)
        view._handle_card_click("log1")
        assert called == ["log1"]

    def test_delete_removes_log(self):
        view = LogsView(_FakePage())
        initial_count = view._service.count()
        view._handle_delete("log1")
        assert view._service.count() == initial_count - 1

    def test_back_navigates_to_tasks(self):
        page = _FakePage()
        view = LogsView(page)
        view._handle_back(_FakeEvent())
        assert page._last_route == "/tasks"

    def test_inject_service(self):
        """可注入自定义 service"""
        custom_service = LogService(logs=[])
        view = LogsView(_FakePage(), service=custom_service)
        # 空服务应显示空状态
        assert len(view._list_container.controls) == 1
        assert view._service is custom_service
