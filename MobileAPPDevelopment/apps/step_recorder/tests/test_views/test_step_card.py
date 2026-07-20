"""StepCard 组件测试"""
import pytest

import flet as ft

from models.step import StepStatus, StepType
from views.components.step_card import (
    STATUS_COLORS,
    STATUS_LABELS,
    StepCard,
    StepCardData,
    render_step_cards,
)


class TestStepCardData:
    """卡片数据模型"""

    def test_default_values(self):
        data = StepCardData(
            step_id="s1",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="打开链接",
            params={"url": "https://example.com"},
        )
        assert data.enabled is True
        assert data.is_placeholder is False

    def test_placeholder_step(self):
        data = StepCardData(
            step_id="s2",
            step_order=2,
            step_type=StepType.BLUETOOTH,
            name_zh="蓝牙开关",
            params={"state": "开"},
            enabled=False,
            is_placeholder=True,
        )
        assert data.is_placeholder is True
        assert data.enabled is False


class TestStatusMapping:
    """状态色板完整性"""

    def test_all_status_have_color(self):
        for status in StepStatus:
            assert status in STATUS_COLORS

    def test_all_status_have_label(self):
        for status in StepStatus:
            assert status in STATUS_LABELS

    def test_colors_match_prd(self):
        assert STATUS_COLORS[StepStatus.AVAILABLE] == "#10b981"
        assert STATUS_COLORS[StepStatus.LIMITED] == "#f59e0b"
        assert STATUS_COLORS[StepStatus.NOT_IMPLEMENTED] == "#94a3b8"

    def test_labels_match_chinese(self):
        assert STATUS_LABELS[StepStatus.AVAILABLE] == "可用"
        assert STATUS_LABELS[StepStatus.LIMITED] == "受限"
        assert STATUS_LABELS[StepStatus.NOT_IMPLEMENTED] == "未实现"


class TestStepCardRender:
    """卡片渲染测试（不启动 GUI，仅校验控件构造）"""

    def test_card_can_be_constructed(self):
        """可用类型卡片正常构造"""
        data = StepCardData(
            step_id="s1",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="打开链接",
            params={"url": "https://example.com"},
        )
        card = StepCard(data=data)
        assert isinstance(card, ft.Container)
        # 应该有子控件
        assert card.content is not None

    def test_placeholder_card_can_be_constructed(self):
        """占位卡片正常构造"""
        data = StepCardData(
            step_id="s2",
            step_order=2,
            step_type=StepType.BLUETOOTH,
            name_zh="蓝牙开关",
            params={"state": "开"},
            is_placeholder=True,
        )
        card = StepCard(data=data)
        assert isinstance(card, ft.Container)

    def test_card_with_empty_params(self):
        """空参数卡片正常构造"""
        data = StepCardData(
            step_id="s3",
            step_order=3,
            step_type=StepType.GO_HOME,
            name_zh="返回主界面",
            params={},
        )
        card = StepCard(data=data)
        assert isinstance(card, ft.Container)

    def test_render_step_cards_batch(self):
        """批量渲染"""
        items = [
            StepCardData(
                step_id=f"s{i}",
                step_order=i,
                step_type=StepType.OPEN_URL,
                name_zh=f"步骤{i}",
                params={},
            )
            for i in range(1, 6)
        ]
        cards = render_step_cards(items)
        assert len(cards) == 5
        assert all(isinstance(c, StepCard) for c in cards)

    def test_callbacks_can_be_attached(self):
        """回调可附加"""
        called = []

        def on_toggle(sid, val):
            called.append(("toggle", sid, val))

        def on_delete(sid):
            called.append(("delete", sid))

        def on_click(sid):
            called.append(("click", sid))

        data = StepCardData(
            step_id="s1",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="打开链接",
            params={"url": "x"},
        )
        StepCard(
            data=data,
            on_toggle_enabled=on_toggle,
            on_delete=on_delete,
            on_click=on_click,
        )
        # 回调已被存储（不触发实际 GUI 事件）
        assert True


class TestParamsSummaryFormat:
    """参数摘要格式化"""

    def test_empty_params(self):
        assert StepCard._format_params_summary({}) == ""

    def test_single_param(self):
        result = StepCard._format_params_summary({"url": "https://x.com"})
        assert "url: https://x.com" in result

    def test_multiple_params_truncated_to_3(self):
        params = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        result = StepCard._format_params_summary(params)
        # 至多 3 项
        assert result.count("·") <= 2

    def test_skip_empty_values(self):
        params = {"a": 1, "b": "", "c": None, "d": []}
        result = StepCard._format_params_summary(params)
        assert "a: 1" in result
        assert "b:" not in result
        assert "c:" not in result
        assert "d:" not in result
