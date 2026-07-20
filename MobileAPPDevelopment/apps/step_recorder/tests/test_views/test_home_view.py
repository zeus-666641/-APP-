"""home_view 主视图测试"""
import pytest

import flet as ft

from models.task import Task, TaskCategory
from views.home_view import HomeView, _default_mock_tasks, _default_mock_relations


class _FakePage:
    """简易 page mock"""

    def __init__(self):
        self.views = []
        self.snackbar = None
        self.theme_mode = "light"

    def go(self, route):
        self._last_route = route

    def update(self):
        pass


class TestMockData:
    """mock 数据完整性"""

    def test_mock_tasks_not_empty(self):
        tasks = _default_mock_tasks()
        assert len(tasks) > 0

    def test_mock_relations_not_empty(self):
        relations = _default_mock_relations()
        assert len(relations) > 0

    def test_mock_tasks_have_valid_ids(self):
        tasks = _default_mock_tasks()
        ids = [t.id for t in tasks]
        assert len(ids) == len(set(ids)), "任务 ID 不能重复"

    def test_mock_relations_reference_valid_tasks(self):
        tasks = _default_mock_tasks()
        task_ids = {t.id for t in tasks}
        relations = _default_mock_relations()
        for rel in relations:
            assert rel.parent_id in task_ids
            assert rel.child_id in task_ids

    def test_mock_tasks_cover_categories(self):
        tasks = _default_mock_tasks()
        categories = {t.category for t in tasks}
        # 至少 3 个不同分类
        assert len(categories) >= 3

    def test_mock_tasks_cover_disabled_state(self):
        tasks = _default_mock_tasks()
        disabled = [t for t in tasks if not t.enabled]
        assert len(disabled) >= 1, "应有至少 1 个禁用任务"


class TestHomeViewConstruction:
    """HomeView 构造测试"""

    def test_can_construct_with_fake_page(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        assert isinstance(view, ft.View)
        assert view.route == "/tasks"

    def test_has_appbar(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        appbars = [c for c in view.controls if isinstance(c, ft.AppBar)]
        assert len(appbars) == 1

    def test_has_navigation_bar(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        nav_bars = [c for c in view.controls if isinstance(c, ft.NavigationBar)]
        assert len(nav_bars) == 1

    def test_nav_bar_has_three_tabs(self):
        """Q50: 3 tab（任务/统计/日志）"""
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        nav_bar = next(c for c in view.controls if isinstance(c, ft.NavigationBar))
        assert len(nav_bar.destinations) == 3

    def test_default_tab_is_tasks(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        nav_bar = next(c for c in view.controls if isinstance(c, ft.NavigationBar))
        assert nav_bar.selected_index == 0  # tasks

    def test_initial_tab_can_be_set(self):
        page = _FakePage()
        view = HomeView(page, initial_tab="logs")  # type: ignore[arg-type]
        nav_bar = next(c for c in view.controls if isinstance(c, ft.NavigationBar))
        assert nav_bar.selected_index == 2  # logs

    def test_has_add_task_button(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        appbar = next(c for c in view.controls if isinstance(c, ft.AppBar))
        # Q50：AppBar actions 包含添加任务按钮
        assert len(appbar.actions) >= 1

    def test_appbar_has_settings_button(self):
        """Q50 需求12：AppBar 左侧有设置按钮"""
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        appbar = next(c for c in view.controls if isinstance(c, ft.AppBar))
        assert appbar.leading is not None  # 设置 IconButton 在 leading


class TestTabConversion:
    """tab key 与 index 转换（Q50: 3 tab）"""

    def test_tab_to_index_mapping(self):
        assert HomeView._tab_to_index("tasks") == 0
        assert HomeView._tab_to_index("stats") == 1
        assert HomeView._tab_to_index("logs") == 2

    def test_index_to_tab_mapping(self):
        assert HomeView._index_to_tab(0) == "tasks"
        assert HomeView._index_to_tab(1) == "stats"
        assert HomeView._index_to_tab(2) == "logs"

    def test_invalid_index_falls_back_to_tasks(self):
        assert HomeView._index_to_tab(99) == "tasks"
        assert HomeView._index_to_tab(-1) == "tasks"


class TestTabContent:
    """tab 内容渲染"""

    def test_tasks_tab_renders_task_tree(self):
        page = _FakePage()
        view = HomeView(page, initial_tab="tasks")  # type: ignore[arg-type]
        # SafeArea 内应有 TaskTree
        safe_area = next(c for c in view.controls if isinstance(c, ft.SafeArea))
        assert safe_area.content is not None

    def test_tasks_tab_displays_section_title(self):
        """Q50：任务 tab 显示'全部任务'标题"""
        page = _FakePage()
        view = HomeView(page, initial_tab="tasks")  # type: ignore[arg-type]
        safe_area = next(c for c in view.controls if isinstance(c, ft.SafeArea))
        content_text = self._extract_all_text(safe_area)
        assert "全部任务" in content_text

    def _extract_all_text(self, control) -> str:
        """递归提取所有 Text 内容"""
        texts = []

        def extract(ctrl):
            if isinstance(ctrl, ft.Text):
                texts.append(ctrl.value or "")
            elif hasattr(ctrl, "content") and ctrl.content:
                extract(ctrl.content)
            elif hasattr(ctrl, "controls") and ctrl.controls:
                for c in ctrl.controls:
                    extract(c)

        extract(control)
        return " ".join(texts)


class TestCallbacks:
    """回调挂载测试"""

    def test_toggle_task_callback_does_not_raise(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        # 切换第一个任务的启用状态
        first_task = view._tasks[0]
        original = first_task.enabled
        view._handle_toggle_task(first_task.id, not original)
        assert first_task.enabled == (not original)

    def test_execute_task_callback_does_not_raise(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        view._handle_execute_task("t1")  # 不抛异常即可

    def test_click_task_callback_does_not_raise(self):
        page = _FakePage()
        view = HomeView(page)  # type: ignore[arg-type]
        view._handle_click_task("t1")  # 不抛异常即可
