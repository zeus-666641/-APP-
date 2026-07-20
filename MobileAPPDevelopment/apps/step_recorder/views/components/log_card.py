"""日志卡片组件（M5）

单个执行日志的卡片展示，用于 logs_view 列表。

列表项字段（Q46 决策）：
- 任务名 + 状态徽章
- 触发源
- 开始时间（相对）
- 耗时

布局：
- 顶部：[任务图标] [任务名 + 状态徽章]
- 中部：[触发源标签] [开始时间(相对)] [耗时]
- 底部左下角：[删除按钮]（Q49）

变更记录:
- Q46: 列表项字段
- Q49: 删除按钮放在卡片左下角（与 F9b 二次确认风格一致）
"""
from __future__ import annotations

from dataclasses import dataclass
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

# 配色（与 step_recorder 项目一致）
_ACCENT = "#2563eb"
_ACCENT_LIGHT = "#dbeafe"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_DANGER = "#ef4444"
_SUCCESS = "#10b981"


@dataclass
class LogCardData:
    """LogCard 数据模型（与 ExecutionLog 解耦，方便 mock 测试）

    Attributes:
        log_id: 日志 ID
        task_id: 任务 ID
        task_name: 任务名
        task_icon: 任务图标（Material icon name）
        status: 执行状态
        trigger_source: 触发源
        started_at: 开始时间
        duration_ms: 耗时（毫秒）
        step_count: 步骤总数
        error_message: 错误信息（成功时为空）
    """

    log_id: str
    task_id: str
    task_name: str
    task_icon: str = "play_arrow"
    status: str = "success"
    trigger_source: str = "manual"
    started_at: datetime | None = None
    duration_ms: int = 0
    step_count: int = 0
    error_message: str = ""

    @classmethod
    def from_log(cls, log: ExecutionLog) -> "LogCardData":
        """从 ExecutionLog 构造"""
        return cls(
            log_id=log.log_id,
            task_id=log.task_id,
            task_name=log.task_name,
            task_icon=log.task_icon,
            status=log.status.value,
            trigger_source=log.trigger_source.value,
            started_at=log.started_at,
            duration_ms=log.duration_ms,
            step_count=log.step_count,
            error_message=log.error_message,
        )


class LogCard(ft.Container):
    """单个日志卡片

    Attributes:
        card_data: 卡片数据
        on_click: 点击回调（参数：log_id）
        on_delete: 删除回调（参数：log_id）
    """

    def __init__(
        self,
        data: LogCardData,
        on_click: Callable[[str], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
    ) -> None:
        self.card_data = data
        self._on_click = on_click
        self._on_delete = on_delete

        # 状态徽章
        status_label = get_status_label(_to_status(data.status))
        status_color = get_status_color(_to_status(data.status))
        status_badge = ft.Container(
            content=ft.Text(
                status_label,
                size=10,
                weight=ft.FontWeight.W_600,
                color="white",
            ),
            bgcolor=status_color,
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            border_radius=4,
        )

        # 任务图标
        icon_block = ft.Container(
            content=ft.Icon(
                icon=data.task_icon if data.task_icon else "play_arrow",
                color=_ACCENT,
                size=20,
            ),
            width=36,
            height=36,
            alignment=ft.Alignment.CENTER,
            bgcolor=_ACCENT_LIGHT,
            border_radius=8,
        )

        # 任务名行
        name_row = ft.Row(
            controls=[
                icon_block,
                ft.Column(
                    controls=[
                        ft.Text(
                            data.task_name,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=_INK,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            f"{data.step_count} 个步骤",
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
            spacing=8,
        )

        # 触发源 / 开始时间 / 耗时
        trigger_label = get_trigger_source_label(_to_trigger(data.trigger_source))
        meta_items: list[ft.Control] = [
            ft.Container(
                content=ft.Text(trigger_label, size=11, color=_MUTED),
                padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                bgcolor=_RULE,
                border_radius=4,
            ),
        ]
        if data.started_at is not None:
            relative_time = format_relative_time(data.started_at)
            meta_items.append(
                ft.Text(
                    relative_time,
                    size=11,
                    color=_MUTED,
                )
            )
        meta_items.append(
            ft.Text(
                format_duration(data.duration_ms),
                size=11,
                color=_MUTED,
            )
        )

        meta_row = ft.Row(
            controls=meta_items,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # 删除按钮（左下角，Q49）
        delete_btn = ft.TextButton(
            "删除",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_delete_click,
            style=ft.ButtonStyle(
                color=_DANGER,
                padding=ft.Padding(left=4, right=4, top=0, bottom=0),
            ),
        )

        # 错误信息（失败/中止时显示）
        error_row: list[ft.Control] = []
        if data.error_message:
            error_row.append(
                ft.Container(
                    content=ft.Text(
                        data.error_message,
                        size=11,
                        color=_DANGER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                    bgcolor="#fef2f2",
                    border_radius=4,
                )
            )

        # 底部行：删除按钮 + 空白填充
        footer_row = ft.Row(
            controls=[
                delete_btn,
                ft.Container(expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

        # 整个卡片内容
        content = ft.Column(
            controls=[
                name_row,
                meta_row,
                *error_row,
                footer_row,
            ],
            spacing=8,
        )

        super().__init__(
            content=content,
            padding=ft.Padding(left=12, right=12, top=10, bottom=8),
            bgcolor=_BG2,
            border_radius=10,
            border=ft.Border.all(1, _RULE),
            on_click=self._handle_card_click,
            on_hover=self._handle_hover,
        )

    # ---- 事件 ----

    def _handle_card_click(self, e: ft.ControlEvent) -> None:
        """卡片整体点击"""
        if self._on_click:
            self._on_click(self.card_data.log_id)

    def _handle_delete_click(self, e: ft.ControlEvent) -> None:
        """删除按钮点击（阻止冒泡，弹出二次确认）"""
        e.stop_propagation = True
        if not self._on_delete:
            return
        page = e.page
        if page is None:
            # 无 page 上下文（测试环境），直接执行
            self._on_delete(self.card_data.log_id)
            return

        task_name = self.card_data.task_name
        log_id = self.card_data.log_id

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
            if self._on_delete:
                self._on_delete(log_id)

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

    def _handle_hover(self, e: ft.ControlEvent) -> None:
        """鼠标悬停高亮"""
        if e.data:
            self.bgcolor = "#f9fafb"
        else:
            self.bgcolor = _BG2
        try:
            e.page.update()
        except Exception:
            pass


# ---- 工具函数 ----


def _to_status(value: str):
    """字符串转 ExecutionStatus 枚举"""
    from services.stats_service import ExecutionStatus

    try:
        return ExecutionStatus(value)
    except ValueError:
        return ExecutionStatus.SUCCESS


def _to_trigger(value: str):
    """字符串转 TriggerSource 枚举"""
    from services.stats_service import TriggerSource

    try:
        return TriggerSource(value)
    except ValueError:
        return TriggerSource.MANUAL
