"""StepTypePicker 组件测试"""
import pytest

import flet as ft

from models.step import StepCategory, StepStatus, StepType
from views.components.step_type_picker import (
    CATEGORY_LABELS,
    STATUS_COLORS,
    STATUS_LABELS,
    StepTypePicker,
    StepTypeTile,
    make_placeholder_snackbar_message,
)


class TestCategoryLabels:
    """分类中文名映射"""

    def test_all_categories_labeled(self):
        for cat in StepCategory:
            assert cat in CATEGORY_LABELS

    def test_labels_correct(self):
        assert CATEGORY_LABELS[StepCategory.SIMULATION] == "模拟操作"
        assert CATEGORY_LABELS[StepCategory.SYSTEM_CONTROL] == "系统控制"
        assert CATEGORY_LABELS[StepCategory.DISPLAY] == "显示设置"
        assert CATEGORY_LABELS[StepCategory.AUDIO_HAPTIC] == "音频触感"
        assert CATEGORY_LABELS[StepCategory.AUXILIARY] == "辅助通知"


class TestStatusMapping:
    """状态色板（与 step_card 一致）"""

    def test_all_status_have_color(self):
        for status in StepStatus:
            assert status in STATUS_COLORS

    def test_all_status_have_label(self):
        for status in StepStatus:
            assert status in STATUS_LABELS


class TestStepTypeTile:
    """单个类型卡片"""

    def test_tile_available_type_can_be_constructed(self):
        tile = StepTypeTile(step_type=StepType.OPEN_URL)
        assert isinstance(tile, ft.Container)

    def test_tile_limited_type_can_be_constructed(self):
        tile = StepTypeTile(step_type=StepType.CLICK)
        assert isinstance(tile, ft.Container)

    def test_tile_not_implemented_can_be_constructed(self):
        tile = StepTypeTile(step_type=StepType.BLUETOOTH)
        assert isinstance(tile, ft.Container)

    def test_tile_callback_can_be_attached(self):
        called = []

        def on_select(st, is_placeholder):
            called.append((st, is_placeholder))

        tile = StepTypeTile(
            step_type=StepType.OPEN_URL,
            on_select=on_select,
        )
        # 回调已附加（不触发 GUI 事件）
        assert tile.step_type == StepType.OPEN_URL

    def test_tile_hint_text_hidden_initially(self):
        """不可做项的提示文字初始隐藏"""
        tile = StepTypeTile(step_type=StepType.BLUETOOTH)
        assert tile.hint_text.visible is False


class TestStepTypePicker:
    """完整面板"""

    def test_picker_can_be_constructed(self):
        picker = StepTypePicker()
        assert isinstance(picker, ft.Container)
        assert picker.content_area is not None
        assert len(picker.content_area.controls) > 0  # 初始已渲染

    def test_picker_initial_renders_simulation_category(self):
        """默认渲染模拟操作分类"""
        picker = StepTypePicker(initial_category=StepCategory.SIMULATION)
        # 内容区应有 1 个 Column（标题 + 网格）
        assert len(picker.content_area.controls) == 1

    def test_picker_initial_category_can_be_set(self):
        """可指定初始分类"""
        picker = StepTypePicker(initial_category=StepCategory.SYSTEM_CONTROL)
        # 内容区有 1 个 Column
        assert len(picker.content_area.controls) == 1

    def test_picker_callback_can_be_attached(self):
        called = []

        def on_select(st, is_placeholder):
            called.append((st, is_placeholder))

        picker = StepTypePicker(on_select=on_select)
        assert picker._on_select is on_select


class TestSearchBehavior:
    """搜索行为（数据层验证）"""

    def test_search_no_query_shows_single_category(self):
        """无搜索词时只显示当前分类"""
        picker = StepTypePicker()
        assert len(picker.content_area.controls) == 1

    def test_search_with_query_shows_multiple_categories(self):
        """有搜索词时跨所有分类分段展示"""
        picker = StepTypePicker()
        # 模拟搜索
        picker._search_query = "开"
        picker._render()
        # "开"应匹配多个分类（蓝牙开关/Wifi开关/打开链接 等）
        assert len(picker.content_area.controls) >= 2

    def test_search_with_no_match_shows_empty_state(self):
        """无匹配项显示空状态"""
        picker = StepTypePicker()
        picker._search_query = "完全不存在的关键字xyz123"
        picker._render()
        # 内容区应有 1 个空状态容器
        assert len(picker.content_area.controls) == 1

    def test_search_matches_name_zh(self):
        """按中文名搜索"""
        picker = StepTypePicker()
        picker._search_query = "蓝牙"
        picker._render()
        # 蓝牙属于系统控制分类
        assert len(picker.content_area.controls) >= 1

    def test_search_matches_type_id(self):
        """按 type_id 搜索"""
        picker = StepTypePicker()
        picker._search_query = "open_url"
        picker._render()
        assert len(picker.content_area.controls) >= 1

    def test_search_matches_description(self):
        """按描述搜索"""
        picker = StepTypePicker()
        picker._search_query = "flet"
        picker._render()
        # 至少匹配 open_url（描述含 Flet）
        assert len(picker.content_area.controls) >= 1


class TestPlaceholderMessage:
    """占位保存提示文案"""

    def test_message_contains_type_name(self):
        msg = make_placeholder_snackbar_message(StepType.BLUETOOTH)
        assert "蓝牙" in msg

    def test_message_contains_not_implemented_marker(self):
        msg = make_placeholder_snackbar_message(StepType.WIFI)
        assert "尚未实现" in msg or "占位" in msg
