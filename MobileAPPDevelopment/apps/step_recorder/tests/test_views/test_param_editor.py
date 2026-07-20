"""ParamEditor 组件测试"""
import pytest

import flet as ft

from models.step import (
    FieldType,
    ParamField,
    StepStatus,
    StepType,
    get_step_type_meta,
)
from views.components.param_editor import ParamEditor


class TestConstruction:
    """构造基本测试"""

    def test_can_be_constructed_with_step_type(self):
        editor = ParamEditor(step_type=StepType.OPEN_URL)
        assert isinstance(editor, ft.Container)

    def test_with_initial_params(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        assert editor._initial_params == {"url": "https://example.com"}

    def test_empty_step_type_has_no_fields_message(self):
        """无 fields 的步骤显示提示"""
        editor = ParamEditor(step_type=StepType.GO_HOME)
        # GO_HOME fields=()，渲染为空状态提示
        content_col = editor.content
        assert len(content_col.controls) >= 1

    def test_field_controls_populated_for_type_with_fields(self):
        editor = ParamEditor(step_type=StepType.OPEN_URL)
        # OPEN_URL 有 1 个字段：url
        assert "url" in editor.field_controls

    def test_multiple_fields_populated(self):
        editor = ParamEditor(step_type=StepType.CLICK)
        # CLICK 有 target/x/y 三个字段
        assert "target" in editor.field_controls
        assert "x" in editor.field_controls
        assert "y" in editor.field_controls


class TestGetValues:
    """读取值"""

    def test_string_field_initial_value_returned(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        values = editor.get_values()
        assert values["url"] == "https://example.com"

    def test_string_field_default_when_no_initial(self):
        editor = ParamEditor(step_type=StepType.OPEN_URL)
        values = editor.get_values()
        # OPEN_URL.url 默认是 None，但 TextField.value 转 str
        assert values["url"] == ""

    def test_int_field_initial_value(self):
        editor = ParamEditor(
            step_type=StepType.CLICK,
            initial_params={"x": 100, "y": 200, "target": "btn1"},
        )
        values = editor.get_values()
        assert values["x"] == 100
        assert values["y"] == 200
        assert values["target"] == "btn1"

    def test_bool_field_returns_bool(self):
        editor = ParamEditor(
            step_type=StepType.DIAL,
            initial_params={"phone": "13800138000", "auto_call": True},
        )
        values = editor.get_values()
        assert values["auto_call"] is True

    def test_int_range_field_returns_int(self):
        editor = ParamEditor(
            step_type=StepType.DELAY,
            initial_params={"duration": 5},
        )
        values = editor.get_values()
        assert values["duration"] == 5
        assert isinstance(values["duration"], int)

    def test_enum_field_initial_value(self):
        editor = ParamEditor(
            step_type=StepType.BLUETOOTH,
            initial_params={"state": "on"},
        )
        values = editor.get_values()
        assert values["state"] == "on"

    def test_enum_field_default_value_when_no_initial(self):
        editor = ParamEditor(step_type=StepType.BLUETOOTH)
        values = editor.get_values()
        # BLUETOOTH.state default = "off"
        assert values["state"] == "off"


class TestDirty:
    """is_dirty 检测（Q20 决策）"""

    def test_not_dirty_initially(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        assert editor.is_dirty() is False

    def test_dirty_after_change_callback_fires(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        # 模拟用户改动
        editor._dirty = True
        assert editor.is_dirty() is True

    def test_not_dirty_when_value_unchanged(self):
        """即使没有触发 callback，值与初始值相同时也算 clean"""
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        # 不触发任何 callback，但值仍等于初始值
        assert editor.is_dirty() is False

    def test_dirty_when_value_differs_from_initial(self):
        """不通过 callback，通过比较值也能检测 dirty"""
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        # 修改控件值但不动 _dirty
        editor.field_controls["url"].value = "https://changed.com"
        editor._dirty = False
        assert editor.is_dirty() is True

    def test_dirty_callback_invoked_on_change(self):
        """on_change 回调被调用"""
        called = []
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            on_change=lambda: called.append(1),
        )
        # 触发 on_change（手动）
        editor._on_change()
        assert len(called) == 1


class TestReset:
    """reset_to_defaults"""

    def test_string_field_reset_to_default(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        # 先脏
        editor.field_controls["url"].value = "https://changed.com"
        editor._dirty = True
        # 重置
        editor.reset_to_defaults()
        # OPEN_URL.url 默认是 None → ""
        assert editor.field_controls["url"].value == ""
        assert editor._dirty is False

    def test_bool_field_reset_to_default(self):
        editor = ParamEditor(
            step_type=StepType.DIAL,
            initial_params={"phone": "123", "auto_call": True},
        )
        editor.reset_to_defaults()
        # DIAL.auto_call default=False
        assert editor.field_controls["auto_call"].value is False

    def test_enum_field_reset_to_default(self):
        editor = ParamEditor(
            step_type=StepType.BLUETOOTH,
            initial_params={"state": "on"},
        )
        editor.reset_to_defaults()
        # BLUETOOTH.state default="off"
        assert editor.field_controls["state"].value == "off"


class TestValidate:
    """validate 返回错误列表"""

    def test_valid_form_returns_no_errors(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://example.com"},
        )
        errors = editor.validate()
        assert errors == []

    def test_required_string_empty_returns_error(self):
        editor = ParamEditor(step_type=StepType.OPEN_URL)
        # url 默认为空字符串，是必填项
        errors = editor.validate()
        assert len(errors) >= 1
        assert any("URL" in e or "url" in e for e in errors)

    def test_required_field_filled_passes(self):
        editor = ParamEditor(
            step_type=StepType.OPEN_URL,
            initial_params={"url": "https://x.com"},
        )
        errors = editor.validate()
        assert errors == []

    def test_int_below_min_returns_error(self):
        editor = ParamEditor(
            step_type=StepType.CLICK,
            initial_params={"x": -5, "y": 0, "target": "btn"},
        )
        # CLICK.x min_value=0，-5 不合法
        errors = editor.validate()
        assert any("X" in e or "小于" in e for e in errors)

    def test_int_at_min_no_error(self):
        editor = ParamEditor(
            step_type=StepType.CLICK,
            initial_params={"x": 0, "y": 0, "target": "btn"},
        )
        errors = editor.validate()
        assert errors == []


class TestQ18NotImplementedAllowsParams:
    """Q18 决策：NOT_IMPLEMENTED 类型也允许填参数"""

    def test_not_implemented_type_renders_form(self):
        editor = ParamEditor(step_type=StepType.BLUETOOTH)
        # BLUETOOTH 有 state 字段
        assert "state" in editor.field_controls

    def test_not_implemented_placeholder_message_when_no_fields(self):
        editor = ParamEditor(step_type=StepType.LOCK_SCREEN)
        # LOCK_SCREEN fields=()
        content = editor.content
        # 应有 1 个 Container（空状态提示）
        assert len(content.controls) == 1
        text_control = content.controls[0].content
        assert "尚未实现" in text_control.value or "无需参数" in text_control.value

    def test_placeholder_text_contains_marker(self):
        editor = ParamEditor(step_type=StepType.LOCK_SCREEN)
        text_control = editor.content.controls[0].content
        # Q18：NOT_IMPLEMENTED 应有"尚未实现"或"占位"标记
        assert "尚未实现" in text_control.value or "占位" in text_control.value


class TestQ19FieldTypeDispatch:
    """Q19 决策：FieldType → 控件类型分发"""

    def test_string_field_uses_textfield(self):
        editor = ParamEditor(step_type=StepType.OPEN_URL)
        ctrl = editor.field_controls["url"]
        assert isinstance(ctrl, ft.TextField)
        assert ctrl.multiline is False or ctrl.multiline is None

    def test_textarea_field_uses_multiline_textfield(self):
        editor = ParamEditor(step_type=StepType.NOTIFY)
        ctrl = editor.field_controls["body"]
        assert isinstance(ctrl, ft.TextField)
        assert ctrl.multiline is True

    def test_bool_field_uses_switch(self):
        editor = ParamEditor(step_type=StepType.DIAL)
        ctrl = editor.field_controls["auto_call"]
        assert isinstance(ctrl, ft.Switch)

    def test_enum_field_uses_dropdown(self):
        editor = ParamEditor(step_type=StepType.BLUETOOTH)
        ctrl = editor.field_controls["state"]
        assert isinstance(ctrl, ft.Dropdown)

    def test_int_range_field_uses_slider_row(self):
        editor = ParamEditor(step_type=StepType.DELAY)
        ctrl = editor.field_controls["duration"]
        # INT_RANGE 返回 Row（不是单控件）
        assert isinstance(ctrl, ft.Row)
        # data 是 (field, slider, text) 三元组
        assert isinstance(ctrl.data, tuple)
        assert len(ctrl.data) == 3
        assert isinstance(ctrl.data[1], ft.Slider)
        assert isinstance(ctrl.data[2], ft.Text)

    def test_int_field_uses_textfield_with_number_keyboard(self):
        editor = ParamEditor(step_type=StepType.CLICK)
        ctrl = editor.field_controls["x"]
        assert isinstance(ctrl, ft.TextField)
        assert ctrl.keyboard_type == ft.KeyboardType.NUMBER


class TestDifferentStepTypes:
    """多个 StepType 都能渲染"""

    @pytest.mark.parametrize("step_type", [
        StepType.OPEN_URL,        # AVAILABLE + STRING
        StepType.DARK_MODE,       # AVAILABLE + ENUM
        StepType.DELAY,           # AVAILABLE + INT_RANGE
        StepType.CLICK,           # LIMITED + STRING + INT
        StepType.DIAL,            # LIMITED + STRING + BOOL
        StepType.NOTIFY,          # LIMITED + STRING + TEXTAREA + STRING
        StepType.BLUETOOTH,       # NOT_IMPLEMENTED + ENUM
        StepType.POWER,           # NOT_IMPLEMENTED + ENUM
        StepType.BRIGHTNESS,      # NOT_IMPLEMENTED + INT_RANGE + BOOL
        StepType.SWIPE,           # LIMITED + INT*4 + INT_RANGE + INT
        StepType.VIBRATE,         # LIMITED + INT_RANGE + ENUM
        StepType.RUN_SUBTASK,     # AVAILABLE + STRING*2
    ])
    def test_step_type_renders_without_error(self, step_type):
        editor = ParamEditor(step_type=step_type)
        values = editor.get_values()
        # 应能正常读取所有字段值
        assert isinstance(values, dict)
        # field_controls 与 meta.fields 一一对应
        meta = get_step_type_meta(step_type)
        for f in meta.fields:
            assert f.key in editor.field_controls
            assert f.key in values
