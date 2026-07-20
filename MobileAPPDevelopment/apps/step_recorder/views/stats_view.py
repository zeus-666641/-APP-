"""统计视图（M4 模块）

按 PRD 第 7 章实现统计可视化：
- 汇总卡片（总执行次数/成功率/平均时长/任务数）
- 任务排行（Top 5 任务）
- 按天趋势（最近 7 天的执行次数）
- 按触发源分布

变更记录:
- Q37 后续：M4 在本次对话内完成（Q41 确认）
- Q5: 占位实现（M4 完成后接入真实数据）
- M5 接入后：从 log_service 加载真实执行记录
"""
from __future__ import annotations

import flet as ft

from services.stats_service import (
    DailyStats,
    ExecutionStatus,
    OverallStats,
    StatsService,
    TaskStats,
    TriggerSource,
    TriggerSourceStats,
)

# 配色
_ACCENT = "#2563eb"
_ACCENT_LIGHT = "#dbeafe"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"
_SUCCESS = "#10b981"
_DANGER = "#ef4444"
_WARNING = "#f59e0b"

# 触发源中文标签
_TRIGGER_LABELS = {
    TriggerSource.MANUAL: "手动触发",
    TriggerSource.TIMER: "定时触发",
    TriggerSource.INTERVAL: "间隔触发",
    TriggerSource.RANDOM: "随机触发",
}


class StatsView(ft.View):
    """统计视图

    Attributes:
        page: Flet 页面对象
        service: 统计服务（可注入用于测试）
    """

    def __init__(self, page: ft.Page, service: StatsService | None = None) -> None:
        self._page = page
        self._service = service or StatsService()

        # 计算 3 维统计
        self._overall = self._service.get_overall_stats()
        self._task_stats = self._service.get_stats_by_task()
        self._daily_stats = self._service.get_stats_by_day(days=7)
        self._trigger_stats = self._service.get_stats_by_trigger_source()
        self._top_tasks = self._service.get_top_tasks(limit=5)

        super().__init__(
            route="/stats",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                    ),
                    title=ft.Text("执行统计"),
                    bgcolor=_ACCENT,
                    color="white",
                ),
                ft.SafeArea(
                    content=self._build_content(),
                    expand=True,
                ),
            ],
            spacing=0,
        )

    def _build_content(self) -> ft.Control:
        """构建主内容：汇总卡片 + 任务排行 + 每日趋势 + 触发源"""
        return ft.Column(
            controls=[
                # section-title
                self._build_section_title("汇总统计", ""),
                # 汇总卡片网格
                self._build_overall_cards(),
                # section-title
                self._build_section_title("任务排行", f"Top {len(self._top_tasks)}"),
                # 任务排行列表
                self._build_top_tasks_list(),
                # section-title
                self._build_section_title("最近 7 天", f"{self._sum_daily()} 次"),
                # 每日趋势柱状图
                self._build_daily_chart(),
                # section-title
                self._build_section_title("按触发源", ""),
                # 触发源分布
                self._build_trigger_source_list(),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_section_title(self, title: str, right_text: str) -> ft.Control:
        """section-title（与 StepEditorView F9c 一致）"""
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
            padding=ft.Padding(left=16, right=16, top=8, bottom=4),
        )

    def _build_overall_cards(self) -> ft.Control:
        """汇总卡片网格（2x2）"""
        rate_percent = f"{self._overall.overall_success_rate * 100:.1f}%"
        avg_sec = self._overall.avg_duration_ms / 1000
        avg_text = f"{avg_sec:.1f}s" if avg_sec < 60 else f"{avg_sec / 60:.1f}min"

        cards = [
            self._build_stat_card(
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                icon_color=_ACCENT,
                title="总执行次数",
                value=str(self._overall.total_executions),
            ),
            self._build_stat_card(
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                icon_color=_SUCCESS,
                title="成功率",
                value=rate_percent,
            ),
            self._build_stat_card(
                icon=ft.Icons.TIMER_OUTLINED,
                icon_color=_WARNING,
                title="平均时长",
                value=avg_text,
            ),
            self._build_stat_card(
                icon=ft.Icons.LIST_ALT,
                icon_color=_ACCENT,
                title="任务数",
                value=str(self._overall.unique_tasks),
            ),
        ]

        # 2x2 网格
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=cards[0:2], spacing=8),
                    ft.Row(controls=cards[2:4], spacing=8),
                ],
                spacing=8,
            ),
            padding=ft.Padding(left=16, right=16, top=0, bottom=0),
        )

    def _build_stat_card(
        self, icon: str, icon_color: str, title: str, value: str
    ) -> ft.Control:
        """单个统计卡片"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon=icon, color=icon_color, size=20),
                        width=36,
                        height=36,
                        bgcolor=_ACCENT_LIGHT,
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                title,
                                size=11,
                                color=_MUTED,
                            ),
                            ft.Text(
                                value,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor=_BG2,
            border_radius=10,
            border=ft.Border.all(1, _RULE),
            expand=True,
        )

    def _build_top_tasks_list(self) -> ft.Control:
        """任务排行列表"""
        if not self._top_tasks:
            return ft.Container(
                content=ft.Text(
                    "暂无执行记录",
                    size=12,
                    color=_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            )

        rows: list[ft.Control] = []
        for i, stat in enumerate(self._top_tasks, 1):
            rate_percent = f"{stat.success_rate * 100:.0f}%"
            # 排名徽章
            rank_color = _ACCENT if i <= 3 else _MUTED
            rank = ft.Container(
                content=ft.Text(
                    str(i),
                    size=12,
                    color="white",
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=24,
                height=24,
                bgcolor=rank_color,
                border_radius=12,
                alignment=ft.Alignment.CENTER,
            )

            # 任务名 + 执行次数
            info = ft.Column(
                controls=[
                    ft.Text(
                        stat.task_name,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=_INK,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"执行 {stat.total_executions} 次 · 成功率 {rate_percent}",
                        size=11,
                        color=_MUTED,
                    ),
                ],
                spacing=2,
                expand=True,
            )

            # 成功率柱状条
            bar_width = int(stat.success_rate * 60)
            rate_bar = ft.Container(
                content=ft.Container(
                    width=bar_width,
                    height=6,
                    bgcolor=_SUCCESS if stat.success_rate >= 0.8 else _WARNING,
                    border_radius=3,
                ),
                width=60,
                height=6,
                bgcolor=_RULE,
                border_radius=3,
            )

            row = ft.Row(
                controls=[rank, info, rate_bar],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            rows.append(
                ft.Container(
                    content=row,
                    padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                    bgcolor=_BG2,
                    border_radius=8,
                    border=ft.Border.all(1, _RULE),
                )
            )

        return ft.Container(
            content=ft.Column(controls=rows, spacing=4),
            padding=ft.Padding(left=16, right=16, top=0, bottom=0),
        )

    def _build_daily_chart(self) -> ft.Control:
        """每日趋势柱状图（简易实现）"""
        max_count = max((d.total_executions for d in self._daily_stats), default=1)
        if max_count == 0:
            max_count = 1

        bars: list[ft.Control] = []
        for daily in self._daily_stats:
            height = int((daily.total_executions / max_count) * 100) + 4
            # 日期短格式 MM-DD
            date_short = daily.date[5:]  # YYYY-MM-DD -> MM-DD
            bar = ft.Column(
                controls=[
                    ft.Text(
                        str(daily.total_executions),
                        size=10,
                        color=_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        width=24,
                        height=height,
                        bgcolor=_ACCENT if daily.total_executions > 0 else _RULE,
                        border_radius=4,
                    ),
                    ft.Text(
                        date_short,
                        size=9,
                        color=_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                alignment=ft.MainAxisAlignment.END,
            )
            bars.append(bar)

        return ft.Container(
            content=ft.Row(
                controls=bars,
                spacing=4,
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=ft.Padding(left=16, right=16, top=8, bottom=16),
            bgcolor=_BG2,
            border_radius=10,
            border=ft.Border.all(1, _RULE),
            margin=ft.Margin(left=16, right=16, top=0, bottom=0),
        )

    def _build_trigger_source_list(self) -> ft.Control:
        """触发源分布列表"""
        total = sum(s.total_executions for s in self._trigger_stats)
        if total == 0:
            return ft.Container(
                content=ft.Text(
                    "暂无触发记录",
                    size=12,
                    color=_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            )

        rows: list[ft.Control] = []
        for stat in self._trigger_stats:
            label = _TRIGGER_LABELS[stat.trigger_source]
            percent = (stat.total_executions / total) * 100 if total > 0 else 0
            bar_width = int((stat.total_executions / total) * 120) if total > 0 else 0

            row = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            label,
                            size=12,
                            color=_INK,
                            width=80,
                        ),
                        ft.Container(
                            content=ft.Container(
                                width=bar_width,
                                height=8,
                                bgcolor=_ACCENT,
                                border_radius=4,
                            ),
                            width=120,
                            height=8,
                            bgcolor=_RULE,
                            border_radius=4,
                        ),
                        ft.Text(
                            f"{stat.total_executions} 次 ({percent:.0f}%)",
                            size=11,
                            color=_MUTED,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            )
            rows.append(row)

        return ft.Container(
            content=ft.Column(controls=rows, spacing=4),
            padding=ft.Padding(left=16, right=16, top=0, bottom=16),
        )

    def _sum_daily(self) -> int:
        """最近 7 天总执行次数"""
        return sum(d.total_executions for d in self._daily_stats)

    def _handle_back(self, e: ft.ControlEvent) -> None:
        """返回上一页"""
        try:
            self._page.go("/tasks")
        except Exception:
            pass
