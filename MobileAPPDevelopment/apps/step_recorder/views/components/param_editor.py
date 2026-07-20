"""参数编辑器组件

按 StepType 动态生成参数表单（Q19 决策）：
- BOOL → Switch
- INT → TextField（数字键盘）
- INT_RANGE → Slider + 数值显示
- STRING → TextField
- TEXTAREA → TextField（multiline）
- ENUM → Dropdown
- COORDINATE → （未来扩展）

按 Q20 决策暴露：
- get_values() -> dict
- is_dirty() -> bool（供 step_editor_view 检测未保存修改）
- reset_to_defaults()
- validate() -> list[str]
"""
from __future__ import annotations

from typing import Any

import flet as ft

from models.step import (
    FieldType,
    ParamField,
    StepStatus,
    StepType,
    get_step_type_meta,
)


# ---- 控件工厂：每个 FieldType 对应一个构造函数 ----


def _make_string_field(f: ParamField, initial: Any) -> ft.TextField:
    return ft.TextField(
        label=f.label_zh,
        value=str(initial) if initial is not None else "",
        hint_text=f.placeholder,
        keyboard_type=ft.KeyboardType.TEXT,
        dense=True,
        border_radius=8,
    )


def _make_textarea_field(f: ParamField, initial: Any) -> ft.TextField:
    return ft.TextField(
        label=f.label_zh,
        value=str(initial) if initial is not None else "",
        hint_text=f.placeholder,
        keyboard_type=ft.KeyboardType.TEXT,
        multiline=True,
        min_lines=3,
        max_lines=6,
        dense=True,
        border_radius=8,
    )


def _make_int_field(f: ParamField, initial: Any) -> ft.TextField:
    return ft.TextField(
        label=f.label_zh,
        value=str(initial) if initial is not None else "",
        hint_text=f.placeholder or f"整数（>= {f.min_value}）" if f.min_value is not None else "整数",
        keyboard_type=ft.KeyboardType.NUMBER,
        dense=True,
        border_radius=8,
    )


def _make_bool_field(f: ParamField, initial: Any) -> ft.Switch:
    return ft.Switch(
        label=f.label_zh,
        value=bool(initial) if initial is not None else bool(f.default),
    )


def _make_int_range_field(
    f: ParamField, initial: Any, on_change_handler=None,
) -> ft.Row:
    """INT_RANGE 用 Slider + 数值 Text 显示

    返回 Row（含 Slider 和 Text）。
    on_change_handler 由 ParamEditor 注入以更新 Text。
    """
    initial_val = (
        int(initial)
        if initial is not None
        else int(f.default) if f.default is not None else int(f.min_value or 0)
    )
    # divisions = (max - min) / step
    divisions = int((f.max_value - (f.min_value or 0)) / max(f.step, 1))

    value_text = ft.Text(
        str(initial_val),
        size=12,
        color="#1a1a2e",
        weight=ft.FontWeight.W_600,
        width=40,
        text_align=ft.TextAlign.RIGHT,
    )

    slider = ft.Slider(
        value=float(initial_val),
        min=float(f.min_value or 0),
        max=float(f.max_value or 100),
        divisions=divisions,
        label="{value}",
        expand=True,
    )

    # 用 Row 关联，外部通过 .data 关联 ParamField
    row = ft.Row(
        controls=[
            ft.Text(
                f.label_zh,
                size=13,
                color="#1a1a2e",
                width=80,
            ),
            slider,
            value_text,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
    )
    row.data = (f, slider, value_text)

    # Slider.on_change 时更新 value_text
    def _on_slider_change(e: ft.ControlEvent) -> None:
        v = int(e.control.value)
        value_text.value = str(v)
        if on_change_handler:
            on_change_handler()

    slider.on_change = _on_slider_change
    return row


def _make_enum_field(f: ParamField, initial: Any) -> ft.Dropdown:
    options = [
        ft.DropdownOption(key=value, text=label)
        for value, label in f.options
    ]
    initial_value = (
        str(initial) if initial is not None
        else str(f.default) if f.default is not None
        else None
    )
    return ft.Dropdown(
        label=f.label_zh,
        value=initial_value,
        options=options,
        dense=True,
        border_radius=8,
    )


# ---- 主组件 ----


class ParamEditor(ft.Container):
    """参数编辑器：按 StepType 渲染动态参数表单

    Attributes:
        step_type: 当前编辑的步骤类型
        initial_params: 初始参数值（dict），用于回填
        field_controls: 字段 key → 控件（或 Row）映射
        on_change: 表单变化回调（用于外部 dirty 检测）
    """

    def __init__(
        self,
        step_type: StepType,
        initial_params: dict | None = None,
        on_change: Any = None,
    ) -> None:
        self.step_type = step_type
        self._initial_params = dict(initial_params) if initial_params else {}
        self._on_change = on_change
        self._dirty = False

        meta = get_step_type_meta(step_type)
        self._meta = meta

        # 构造每个字段的控件
        self.field_controls: dict[str, Any] = {}
        self._field_meta: dict[str, ParamField] = {}

        # 内嵌状态变更监听
        def _mark_dirty(*_args, **_kwargs) -> None:
            self._dirty = True
            if self._on_change:
                self._on_change()

        rows: list[ft.Control] = []

        # 空字段提示
        if not meta.fields:
            rows.append(
                ft.Container(
                    content=ft.Text(
                        "此步骤无需参数" if meta.status != StepStatus.NOT_IMPLEMENTED
                        else "此步骤尚未实现 · 仅保存占位",
                        size=13,
                        color="#94a3b8",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.Padding(left=12, right=12, top=24, bottom=24),
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for f in meta.fields:
                initial_value = self._initial_params.get(f.key, f.default)
                ctrl = self._build_field_control(f, initial_value, _mark_dirty)
                self.field_controls[f.key] = ctrl
                self._field_meta[f.key] = f
                rows.append(ctrl)

        # 整体容器
        super().__init__(
            content=ft.Column(
                controls=rows,
                spacing=10,
                expand=True,
            ),
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor="#ffffff",
            border_radius=12,
            border=ft.Border.all(1, "#e5e7eb"),
        )

    def _build_field_control(
        self,
        f: ParamField,
        initial: Any,
        on_change_handler: Any,
    ) -> ft.Control:
        """按 FieldType 分发构造"""
        if f.field_type == FieldType.STRING:
            tf = _make_string_field(f, initial)
            tf.on_change = lambda e: on_change_handler()
            return tf
        if f.field_type == FieldType.TEXTAREA:
            tf = _make_textarea_field(f, initial)
            tf.on_change = lambda e: on_change_handler()
            return tf
        if f.field_type == FieldType.INT:
            tf = _make_int_field(f, initial)
            tf.on_change = lambda e: on_change_handler()
            return tf
        if f.field_type == FieldType.BOOL:
            sw = _make_bool_field(f, initial)
            sw.on_change = lambda e: on_change_handler()
            return sw
        if f.field_type == FieldType.INT_RANGE:
            return _make_int_range_field(f, initial, on_change_handler)
        if f.field_type == FieldType.ENUM:
            dd = _make_enum_field(f, initial)
            # Flet 0.86.1: Dropdown 用 on_select（非 on_change）
            dd.on_select = lambda e: on_change_handler()
            return dd
        # COORDINATE 等未来类型：fallback 到 STRING
        return _make_string_field(f, initial)

    # ---- 读取值 ----

    def get_values(self) -> dict:
        """从控件读取当前参数值"""
        values: dict[str, Any] = {}
        for key, ctrl in self.field_controls.items():
            f = self._field_meta[key]
            values[key] = self._read_field_value(f, ctrl)
        return values

    def _read_field_value(self, f: ParamField, ctrl: ft.Control) -> Any:
        if f.field_type == FieldType.STRING:
            return ctrl.value or ""
        if f.field_type == FieldType.TEXTAREA:
            return ctrl.value or ""
        if f.field_type == FieldType.INT:
            try:
                return int(ctrl.value) if ctrl.value not in (None, "") else None
            except (TypeError, ValueError):
                return None
        if f.field_type == FieldType.BOOL:
            return bool(ctrl.value)
        if f.field_type == FieldType.INT_RANGE:
            # ctrl 是 Row，data 是 (field, slider, text)
            slider = ctrl.data[1]
            try:
                return int(slider.value)
            except (TypeError, ValueError):
                return None
        if f.field_type == FieldType.ENUM:
            return ctrl.value
        # fallback
        return ctrl.value

    # ---- dirty 检测（Q20 决策）----

    def is_dirty(self) -> bool:
        """检测用户是否修改了参数"""
        if self._dirty:
            return True
        # 进一步检测：控件当前值与初始值是否不同
        current = self.get_values()
        for key, value in current.items():
            initial = self._initial_params.get(key, self._field_meta[key].default)
            if _normalize(value) != _normalize(initial):
                return True
        return False

    def reset_to_defaults(self) -> None:
        """重置所有字段为默认值"""
        for key, ctrl in self.field_controls.items():
            f = self._field_meta[key]
            self._set_field_value(f, ctrl, f.default)
        self._dirty = False

    def _set_field_value(self, f: ParamField, ctrl: ft.Control, value: Any) -> None:
        if f.field_type in (FieldType.STRING, FieldType.TEXTAREA, FieldType.INT):
            ctrl.value = str(value) if value is not None else ""
        elif f.field_type == FieldType.BOOL:
            ctrl.value = bool(value)
        elif f.field_type == FieldType.INT_RANGE:
            slider = ctrl.data[1]
            text = ctrl.data[2]
            slider.value = float(value) if value is not None else float(f.min_value or 0)
            text.value = str(int(slider.value))
        elif f.field_type == FieldType.ENUM:
            ctrl.value = str(value) if value is not None else None

    # ---- 校验 ----

    def validate(self) -> list[str]:
        """校验表单，返回错误信息列表（空列表 = 通过）"""
        errors: list[str] = []
        values = self.get_values()
        for key, value in values.items():
            f = self._field_meta[key]
            if f.required and (value is None or value == ""):
                errors.append(f"{f.label_zh} 是必填项")
            elif f.field_type == FieldType.INT and value is not None:
                if f.min_value is not None and value < f.min_value:
                    errors.append(f"{f.label_zh} 不能小于 {f.min_value}")
            elif f.field_type == FieldType.INT_RANGE and value is not None:
                if f.min_value is not None and value < f.min_value:
                    errors.append(f"{f.label_zh} 不能小于 {f.min_value}")
                if f.max_value is not None and value > f.max_value:
                    errors.append(f"{f.label_zh} 不能大于 {f.max_value}")
        return errors


def _normalize(value: Any) -> str:
    """归一化值用于比较（处理 None/str/int）"""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
