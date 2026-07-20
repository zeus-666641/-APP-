"""task_edit_view 测试"""
import pytest

import flet as ft

from models.task import Task, TaskCategory
from views.task_edit_view import (
    TaskEditData,
    TaskEditDrawer,
    TaskEditView,
)


class _FakePage:
    def __init__(self):
        self.views = []
        self.snackbar = None

    def go(self, route):
        self._last_route = route

    def update(self):
        pass


class TestTaskEditData:
    """任务编辑数据模型"""

    def test_default_values(self):
        data = TaskEditData()
        assert data.task_id is None
        assert data.name == ""
        assert data.icon == "play_arrow"
        assert data.category == TaskCategory.DEFAULT
        assert data.enabled is True
        assert data.keep_screen_on is False

    def test_from_task(self):
        task = Task(
            id="t1",
            name="测试任务",
            description="描述",
            icon="star",
            category=TaskCategory.WORK,
            enabled=False,
            keep_screen_on=True,
        )
        data = TaskEditData.from_task(task)
        assert data.task_id == "t1"
        assert data.name == "测试任务"
        assert data.description == "描述"
        assert data.icon == "star"
        assert data.category == TaskCategory.WORK
        assert data.enabled is False
        assert data.keep_screen_on is True

    def test_to_task(self):
        data = TaskEditData(
            name="新任务",
            icon="home",
            category=TaskCategory.LIFE,
            enabled=False,
        )
        task = data.to_task("new_id")
        assert task.id == "new_id"
        assert task.name == "新任务"
        assert task.icon == "home"
        assert task.category == TaskCategory.LIFE
        assert task.enabled is False

    def test_is_valid_empty_name(self):
        data = TaskEditData(name="")
        assert data.is_valid() is False

    def test_is_valid_whitespace_name(self):
        data = TaskEditData(name="   ")
        assert data.is_valid() is False

    def test_is_valid_valid_name(self):
        data = TaskEditData(name="有效名称")
        assert data.is_valid() is True


class TestTaskEditDrawer:
    """任务编辑抽屉"""

    def test_can_construct_for_new_task(self):
        drawer = TaskEditDrawer(on_save=lambda d: None, on_cancel=lambda: None)
        assert isinstance(drawer, ft.Container)
        assert drawer.content is not None

    def test_can_construct_for_edit_mode(self):
        existing = TaskEditData(task_id="t1", name="已存在任务")
        drawer = TaskEditDrawer(
            on_save=lambda d: None,
            on_cancel=lambda: None,
            initial_data=existing,
        )
        assert isinstance(drawer, ft.Container)

    def test_save_callback_fires_on_valid_data(self):
        saved_data = []

        def on_save(data):
            saved_data.append(data)

        drawer = TaskEditDrawer(
            on_save=on_save,
            on_cancel=lambda: None,
            initial_data=TaskEditData(name="测试"),
        )
        # 模拟点击保存
        drawer._handle_save(_FakeEvent())
        assert len(saved_data) == 1
        assert saved_data[0].name == "测试"

    def test_save_callback_does_not_fire_on_invalid_data(self):
        saved_data = []

        def on_save(data):
            saved_data.append(data)

        drawer = TaskEditDrawer(
            on_save=on_save,
            on_cancel=lambda: None,
            initial_data=TaskEditData(name=""),
        )
        # 名称字段为空
        drawer._name_field.value = ""
        drawer._handle_save(_FakeEvent())
        assert len(saved_data) == 0

    def test_cancel_callback_fires(self):
        cancelled = []

        def on_cancel():
            cancelled.append(True)

        drawer = TaskEditDrawer(
            on_save=lambda d: None,
            on_cancel=on_cancel,
        )
        drawer._handle_cancel(_FakeEvent())
        assert len(cancelled) == 1

    def test_parent_options_are_populated(self):
        parent_options = [("t1", "父任务"), ("t2", "另一个父任务")]
        drawer = TaskEditDrawer(
            on_save=lambda d: None,
            on_cancel=lambda: None,
            parent_options=parent_options,
        )
        # 父任务 dropdown 应有 3 个选项：无 + 2 个父任务
        assert len(drawer._parent_dropdown.options) == 3

    def test_is_dirty_returns_false_initially(self):
        drawer = TaskEditDrawer(
            on_save=lambda d: None,
            on_cancel=lambda: None,
            initial_data=TaskEditData(name="测试"),
        )
        # 没有改动时
        assert drawer.is_dirty() is False


class _FakeEvent:
    """模拟 ControlEvent"""

    def __init__(self):
        self.control = None
        self.page = None

    def stop_propagation(self):
        pass


class TestTaskEditView:
    """任务编辑全屏视图"""

    def test_can_construct(self):
        page = _FakePage()
        view = TaskEditView(
            page=page,  # type: ignore[arg-type]
            on_save=lambda d: None,
            on_cancel=lambda: None,
        )
        assert isinstance(view, ft.View)
        assert view.route == "/task_edit"

    def test_has_appbar_with_back_button(self):
        page = _FakePage()
        view = TaskEditView(
            page=page,  # type: ignore[arg-type]
            on_save=lambda d: None,
            on_cancel=lambda: None,
        )
        appbar = view.controls[0]
        assert isinstance(appbar, ft.AppBar)
        assert appbar.leading is not None
