"""step_editor_view 测试"""
from dataclasses import dataclass, field
from typing import List

import flet as ft

from models.step import StepStatus, StepType
from views.components.step_card import StepCardData
from views.step_editor_view import (
    StepEditorDrawer,
    StepEditorView,
    _default_mock_steps,
)


# ---- fake page（同 test_notifier）----


@dataclass
class _FakeOverlay:
    items: List[ft.Control] = field(default_factory=list)

    def append(self, ctrl: ft.Control) -> None:
        self.items.append(ctrl)


@dataclass
class _FakePage:
    overlay: _FakeOverlay = field(default_factory=_FakeOverlay)

    def update(self) -> None:
        pass

    def go(self, route: str) -> None:
        pass


# ---- mock 数据 ----


class TestMockData:
    """Q23 决策：mock 5 条示例步骤"""

    def test_returns_5_steps(self):
        steps = _default_mock_steps()
        assert len(steps) == 5

    def test_covers_all_three_statuses(self):
        """覆盖 AVAILABLE/LIMITED/NOT_IMPLEMENTED 三种状态"""
        steps = _default_mock_steps()
        statuses = set()
        for s in steps:
            from models.step import get_step_type_meta
            statuses.add(get_step_type_meta(s.step_type).status)
        assert StepStatus.AVAILABLE in statuses
        assert StepStatus.LIMITED in statuses
        assert StepStatus.NOT_IMPLEMENTED in statuses

    def test_not_implemented_marked_as_placeholder(self):
        """NOT_IMPLEMENTED 步骤标记为 is_placeholder"""
        steps = _default_mock_steps()
        bluetooth = next(s for s in steps if s.step_type == StepType.BLUETOOTH)
        assert bluetooth.is_placeholder is True

    def test_step_ids_unique(self):
        steps = _default_mock_steps()
        ids = [s.step_id for s in steps]
        assert len(ids) == len(set(ids))

    def test_step_orders_sequential(self):
        """步骤序号从 1 开始连续"""
        steps = _default_mock_steps()
        orders = [s.step_order for s in steps]
        assert orders == [1, 2, 3, 4, 5]


# ---- StepEditorDrawer ----


class TestStepEditorDrawer:
    """抽屉组件（Q21 决策）"""

    def test_can_be_constructed(self):
        drawer = StepEditorDrawer()
        assert isinstance(drawer, ft.Container)

    def test_start_add_resets_state(self):
        """start_add 重置编辑状态"""
        drawer = StepEditorDrawer()
        drawer.start_add()
        # 标题应为"添加步骤"
        # 保存按钮应禁用（未选类型）
        assert drawer._save_btn.disabled is True

    def test_start_edit_loads_existing_params(self):
        """start_edit 加载已有步骤参数"""
        step = StepCardData(
            step_id="step_x",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="测试",
            params={"url": "https://test.com"},
        )
        drawer = StepEditorDrawer()
        drawer.start_edit(step)
        # ParamEditor 应已实例化
        assert drawer._param_editor is not None
        # 标题应包含步骤名
        assert "测试" in drawer._title.value
        # 保存按钮应可用
        assert drawer._save_btn.disabled is False

    def test_is_dirty_initially_false_after_start_add(self):
        drawer = StepEditorDrawer()
        drawer.start_add()
        assert drawer.is_dirty() is False

    def test_is_dirty_false_after_start_edit_without_changes(self):
        """start_edit 后未改动时 dirty 为 False"""
        step = StepCardData(
            step_id="step_x",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="测试",
            params={"url": "https://test.com"},
        )
        drawer = StepEditorDrawer()
        drawer.start_edit(step)
        # 未改动
        assert drawer.is_dirty() is False

    def test_save_callback_invoked_with_correct_data(self):
        """保存回调被正确调用"""
        called_with = []
        drawer = StepEditorDrawer(
            on_save=lambda step_id, step_type, params, errors: called_with.append(
                (step_id, step_type, params, errors)
            ),
        )
        # 编辑已有步骤
        step = StepCardData(
            step_id="step_x",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="测试",
            params={"url": "https://test.com"},
        )
        drawer.start_edit(step)
        # 模拟保存点击
        drawer._handle_save(None)  # type: ignore[arg-type]
        assert len(called_with) == 1
        step_id, step_type, params, errors = called_with[0]
        assert step_id == "step_x"
        assert step_type == StepType.OPEN_URL
        assert params["url"] == "https://test.com"
        assert errors == []

    def test_cancel_callback_invoked(self):
        """取消回调被调用"""
        called = []
        drawer = StepEditorDrawer(
            on_cancel=lambda: called.append(1),
        )
        drawer._handle_cancel(None)  # type: ignore[arg-type]
        assert len(called) == 1

    def test_handle_type_selected_creates_param_editor(self):
        """类型选中后创建 ParamEditor"""
        drawer = StepEditorDrawer()
        drawer.start_add()
        # 选中 OPEN_URL
        drawer._handle_type_selected(StepType.OPEN_URL, False)
        assert drawer._param_editor is not None
        assert drawer._selected_step_type == StepType.OPEN_URL
        # 保存按钮应启用
        assert drawer._save_btn.disabled is False

    def test_save_validation_failure_passes_errors(self):
        """校验失败时把 errors 传给 on_save"""
        called_with = []
        drawer = StepEditorDrawer(
            on_save=lambda step_id, step_type, params, errors: called_with.append(
                (step_id, step_type, params, errors)
            ),
        )
        # 添加新步骤但未填 url（必填）
        drawer.start_add()
        drawer._handle_type_selected(StepType.OPEN_URL, False)
        # 不修改 url，保持为空
        drawer._handle_save(None)  # type: ignore[arg-type]
        assert len(called_with) == 1
        _, _, _, errors = called_with[0]
        assert len(errors) > 0


# ---- StepEditorView（主视图）----


class TestStepEditorView:
    """主视图（M2-T2.7 首次可运行）"""

    def test_can_be_constructed_with_fake_page(self):
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        assert isinstance(view, ft.View)
        assert view.route == "/step_editor"

    def test_has_appbar_with_back_button(self):
        """顶部 AppBar 含返回按钮"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        # 找 AppBar
        main_col = view.controls[0]
        # main_col 是 Column，第一个孩子是 AppBar
        # 但是因为 Stack 嵌套，需要深入查找
        appbars = self._find_controls_by_type(view, ft.AppBar)
        assert len(appbars) >= 1

    def test_has_fab_button(self):
        """FAB 显示由 add_step_entry 设置控制（需求3/F1）

        - 默认 "appbar"：无 FAB
        - "fab"：有 FAB
        - "both"：有 FAB
        """
        from views.settings_view import _APP_SETTINGS, set_app_setting

        # 备份并清理当前 add_step_entry 设置
        original = _APP_SETTINGS.get("add_step_entry")
        try:
            # 1. 默认 appbar：无 FAB
            _APP_SETTINGS.pop("add_step_entry", None)
            page1 = _FakePage()
            view1 = StepEditorView(page1)  # type: ignore[arg-type]
            fabs1 = self._find_controls_by_type(view1, ft.FloatingActionButton)
            assert len(fabs1) == 0, "默认 add_step_entry=appbar 时不应有 FAB"

            # 2. fab：有 FAB
            set_app_setting("add_step_entry", "fab")
            page2 = _FakePage()
            view2 = StepEditorView(page2)  # type: ignore[arg-type]
            fabs2 = self._find_controls_by_type(view2, ft.FloatingActionButton)
            assert len(fabs2) >= 1, "add_step_entry=fab 时应有 FAB"

            # 3. both：有 FAB
            set_app_setting("add_step_entry", "both")
            page3 = _FakePage()
            view3 = StepEditorView(page3)  # type: ignore[arg-type]
            fabs3 = self._find_controls_by_type(view3, ft.FloatingActionButton)
            assert len(fabs3) >= 1, "add_step_entry=both 时应有 FAB"
        finally:
            # 还原设置，避免污染其他测试
            if original is None:
                _APP_SETTINGS.pop("add_step_entry", None)
            else:
                set_app_setting("add_step_entry", original)

    def test_has_appbar_add_button(self):
        """AppBar 右上角 + 按钮（Q22 决策：双入口）"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        # AppBar.actions 应含 IconButton(icon=ADD)
        appbars = self._find_controls_by_type(view, ft.AppBar)
        assert len(appbars) >= 1
        appbar = appbars[0]
        # actions 至少有一个 IconButton
        assert len(appbar.actions) >= 1

    def test_initial_steps_loaded_from_mock(self):
        """首跑加载 mock 5 条步骤"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        assert len(view._steps) == 5

    def test_initial_step_list_renders_step_cards(self):
        """初始 ListView 渲染了 StepCard 控件"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        cards = self._find_controls_by_type(view, ft.Container)
        # 应该能找到多个 Container（StepCard 是 Container 子类）
        assert len(cards) >= 5

    def test_drawer_initially_hidden(self):
        """编辑抽屉初始不可见"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        assert view._overlay.visible is False

    def test_handle_add_step_shows_drawer(self):
        """点击 + 按钮后显示抽屉"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        view._handle_add_step()
        assert view._overlay.visible is True

    def test_handle_edit_step_loads_into_drawer(self):
        """点击卡片编辑加载到抽屉"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        view._handle_edit_step(first_step_id)
        # 抽屉应显示，且抽屉中 ParamEditor 应已加载
        assert view._overlay.visible is True
        assert view._drawer._param_editor is not None

    def test_handle_delete_step_removes_from_list(self):
        """删除步骤从列表移除"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        original_count = len(view._steps)
        view._handle_delete_step(first_step_id)
        assert len(view._steps) == original_count - 1

    def test_handle_delete_step_renumbers_remaining(self):
        """删除后剩余步骤重新编号"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        view._handle_delete_step(first_step_id)
        # 剩余步骤的 step_order 应为 1, 2, 3, 4
        orders = [s.step_order for s in view._steps]
        assert orders == [1, 2, 3, 4]

    def test_handle_save_new_step_appends_to_list(self):
        """保存新步骤追加到列表"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        original_count = len(view._steps)
        view._handle_save_step(
            step_id=None,
            step_type=StepType.DELAY,
            params={"duration": 10},
            errors=[],
        )
        assert len(view._steps) == original_count + 1
        # 新步骤的 type 应为 DELAY
        assert view._steps[-1].step_type == StepType.DELAY

    def test_handle_save_existing_step_updates(self):
        """保存已有步骤更新现有项"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        view._handle_save_step(
            step_id=first_step_id,
            step_type=StepType.DELAY,
            params={"duration": 999},
            errors=[],
        )
        # 第一项应被更新
        assert view._steps[0].step_type == StepType.DELAY
        assert view._steps[0].params["duration"] == 999

    def test_handle_toggle_step_changes_enabled(self):
        """启用/禁用切换"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        original_enabled = view._steps[0].enabled
        view._handle_toggle_step(first_step_id, not original_enabled)
        assert view._steps[0].enabled is (not original_enabled)

    def test_handle_save_with_validation_errors_does_not_modify_list(self):
        """校验失败时不修改步骤列表"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        original_count = len(view._steps)
        view._handle_save_step(
            step_id=None,
            step_type=StepType.OPEN_URL,
            params={"url": ""},  # 必填项为空
            errors=["URL 地址 是必填项"],
        )
        assert len(view._steps) == original_count

    # ---- 辅助方法：递归查找控件 ----

    @staticmethod
    def _find_controls_by_type(root, cls):
        """递归查找指定类型的所有控件"""
        found = []
        visited = set()

        def _walk(ctrl):
            cid = id(ctrl)
            if cid in visited:
                return
            visited.add(cid)
            if isinstance(ctrl, cls):
                found.append(ctrl)
            # 遍历子控件
            for attr in ["controls", "actions", "content"]:
                children = getattr(ctrl, attr, None)
                if children is None:
                    continue
                if isinstance(children, list):
                    for c in children:
                        _walk(c)
                elif isinstance(children, ft.Control):
                    _walk(children)

        _walk(root)
        return found


# ---- Q20 未保存离开对话框 ----


class TestQ20UnsavedDialog:
    """Q20 决策：未保存离开提示对话框"""

    def test_close_drawer_with_dirty_shows_dialog(self):
        """抽屉有改动时关闭会弹保存对话框"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        # 先编辑一个步骤（会触发 dirty 后续修改）
        first_step_id = view._steps[0].step_id
        view._handle_edit_step(first_step_id)
        # 修改参数使 dirty=True
        view._drawer._param_editor._dirty = True
        # 尝试关闭抽屉
        view._handle_close_drawer()
        # 应在 page.overlay 中找到 AlertDialog
        dialogs = [c for c in page.overlay.items if isinstance(c, ft.AlertDialog)]
        assert len(dialogs) >= 1

    def test_close_drawer_without_dirty_closes_immediately(self):
        """无改动时直接关闭抽屉"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        view._handle_add_step()  # 显示抽屉
        # 抽屉 dirty=False（未做任何编辑）
        view._handle_close_drawer()
        # 抽屉应已隐藏
        assert view._overlay.visible is False

    def test_dialog_has_three_choices(self):
        """对话框应有 3 个选项：保存并退出 / 继续编辑 / 不保存退出"""
        page = _FakePage()
        view = StepEditorView(page)  # type: ignore[arg-type]
        first_step_id = view._steps[0].step_id
        view._handle_edit_step(first_step_id)
        view._drawer._param_editor._dirty = True
        view._handle_close_drawer()
        dialogs = [c for c in page.overlay.items if isinstance(c, ft.AlertDialog)]
        assert len(dialogs) >= 1
        # 应有 3 个 action 按钮
        assert len(dialogs[-1].actions) == 3
