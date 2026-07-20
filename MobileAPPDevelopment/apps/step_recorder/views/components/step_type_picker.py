"""步骤类型选择面板

PRD 设计：
- 顶部搜索框（全局搜索，跨所有分类）
- 5 分类标签页：模拟操作/系统控制/显示/音频/辅助
- 4 列网格展示该分类下全部类型
- 每个卡片：图标 + 中文名 + 状态角标
- 不可做项点击：展开"尚未完成"提示 + 自动保存占位（无需确认）
- 搜索时：按分类分段展示匹配结果（每段标题 + 网格）

回调：
- on_select(step_type, is_placeholder): 用户选中某个类型
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from models.step import (
    STEP_TYPE_REGISTRY,
    StepCategory,
    StepStatus,
    StepType,
    get_step_type_meta,
)

# 分类中文名映射
CATEGORY_LABELS: dict[StepCategory, str] = {
    StepCategory.SIMULATION: "模拟操作",
    StepCategory.SYSTEM_CONTROL: "系统控制",
    StepCategory.DISPLAY: "显示设置",
    StepCategory.AUDIO_HAPTIC: "音频触感",
    StepCategory.AUXILIARY: "辅助通知",
}

# 状态色（与 step_card 一致）
STATUS_COLORS: dict[StepStatus, str] = {
    StepStatus.AVAILABLE: "#10b981",
    StepStatus.LIMITED: "#f59e0b",
    StepStatus.NOT_IMPLEMENTED: "#94a3b8",
}

STATUS_LABELS: dict[StepStatus, str] = {
    StepStatus.AVAILABLE: "可用",
    StepStatus.LIMITED: "受限",
    StepStatus.NOT_IMPLEMENTED: "未实现",
}


class StepTypeTile(ft.Container):
    """单个类型卡片（网格中的一项）

    显示图标 + 中文名 + 状态角标。
    不可做项点击后展开底部提示文字 + 自动触发 on_select(is_placeholder=True)
    """

    def __init__(
        self,
        step_type: StepType,
        on_select: Callable[[StepType, bool], None] | None = None,
    ) -> None:
        self.step_type = step_type
        self._on_select = on_select
        meta = get_step_type_meta(step_type)
        status_color = STATUS_COLORS[meta.status]
        status_label = STATUS_LABELS[meta.status]
        is_not_impl = meta.status == StepStatus.NOT_IMPLEMENTED

        # 状态角标（小色块 + 文字）
        status_badge = ft.Container(
            content=ft.Text(
                status_label,
                size=9,
                color="white",
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=status_color,
            padding=ft.Padding(left=4, right=4, top=1, bottom=1),
            border_radius=4,
        )

        # 图标
        icon = ft.Icon(
            icon=meta.icon,
            color="#1a1a2e" if not is_not_impl else "#94a3b8",
            size=28,
        )

        # 中文名
        name = ft.Text(
            meta.name_zh,
            size=12,
            color="#1a1a2e" if not is_not_impl else "#94a3b8",
            weight=ft.FontWeight.W_500,
            text_align=ft.TextAlign.CENTER,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # 提示文字（默认隐藏，点击 NOT_IMPLEMENTED 后展开）
        self.hint_text = ft.Text(
            "尚未完成 · 已保存为占位",
            size=10,
            color="#94a3b8",
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

        # 整体布局
        super().__init__(
            content=ft.Column(
                controls=[
                    icon,
                    name,
                    status_badge,
                    self.hint_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            width=72,
            height=96,
            padding=ft.Padding(left=4, right=4, top=8, bottom=8),
            bgcolor="#f9fafb" if is_not_impl else "#ffffff",
            border_radius=10,
            border=ft.Border.all(
                1, "#e5e7eb" if not is_not_impl else "#f1f5f9"
            ),
            on_click=self._handle_click,
        )

    def _handle_click(self, e: ft.ControlEvent) -> None:
        """点击处理：可用/受限 → 直接选中；不可做 → 展开提示 + 自动保存占位"""
        meta = get_step_type_meta(self.step_type)
        if meta.status == StepStatus.NOT_IMPLEMENTED:
            # 展开提示
            self.hint_text.visible = True
            # 自动保存占位
            if self._on_select:
                self._on_select(self.step_type, True)
        else:
            if self._on_select:
                self._on_select(self.step_type, False)


class StepTypePicker(ft.Container):
    """步骤类型选择面板

    包含：搜索框 + 5 分类标签 + 4 列网格

    Attributes:
        on_select: 选中类型回调 (step_type, is_placeholder)
        on_search_change: 搜索内容变化回调
    """

    def __init__(
        self,
        on_select: Callable[[StepType, bool], None] | None = None,
        on_search_change: Callable[[str], None] | None = None,
        initial_category: StepCategory = StepCategory.SIMULATION,
    ) -> None:
        self._on_select = on_select
        self._on_search_change = on_search_change
        self._current_category = initial_category
        self._search_query = ""

        # 搜索框
        self.search_field = ft.TextField(
            hint_text="搜索步骤类型...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._handle_search,
            dense=True,
            border_radius=8,
        )

        # 5 分类按钮（不使用 ft.Tabs，因 Flet 0.86 改了 Tabs 签名；
        # 改用自定义 Container 按钮组，更可控且稳定）
        self.category_buttons: list[ft.Container] = []
        for cat, label in CATEGORY_LABELS.items():
            btn = self._make_category_button(cat, label)
            self.category_buttons.append(btn)

        self.category_row = ft.Row(
            controls=self.category_buttons,
            scroll=ft.ScrollMode.AUTO,
            spacing=4,
        )

        # 内容容器（动态切换：网格 or 搜索结果分段）
        self.content_area = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # 整体布局
        super().__init__(
            content=ft.Column(
                controls=[
                    self.search_field,
                    self.category_row,
                    self.content_area,
                ],
                spacing=8,
                expand=True,
            ),
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor="#ffffff",
            border_radius=12,
            border=ft.Border.all(1, "#e5e7eb"),
        )

        # 初始渲染
        self._render()

    def _handle_search(self, e: ft.ControlEvent) -> None:
        """搜索框内容变化"""
        self._search_query = e.control.value or ""
        if self._on_search_change:
            self._on_search_change(self._search_query)
        self._render()

    def _make_category_button(self, cat: StepCategory, label: str) -> ft.Container:
        """构造单个分类按钮（选中态用背景色区分）"""
        is_active = cat == self._current_category
        return ft.Container(
            content=ft.Text(
                label,
                size=12,
                color="white" if is_active else "#6b7280",
                weight=ft.FontWeight.W_500,
            ),
            padding=ft.Padding(left=12, right=12, top=6, bottom=6),
            bgcolor="#2563eb" if is_active else "#f1f5f9",
            border_radius=8,
            on_click=self._handle_category_click,
            data=cat.value,
        )

    def _handle_category_click(self, e: ft.ControlEvent) -> None:
        """分类按钮点击"""
        cat_value = e.control.data
        self._current_category = StepCategory(cat_value)
        # 清空搜索（切换分类时）
        if self._search_query:
            self._search_query = ""
            self.search_field.value = ""
        # 刷新所有按钮的选中态
        for btn in self.category_buttons:
            is_active = btn.data == cat_value
            text_ctrl = btn.content  # type: ignore[union-attr]
            text_ctrl.color = "white" if is_active else "#6b7280"  # type: ignore[union-attr]
            btn.bgcolor = "#2563eb" if is_active else "#f1f5f9"
        self._render()

    def _render(self) -> None:
        """根据当前搜索/分类状态重新渲染内容区"""
        self.content_area.controls.clear()

        if self._search_query:
            # 搜索模式：跨所有分类，按分类分段展示匹配项
            self._render_search_results()
        else:
            # 默认模式：仅显示当前分类的网格
            self._render_single_category(self._current_category)

    def _render_single_category(self, category: StepCategory) -> None:
        """渲染单个分类的网格"""
        items = [
            (st, meta)
            for st, meta in STEP_TYPE_REGISTRY.items()
            if meta.category == category
        ]

        grid = self._build_grid(items)
        self.content_area.controls.append(
            ft.Column(
                controls=[
                    ft.Text(
                        CATEGORY_LABELS[category],
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color="#1a1a2e",
                    ),
                    grid,
                ],
                spacing=8,
            )
        )

    def _render_search_results(self) -> None:
        """渲染搜索结果：按分类分段"""
        query = self._search_query.lower()
        any_match = False

        for category in StepCategory:
            items = [
                (st, meta)
                for st, meta in STEP_TYPE_REGISTRY.items()
                if meta.category == category
                and (
                    query in meta.name_zh.lower()
                    or query in meta.description.lower()
                    or query in meta.type_id.lower()
                )
            ]
            if not items:
                continue
            any_match = True

            self.content_area.controls.append(
                ft.Column(
                    controls=[
                        ft.Text(
                            f"{CATEGORY_LABELS[category]} ({len(items)})",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color="#1a1a2e",
                        ),
                        self._build_grid(items),
                    ],
                    spacing=6,
                )
            )

        if not any_match:
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.SEARCH_OFF,
                                color="#94a3b8",
                                size=32,
                            ),
                            ft.Text(
                                f'未找到匹配 "{self._search_query}" 的步骤类型',
                                size=13,
                                color="#6b7280",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=ft.Padding(left=20, right=20, top=40, bottom=40),
                    alignment=ft.Alignment.CENTER,
                )
            )

    def _build_grid(
        self,
        items: list[tuple[StepType, "StepTypeMeta"]],
    ) -> ft.GridView:
        """构造 4 列网格"""
        tiles = [
            StepTypeTile(
                step_type=st,
                on_select=self._on_select,
            )
            for st, _ in items
        ]
        return ft.GridView(
            controls=tiles,
            runs_count=4,           # 4 列
            max_extent=80,          # 每项最大宽度
            child_aspect_ratio=0.9,  # 宽高比
            spacing=4,
            run_spacing=4,
        )


def make_placeholder_snackbar_message(step_type: StepType) -> str:
    """生成占位保存提示文案"""
    meta = get_step_type_meta(step_type)
    return f"已保存占位步骤「{meta.name_zh}」（尚未实现）"
