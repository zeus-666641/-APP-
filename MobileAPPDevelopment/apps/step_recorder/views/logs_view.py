"""执行日志列表视图（M5）

按 PRD 第 8 章实现日志列表：
- 顶部搜索框（按任务名/日志ID 模糊匹配，Q49）
- 4 维过滤（状态/任务/触发源/时间范围，Q44）
- 分组切换（按日期/平铺，Q47）
- 列表卡片（LogCard，含左下角删除按钮，Q46/Q49）
- 空状态占位
- 点击卡片跳转详情 /logs/{id}（Q42）

变更记录:
- Q42: 详情用独立路由
- Q44: 4 维过滤
- Q46: 列表项字段
- Q47: 分组切换
- Q49: 搜索 + 单条删除（按钮在卡片左下角）
"""
from __future__ import annotations

from typing import Callable, Literal

import flet as ft

from models.log import GroupMode, LogFilter, TimeRangeKey
from services.log_service import LogService
from services.stats_service import ExecutionStatus, TriggerSource
from views.components.log_card import LogCard, LogCardData

# 配色
_ACCENT = "#2563eb"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"

# 选项中文标签
_STATUS_OPTIONS: list[tuple[ExecutionStatus, str]] = [
    (ExecutionStatus.SUCCESS, "成功"),
    (ExecutionStatus.FAILED, "失败"),
    (ExecutionStatus.ABORTED, "已中止"),
    (ExecutionStatus.RUNNING, "执行中"),
    (ExecutionStatus.SKIPPED, "已跳过"),
]

_TRIGGER_OPTIONS: list[tuple[TriggerSource, str]] = [
    (TriggerSource.MANUAL, "手动触发"),
    (TriggerSource.TIMER, "定时触发"),
    (TriggerSource.INTERVAL, "间隔触发"),
    (TriggerSource.RANDOM, "随机触发"),
]

_TIME_RANGE_OPTIONS: list[tuple[TimeRangeKey, str]] = [
    ("all", "全部"),
    ("1d", "最近 1 天"),
    ("7d", "最近 7 天"),
    ("30d", "最近 30 天"),
]


class LogsView(ft.View):
    """执行日志列表视图

    Attributes:
        page: Flet 页面对象
        service: 日志服务（可注入用于测试）
        on_navigate_detail: 详情跳转回调（参数：log_id）
    """

    def __init__(
        self,
        page: ft.Page,
        service: LogService | None = None,
        on_navigate_detail: Callable[[str], None] | None = None,
    ) -> None:
        self._page = page
        self._service = service or LogService()
        self._on_navigate_detail = on_navigate_detail

        # 当前过滤器状态
        self._filter = LogFilter()
        # 当前分组模式
        self._group_mode: GroupMode = "date"
        # 任务过滤候选列表
        self._tasks = self._service.get_unique_tasks()

        # 构建组件树
        self._search_field = ft.TextField(
            hint_text="搜索任务名或日志 ID",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._handle_search_change,
            dense=True,
            border_radius=8,
        )

        self._status_dropdown = ft.Dropdown(
            label="状态",
            value="",
            options=[
                ft.dropdown.Option(key="", text="全部状态"),
                *[
                    ft.dropdown.Option(key=s.value, text=label)
                    for s, label in _STATUS_OPTIONS
                ],
            ],
            on_select=self._handle_status_change,
            dense=True,
        )

        self._task_dropdown = ft.Dropdown(
            label="任务",
            value="",
            options=[
                ft.dropdown.Option(key="", text="全部任务"),
                *[
                    ft.dropdown.Option(key=task_id, text=name)
                    for task_id, name, _ in self._tasks
                ],
            ],
            on_select=self._handle_task_change,
            dense=True,
        )

        self._trigger_dropdown = ft.Dropdown(
            label="触发源",
            value="",
            options=[
                ft.dropdown.Option(key="", text="全部触发源"),
                *[
                    ft.dropdown.Option(key=t.value, text=label)
                    for t, label in _TRIGGER_OPTIONS
                ],
            ],
            on_select=self._handle_trigger_change,
            dense=True,
        )

        self._time_dropdown = ft.Dropdown(
            label="时间范围",
            value="all",
            options=[
                ft.dropdown.Option(key=k, text=label)
                for k, label in _TIME_RANGE_OPTIONS
            ],
            on_select=self._handle_time_range_change,
            dense=True,
        )

        self._group_mode_segmented = ft.SegmentedButton(
            selected=["date" if self._group_mode == "date" else "flat"],
            segments=[
                ft.Segment(value="date", label=ft.Text("按日期", size=12)),
                ft.Segment(value="flat", label=ft.Text("平铺", size=12)),
            ],
            on_change=self._handle_group_mode_change,
            allow_multiple_selection=False,
            allow_empty_selection=False,
        )

        # section-title + 计数（动态更新）
        self._section_count = ft.Text("共 0 项", size=12, color=_MUTED)
        self._section_title = ft.Row(
            controls=[
                ft.Text(
                    "执行日志",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=_INK,
                ),
                self._section_count,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 日志列表容器
        self._list_container = ft.Column(
            controls=[],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            route="/logs",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                    ),
                    title=ft.Text("执行日志"),
                    bgcolor=_ACCENT,
                    color="white",
                ),
                ft.SafeArea(
                    content=ft.Column(
                        controls=[
                            # 搜索框
                            ft.Container(
                                content=self._search_field,
                                padding=ft.Padding(left=16, right=16, top=8, bottom=4),
                            ),
                            # 4 维过滤
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                self._status_dropdown,
                                                self._trigger_dropdown,
                                            ],
                                            spacing=8,
                                        ),
                                        ft.Row(
                                            controls=[
                                                self._task_dropdown,
                                                self._time_dropdown,
                                            ],
                                            spacing=8,
                                        ),
                                    ],
                                    spacing=4,
                                ),
                                padding=ft.Padding(left=16, right=16, top=0, bottom=4),
                            ),
                            # 分组切换
                            ft.Container(
                                content=self._group_mode_segmented,
                                padding=ft.Padding(left=16, right=16, top=0, bottom=4),
                            ),
                            # section-title
                            ft.Container(
                                content=self._section_title,
                                padding=ft.Padding(left=16, right=16, top=4, bottom=4),
                            ),
                            # 列表
                            ft.Container(
                                content=self._list_container,
                                padding=ft.Padding(left=16, right=16, top=0, bottom=16),
                                expand=True,
                            ),
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        )

        # 初始渲染
        self._refresh_list()

    # ---- 渲染 ----

    def _refresh_list(self) -> None:
        """刷新日志列表（重新过滤 + 分组 + 渲染）"""
        filtered = self._service.filter(self._filter)
        groups = self._service.group(filtered, mode=self._group_mode)

        # 更新计数
        self._section_count.value = f"共 {len(filtered)} 项"

        controls: list[ft.Control] = []
        if not filtered:
            controls.append(self._build_empty_state())
        else:
            for group in groups:
                # 分组标题（flat 模式只显示一个"全部日志"标题，可隐藏）
                if self._group_mode == "date" or len(groups) > 1:
                    controls.append(self._build_group_header(group))
                # 组内卡片
                for log in group.logs:
                    card = LogCard(
                        data=LogCardData.from_log(log),
                        on_click=self._handle_card_click,
                        on_delete=self._handle_delete,
                    )
                    controls.append(card)

        self._list_container.controls = controls
        try:
            self._list_container.update()
        except Exception:
            pass
        try:
            self._section_count.update()
        except Exception:
            pass

    def _build_empty_state(self) -> ft.Control:
        """空状态占位"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon=ft.Icons.INBOX_OUTLINED,
                        color=_MUTED,
                        size=48,
                    ),
                    ft.Text(
                        "暂无日志",
                        size=14,
                        color=_MUTED,
                    ),
                    ft.Text(
                        "执行任务后，日志会出现在这里",
                        size=12,
                        color=_MUTED,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=ft.Padding(left=16, right=16, top=40, bottom=40),
        )

    def _build_group_header(self, group) -> ft.Control:
        """分组标题（按日期时显示日期标签 + 该组数量）"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        group.label,
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=_MUTED,
                    ),
                    ft.Text(
                        f"{len(group.logs)} 项",
                        size=11,
                        color=_MUTED,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=4, right=4, top=8, bottom=4),
        )

    # ---- 事件处理 ----

    def _handle_search_change(self, e: ft.ControlEvent) -> None:
        """搜索框输入"""
        self._filter.keyword = str(e.control.value or "")
        self._refresh_list()

    def _handle_status_change(self, e: ft.ControlEvent) -> None:
        """状态过滤"""
        value = str(e.control.value or "")
        if value:
            try:
                self._filter.status = ExecutionStatus(value)
            except ValueError:
                self._filter.status = None
        else:
            self._filter.status = None
        self._refresh_list()

    def _handle_task_change(self, e: ft.ControlEvent) -> None:
        """任务过滤"""
        value = str(e.control.value or "")
        self._filter.task_id = value if value else None
        self._refresh_list()

    def _handle_trigger_change(self, e: ft.ControlEvent) -> None:
        """触发源过滤"""
        value = str(e.control.value or "")
        if value:
            try:
                self._filter.trigger_source = TriggerSource(value)
            except ValueError:
                self._filter.trigger_source = None
        else:
            self._filter.trigger_source = None
        self._refresh_list()

    def _handle_time_range_change(self, e: ft.ControlEvent) -> None:
        """时间范围过滤"""
        value = str(e.control.value or "all")
        try:
            self._filter.time_range = value  # type: ignore[assignment]
        except (TypeError, ValueError):
            self._filter.time_range = "all"
        self._refresh_list()

    def _handle_group_mode_change(self, e: ft.ControlEvent) -> None:
        """分组模式切换"""
        selected = e.control.selected
        if "flat" in selected:
            self._group_mode = "flat"
        else:
            self._group_mode = "date"
        self._refresh_list()

    def _handle_card_click(self, log_id: str) -> None:
        """点击卡片 → 跳转详情"""
        if self._on_navigate_detail:
            self._on_navigate_detail(log_id)
        else:
            try:
                self._page.go(f"/logs/{log_id}")
            except Exception:
                pass

    def _handle_delete(self, log_id: str) -> None:
        """删除日志"""
        self._service.delete(log_id)
        self._refresh_list()

    def _handle_back(self, e: ft.ControlEvent | None = None) -> None:
        """返回上一页"""
        try:
            self._page.go("/tasks")
        except Exception:
            pass
