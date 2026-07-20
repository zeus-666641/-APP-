"""执行日志详情视图（M5）

按 PRD 第 8 章实现日志详情（独立路由 /logs/{id}，Q42）：
- 顶部 AppBar：返回 + 删除
- 概览卡片：任务名 + 状态徽章 + 元信息（触发源/开始时间/耗时/总步骤数）
- 错误信息（失败/中止时显示）
- section-title: "步骤执行时间轴"
- 时间轴列表（Q43：序号 + 图标 + 名称 + 状态点 + 耗时）
- 错误步骤展开错误信息

变更记录:
- Q42: 独立路由 /logs/{id}
- Q43: 时间轴样式（序号+图标+名称+状态点+耗时）
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable

import flet as ft

from models.log import ExecutionLog
from services.log_service import (
    format_duration,
    format_relative_time,
    get_status_color,
    get_status_label,
    get_trigger_source_label,
)
from services.stats_service import ExecutionStatus

# 配色
_ACCENT = "#2563eb"
_ACCENT_LIGHT = "#dbeafe"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"
_DANGER = "#ef4444"
_SUCCESS = "#10b981"
_WARNING = "#f59e0b"


class LogDetailView(ft.View):
    """执行日志详情视图

    Attributes:
        page: Flet 页面对象
        log_id: 日志 ID
        log: 日志数据（如果传入则使用，否则从服务加载）
        on_delete: 删除回调（参数：log_id）
    """

    def __init__(
        self,
        page: ft.Page,
        log_id: str,
        log: ExecutionLog | None = None,
        on_delete: Callable[[str], None] | None = None,
    ) -> None:
        self._page = page
        self._log_id = log_id
        self._on_delete = on_delete

        if log is None:
            # 从服务加载（延迟导入避免循环依赖）
            from services.log_service import LogService

            self._service = LogService()
            self._log = self._service.get_by_id(log_id)
        else:
            self._service = None
            self._log = log

        # 构建视图
        if self._log is None:
            super().__init__(
                route=f"/logs/{log_id}",
                controls=[self._build_not_found()],
                spacing=0,
            )
            return

        super().__init__(
            route=f"/logs/{log_id}",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                    ),
                    title=ft.Text("日志详情"),
                    bgcolor=_ACCENT,
                    color="white",
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=self._handle_delete_click,
                            tooltip="删除日志",
                            icon_color="white",
                        ),
                    ],
                ),
                ft.SafeArea(
                    content=ft.Column(
                        controls=[
                            # 概览卡片
                            self._build_overview_card(),
                            # 错误信息（若有）
                            self._build_error_card(),
                            # 时间轴 section-title
                            self._build_section_title(
                                "步骤执行时间轴",
                                f"{self._log.step_count} 步 · 成功 {self._log.success_step_count} · 失败 {self._log.failed_step_count}",
                            ),
                            # 时间轴列表
                            self._build_timeline(),
                        ],
                        spacing=12,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        )

    # ---- 组件构建 ----

    def _build_not_found(self) -> ft.Control:
        """日志不存在占位"""
        return ft.SafeArea(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.ERROR_OUTLINE,
                            color=_MUTED,
                            size=48,
                        ),
                        ft.Text(
                            "日志不存在",
                            size=14,
                            color=_INK,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            f"找不到 ID 为 {self._log_id} 的日志",
                            size=12,
                            color=_MUTED,
                        ),
                        ft.Button(
                            "返回列表",
                            icon=ft.Icons.ARROW_BACK,
                            on_click=self._handle_back,
                            bgcolor=_ACCENT,
                            color="white",
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            ),
            expand=True,
        )

    def _build_overview_card(self) -> ft.Control:
        """概览卡片：任务名 + 状态徽章 + 元信息"""
        log = self._log
        assert log is not None

        status_label = get_status_label(log.status)
        status_color = get_status_color(log.status)

        # 状态徽章
        status_badge = ft.Container(
            content=ft.Text(
                status_label,
                size=12,
                weight=ft.FontWeight.W_600,
                color="white",
            ),
            bgcolor=status_color,
            padding=ft.Padding(left=8, right=8, top=4, bottom=4),
            border_radius=4,
        )

        # 任务图标块
        icon_block = ft.Container(
            content=ft.Icon(
                icon=log.task_icon if log.task_icon else "play_arrow",
                color=_ACCENT,
                size=24,
            ),
            width=48,
            height=48,
            alignment=ft.Alignment.CENTER,
            bgcolor=_ACCENT_LIGHT,
            border_radius=12,
        )

        # 任务名 + 状态徽章
        name_row = ft.Row(
            controls=[
                icon_block,
                ft.Column(
                    controls=[
                        ft.Text(
                            log.task_name,
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=_INK,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"日志 ID：{log.log_id}",
                            size=11,
                            color=_MUTED,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                status_badge,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        # 元信息行（触发源 / 开始时间 / 耗时 / 步骤数）
        trigger_label = get_trigger_source_label(log.trigger_source)
        relative_time = format_relative_time(log.started_at)
        absolute_time = log.started_at.strftime("%Y-%m-%d %H:%M:%S")
        duration = format_duration(log.duration_ms)

        meta_items = [
            self._build_meta_item(
                icon=ft.Icons.FLASH_ON_OUTLINED,
                label="触发源",
                value=trigger_label,
            ),
            self._build_meta_item(
                icon=ft.Icons.SCHEDULE_OUTLINED,
                label="开始时间",
                value=f"{relative_time}\n{absolute_time}",
            ),
            self._build_meta_item(
                icon=ft.Icons.TIMER_OUTLINED,
                label="总耗时",
                value=duration,
            ),
            self._build_meta_item(
                icon=ft.Icons.LIST_ALT_OUTLINED,
                label="步骤数",
                value=f"{log.step_count}",
            ),
        ]

        # 2x2 元信息网格
        meta_grid = ft.Column(
            controls=[
                ft.Row(controls=meta_items[0:2], spacing=8),
                ft.Row(controls=meta_items[2:4], spacing=8),
            ],
            spacing=8,
        )

        return ft.Container(
            content=ft.Column(
                controls=[name_row, meta_grid],
                spacing=12,
            ),
            padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            bgcolor=_BG2,
            border_radius=12,
            border=ft.Border.all(1, _RULE),
            margin=ft.Margin(left=16, right=16, top=8, bottom=0),
        )

    def _build_meta_item(self, icon: str, label: str, value: str) -> ft.Control:
        """单个元信息项（4 宫格中一格）"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon=icon, color=_ACCENT, size=16),
                    ft.Column(
                        controls=[
                            ft.Text(
                                label,
                                size=10,
                                color=_MUTED,
                            ),
                            ft.Text(
                                value,
                                size=12,
                                color=_INK,
                                weight=ft.FontWeight.W_500,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=10, right=10, top=8, bottom=8),
            bgcolor="#f9fafb",
            border_radius=8,
            expand=True,
        )

    def _build_error_card(self) -> ft.Control:
        """错误信息卡片（无错误时返回空 Container）"""
        if self._log is None or not self._log.error_message:
            return ft.Container(height=0, padding=0)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon=ft.Icons.ERROR_OUTLINE, color=_DANGER, size=20),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "错误信息",
                                size=11,
                                color=_DANGER,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                self._log.error_message,
                                size=13,
                                color=_INK,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            bgcolor="#fef2f2",
            border_radius=10,
            border=ft.Border.all(1, "#fecaca"),
            margin=ft.Margin(left=16, right=16, top=8, bottom=0),
        )

    def _build_section_title(self, title: str, right_text: str) -> ft.Control:
        """section-title（与 stats_view / StepEditorView F9c 一致）"""
        controls = [
            ft.Text(
                title,
                size=14,
                weight=ft.FontWeight.W_600,
                color=_INK,
            )
        ]
        if right_text:
            controls.append(
                ft.Text(
                    right_text,
                    size=12,
                    color=_MUTED,
                )
            )
        return ft.Container(
            content=ft.Row(
                controls=controls,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=16, right=16, top=12, bottom=4),
        )

    def _build_timeline(self) -> ft.Control:
        """步骤时间轴列表（Q43）"""
        if self._log is None or not self._log.step_executions:
            return ft.Container(
                content=ft.Text(
                    "暂无步骤执行记录",
                    size=12,
                    color=_MUTED,
                ),
                padding=ft.Padding(left=16, right=16, top=16, bottom=16),
                alignment=ft.Alignment.CENTER,
            )

        timeline_items: list[ft.Control] = []
        for i, step in enumerate(self._log.step_executions):
            is_last = i == len(self._log.step_executions) - 1
            timeline_items.append(self._build_timeline_item(step, is_last))

        return ft.Container(
            content=ft.Column(
                controls=timeline_items,
                spacing=0,
            ),
            padding=ft.Padding(left=16, right=16, top=0, bottom=16),
        )

    def _build_timeline_item(self, step, is_last: bool) -> ft.Control:
        """单个时间轴节点（Q43：序号 + 图标 + 名称 + 状态点 + 耗时 + 错误信息）"""
        status_color = get_status_color(step.status)
        status_label = get_status_label(step.status)

        # 序号圆圈
        order_circle = ft.Container(
            content=ft.Text(
                str(step.order),
                size=11,
                color="white",
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
            ),
            width=24,
            height=24,
            bgcolor=_ACCENT,
            border_radius=12,
            alignment=ft.Alignment.CENTER,
        )

        # 步骤图标
        step_icon = ft.Container(
            content=ft.Icon(
                icon=step.icon if step.icon else "play_arrow",
                color=status_color,
                size=18,
            ),
            width=32,
            height=32,
            bgcolor="#f3f4f6",
            border_radius=8,
            alignment=ft.Alignment.CENTER,
        )

        # 步骤名 + 状态点
        name_col = ft.Column(
            controls=[
                ft.Text(
                    step.step_name,
                    size=13,
                    color=_INK,
                    weight=ft.FontWeight.W_500,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            width=6,
                            height=6,
                            bgcolor=status_color,
                            border_radius=3,
                        ),
                        ft.Text(
                            status_label,
                            size=11,
                            color=status_color,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            "·",
                            size=11,
                            color=_MUTED,
                        ),
                        ft.Text(
                            step.step_type,
                            size=11,
                            color=_MUTED,
                        ),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=4,
            expand=True,
        )

        # 耗时
        duration_text = ft.Text(
            format_duration(step.duration_ms),
            size=11,
            color=_MUTED,
        )

        # 时间轴节点行
        node_row = ft.Row(
            controls=[
                order_circle,
                step_icon,
                name_col,
                duration_text,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 错误信息（仅失败时显示）
        error_block: list[ft.Control] = []
        if step.status == ExecutionStatus.FAILED and step.error_message:
            error_block.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.ERROR_OUTLINE,
                                color=_DANGER,
                                size=12,
                            ),
                            ft.Text(
                                step.error_message,
                                size=11,
                                color=_DANGER,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                            ),
                        ],
                        spacing=4,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                    bgcolor="#fef2f2",
                    border_radius=4,
                    margin=ft.Margin(left=32, right=0, top=4, bottom=0),
                )
            )

        # 连接线（非最后一步显示）
        connector = ft.Container(
            width=2,
            height=16,
            bgcolor=_RULE,
            margin=ft.Margin(left=11, right=0, top=0, bottom=0),
        ) if not is_last else ft.Container(height=0)

        return ft.Column(
            controls=[
                ft.Container(
                    content=node_row,
                    padding=ft.Padding(left=0, right=0, top=4, bottom=4),
                ),
                *error_block,
                connector,
            ],
            spacing=0,
        )

    # ---- 事件 ----

    def _handle_back(self, e: ft.ControlEvent | None = None) -> None:
        """返回上一页"""
        try:
            self._page.go("/logs")
        except Exception:
            pass

    def _handle_delete_click(self, e: ft.ControlEvent) -> None:
        """删除按钮（弹出二次确认）"""
        if self._log is None:
            return
        page = e.page
        if page is None:
            # 测试环境
            if self._on_delete:
                self._on_delete(self._log_id)
            return

        log_id = self._log_id
        task_name = self._log.task_name

        def _close_dialog(_e: ft.ControlEvent | None = None) -> None:
            dialog.open = False
            try:
                page.update()
            except Exception:
                pass
            if dialog in page.overlay:
                page.overlay.remove(dialog)

        def _confirm_delete(_e: ft.ControlEvent) -> None:
            _close_dialog()
            # 先调用服务删除
            if self._service is not None:
                self._service.delete(log_id)
            if self._on_delete:
                self._on_delete(log_id)
            # 跳回列表
            try:
                page.go("/logs")
            except Exception:
                pass

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除"),
            content=ft.Text(
                f"确定要删除任务「{task_name}」的执行日志吗？此操作不可撤销。"
            ),
            actions=[
                ft.Button("取消", on_click=_close_dialog),
                ft.Button(
                    "确认删除",
                    on_click=_confirm_delete,
                    bgcolor=_DANGER,
                    color="white",
                ),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        try:
            page.update()
        except Exception:
            pass
