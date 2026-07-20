"""Notifier / SnackBar 通知组件测试"""
from dataclasses import dataclass, field
from typing import List

import flet as ft

from views.components.notifier import (
    DEFAULT_DURATION_MS,
    LEVEL_COLORS,
    NotificationLevel,
    Notifier,
    build_snackbar,
    error_snackbar,
    placeholder_saved_snackbar,
    step_copied_snackbar,
    step_deleted_snackbar,
    step_moved_snackbar,
    step_saved_snackbar,
)


# ---- 测试用 fake page（避开真 Page 依赖） ----


@dataclass
class _FakeOverlay:
    """模拟 page.overlay 列表"""

    items: List[ft.Control] = field(default_factory=list)

    def append(self, control: ft.Control) -> None:
        self.items.append(control)


@dataclass
class _FakePage:
    """最小化的 Page 替身：仅暴露 overlay + update"""

    overlay: _FakeOverlay = field(default_factory=_FakeOverlay)

    def update(self) -> None:  # 与 Notifier.show 调用兼容
        pass


# ---- build_snackbar 纯函数测试 ----


class TestBuildSnackbar:
    """build_snackbar 返回正确结构"""

    def test_returns_snackbar_instance(self):
        sb = build_snackbar("hello")
        assert isinstance(sb, ft.SnackBar)

    def test_message_set_in_content(self):
        sb = build_snackbar("hello")
        # content 是 Text 控件
        assert isinstance(sb.content, ft.Text)
        assert sb.content.value == "hello"

    def test_default_level_is_info(self):
        sb = build_snackbar("x")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.INFO]

    def test_each_level_sets_correct_color(self):
        for level in NotificationLevel:
            sb = build_snackbar("x", level=level)
            assert sb.bgcolor == LEVEL_COLORS[level]

    def test_custom_duration_applied(self):
        sb = build_snackbar("x", duration_ms=5000)
        # duration 是 int 毫秒
        assert sb.duration == 5000

    def test_default_duration_used_when_not_specified(self):
        sb = build_snackbar("x")
        assert sb.duration == DEFAULT_DURATION_MS

    def test_action_text_passed_through(self):
        sb = build_snackbar("x", action_text="撤销")
        assert sb.action == "撤销"

    def test_no_action_by_default(self):
        sb = build_snackbar("x")
        assert sb.action is None

    def test_content_text_color_is_white(self):
        sb = build_snackbar("x")
        assert sb.content.color == "white"


# ---- 预设文案工厂测试 ----


class TestPresetFactories:
    """各业务场景预设 SnackBar"""

    def test_placeholder_saved_uses_placeholder_level(self):
        sb = placeholder_saved_snackbar("蓝牙开关")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.PLACEHOLDER]
        assert "蓝牙开关" in sb.content.value
        assert "尚未实现" in sb.content.value or "占位" in sb.content.value

    def test_step_saved_uses_success_level(self):
        sb = step_saved_snackbar("点击")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.SUCCESS]
        assert "点击" in sb.content.value
        assert "已保存" in sb.content.value

    def test_step_deleted_uses_info_level(self):
        sb = step_deleted_snackbar("点击")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.INFO]
        assert "点击" in sb.content.value
        assert "已删除" in sb.content.value

    def test_step_moved_includes_new_position(self):
        sb = step_moved_snackbar("点击", 3)
        assert "3" in sb.content.value
        assert "移动" in sb.content.value

    def test_step_copied_uses_success_level(self):
        sb = step_copied_snackbar("点击")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.SUCCESS]
        assert "复制" in sb.content.value

    def test_error_uses_error_level(self):
        sb = error_snackbar("网络失败")
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.ERROR]
        assert "网络失败" in sb.content.value

    def test_error_has_longer_duration_than_default(self):
        sb_default = build_snackbar("x")
        sb_error = error_snackbar("x")
        assert sb_error.duration > sb_default.duration


# ---- Notifier 类测试 ----


class TestNotifier:
    """Notifier 高层接口"""

    def test_can_be_constructed_without_page(self):
        n = Notifier()
        assert n.page is None

    def test_can_be_constructed_with_page(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        assert n.page is page

    def test_attach_sets_page(self):
        page = _FakePage()
        n = Notifier()
        returned = n.attach(page)  # type: ignore[arg-type]
        assert returned is n
        assert n.page is page

    def test_show_without_page_silently_no_op(self):
        """无 page 时静默失败（不抛异常）"""
        n = Notifier()
        sb = build_snackbar("x")
        # 不应抛异常
        n.show(sb)

    def test_show_appends_snackbar_to_overlay(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        sb = build_snackbar("x")
        n.show(sb)
        assert sb in page.overlay.items
        assert sb.open is True

    def test_placeholder_saved_high_level_method_works(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.placeholder_saved("蓝牙开关")
        assert len(page.overlay.items) == 1
        sb = page.overlay.items[0]
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.PLACEHOLDER]

    def test_step_saved_high_level_method_works(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.step_saved("点击")
        sb = page.overlay.items[0]
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.SUCCESS]

    def test_step_deleted_high_level_method_works(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.step_deleted("点击")
        sb = page.overlay.items[0]
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.INFO]

    def test_step_moved_includes_position(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.step_moved("点击", 5)
        sb = page.overlay.items[0]
        assert "5" in sb.content.value

    def test_error_method_uses_error_level(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.error("网络错误")
        sb = page.overlay.items[0]
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.ERROR]

    def test_warning_method_uses_warning_level(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.warning("受限")
        sb = page.overlay.items[0]
        assert sb.bgcolor == LEVEL_COLORS[NotificationLevel.WARNING]

    def test_multiple_notifications_all_added(self):
        page = _FakePage()
        n = Notifier(page=page)  # type: ignore[arg-type]
        n.info("a")
        n.info("b")
        n.info("c")
        assert len(page.overlay.items) == 3


# ---- LEVEL_COLORS 完整性 ----


class TestLevelColors:
    """级别色板覆盖所有 NotificationLevel"""

    def test_all_levels_have_color(self):
        for level in NotificationLevel:
            assert level in LEVEL_COLORS

    def test_placeholder_color_differs_from_success(self):
        """占位色与成功色不同（避免视觉混淆）"""
        assert LEVEL_COLORS[NotificationLevel.PLACEHOLDER] != LEVEL_COLORS[NotificationLevel.SUCCESS]
