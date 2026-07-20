"""步骤卡片组件

PRD 原样样式（参照 步骤记录器v1.0 HTML phone-screen 截图）：
- 左侧：序号圆圈（accent 主色 + 白字）
- 中间：步骤名 + 参数摘要 + 状态徽章
- 右侧：启用开关 + 删除按钮
- 占位步骤（NOT_IMPLEMENTED）：视觉与正常一致，但徽章置灰
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

from models.step import StepStatus, StepType, get_step_type_meta

# 状态色板（参照 PRD HTML :root CSS 变量）
STATUS_COLORS: dict[StepStatus, str] = {
    StepStatus.AVAILABLE: "#10b981",        # --success 绿
    StepStatus.LIMITED: "#f59e0b",           # --warning 黄
    StepStatus.NOT_IMPLEMENTED: "#94a3b8",   # 灰
}

STATUS_LABELS: dict[StepStatus, str] = {
    StepStatus.AVAILABLE: "可用",
    StepStatus.LIMITED: "受限",
    StepStatus.NOT_IMPLEMENTED: "未实现",
}


@dataclass
class StepCardData:
    """步骤卡片数据模型"""

    step_id: str
    step_order: int
    step_type: StepType
    name_zh: str                      # 显示名（取自 type meta 或自定义）
    params: dict                      # 参数摘要
    enabled: bool = True
    is_placeholder: bool = False       # 是否为占位步骤（用户保存但未实现）


class StepCard(ft.Container):
    """单个步骤卡片

    Attributes:
        data: 卡片数据
        on_toggle_enabled: 启用/禁用回调
        on_delete: 删除回调
        on_click: 点击卡片回调（弹出编辑）
    """

    def __init__(
        self,
        data: StepCardData,
        on_toggle_enabled: Callable[[str, bool], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
        on_click: Callable[[str], None] | None = None,
    ) -> None:
        self.data = data
        self._on_toggle_enabled = on_toggle_enabled
        self._on_delete = on_delete
        self._on_click = on_click

        meta = get_step_type_meta(data.step_type)
        status_color = STATUS_COLORS[meta.status]
        status_label = STATUS_LABELS[meta.status]

        # 占位步骤额外标记
        placeholder_badge = (
            ft.Container(
                content=ft.Text(
                    "占位", size=10, color="#94a3b8",
                    weight=ft.FontWeight.W_500,
                ),
                bgcolor="#f1f5f9",
                padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                border_radius=8,
                visible=data.is_placeholder,
            )
            if data.is_placeholder
            else ft.Container(width=0, height=0)
        )

        # 序号圆圈
        step_num = ft.Container(
            content=ft.Text(
                str(data.step_order),
                color="white",
                size=13,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            width=28,
            height=28,
            bgcolor="#2563eb",  # accent 主色
            border_radius=14,
            alignment=ft.Alignment.CENTER,
        )

        # 步骤名 + 参数摘要 + 状态徽章
        params_summary = self._format_params_summary(data.params)
        info_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            data.name_zh or meta.name_zh,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color="#1a1a2e",
                        ),
                        ft.Container(
                            content=ft.Text(
                                status_label,
                                size=10,
                                color="white",
                                weight=ft.FontWeight.W_500,
                            ),
                            bgcolor=status_color,
                            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                            border_radius=8,
                        ),
                        placeholder_badge,
                    ],
                    spacing=6,
                ),
                ft.Text(
                    params_summary,
                    size=12,
                    color="#6b7280",
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ) if params_summary else ft.Container(height=0),
            ],
            spacing=2,
            expand=True,
        )

        # 启用开关
        toggle = ft.Switch(
            value=data.enabled,
            on_change=self._handle_toggle,
            scale=0.8,
        )

        # 删除按钮
        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="#ef4444",
            icon_size=18,
            tooltip="删除",
            on_click=self._handle_delete,
        )

        # 整体行容器（参照 .step-item 样式）
        super().__init__(
            content=ft.Row(
                controls=[
                    step_num,
                    info_column,
                    toggle,
                    delete_btn,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor="#ffffff",
            border_radius=10,
            border=ft.Border.all(1, "#e5e7eb"),
            on_click=self._handle_click,
        )

    @staticmethod
    def _format_params_summary(params: dict) -> str:
        """格式化参数摘要（一行）"""
        if not params:
            return ""
        items = []
        for k, v in params.items():
            if v in (None, "", [], {}):
                continue
            items.append(f"{k}: {v}")
        return " · ".join(items[:3])  # 最多显示 3 项

    def _handle_toggle(self, e: ft.ControlEvent) -> None:
        """启用/禁用切换"""
        new_value = bool(e.control.value)
        self.data.enabled = new_value
        if self._on_toggle_enabled:
            self._on_toggle_enabled(self.data.step_id, new_value)

    def _handle_delete(self, e: ft.ControlEvent) -> None:
        """删除点击"""
        if self._on_delete:
            self._on_delete(self.data.step_id)

    def _handle_click(self, e: ft.ControlEvent) -> None:
        """整卡点击"""
        if self._on_click:
            self._on_click(self.data.step_id)


def render_step_cards(
    steps: list[StepCardData],
    on_toggle_enabled: Callable[[str, bool], None] | None = None,
    on_delete: Callable[[str], None] | None = None,
    on_click: Callable[[str], None] | None = None,
) -> list[StepCard]:
    """批量渲染步骤卡片列表

    Args:
        steps: 卡片数据列表
        on_toggle_enabled/on_delete/on_click: 回调（每个卡片共用）

    Returns:
        StepCard 控件列表（用于 ListView.controls）
    """
    return [
        StepCard(
            data=s,
            on_toggle_enabled=on_toggle_enabled,
            on_delete=on_delete,
            on_click=on_click,
        )
        for s in steps
    ]
