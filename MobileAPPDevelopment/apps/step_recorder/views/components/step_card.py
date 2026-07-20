"""步骤卡片组件

PRD 原样样式（参照 步骤记录器v1.0 HTML phone-screen 截图）：
- 左侧：序号圆圈（accent 主色 + 白字）
- 然后：步骤图标（36x36 圆角矩形 accent-light 背景 + Material icon）→ F8 新增
- 中间：步骤名 + 参数摘要 + 状态徽章
- 右侧：执行按钮 + 启用开关 + 删除按钮
- 占位步骤（NOT_IMPLEMENTED）：视觉与正常一致，但徽章置灰

B2 修复：
- StepCard.on_click 不再设置在 Container 上，改为只在 step_num 上
- 避免 Switch/Delete 按钮点击触发整卡 on_click 编辑事件
- 同时为 Switch 和 Delete 添加 stop_propagation 防止冒泡

F2 修复：
- 卡片固定宽度（width=360），不因名字长短变化
- info_column 的 Text max_lines=1 + ellipsis 保证不撑开

F5 新增：
- 步骤卡片添加执行按钮（play_circle 图标），on_execute 回调

F8 改进（参考 HTML PRD）：
- 序号圆圈后增加 36x36 步骤图标块（accent-light 背景 + Material icon）
- spacing 从 8 改为 12（与 HTML gap 一致）
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

# 固定卡片宽度（F2：不因名字长短变化）
_CARD_WIDTH = 360
# 按钮区固定宽度
_ACTIONS_WIDTH = 130
# 步骤图标块尺寸（F8：与 HTML PRD .step-icon 一致）
_ICON_BOX_SIZE = 36
_ICON_BOX_RADIUS = 8
# 配色（与 HTML PRD :root CSS 变量对齐）
_ACCENT = "#2563eb"
_ACCENT_LIGHT = "#dbeafe"  # HTML var(--accent-light)
_RULE = "#e5e7eb"
_BG2 = "#ffffff"
_MUTED = "#6b7280"
_DANGER = "#ef4444"


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
    children: list["StepCardData"] = None  # F4：子步骤列表（嵌套），默认 None 表示不支持子步骤
    # F6：触发器配置（M3 触发器系统接入时使用）
    trigger_date: str | None = None    # 指定触发日期（ISO 格式字符串，如 "2026-07-20T14:30:00"）
    trigger_count: int = 1             # 触发次数（默认 1 次；0 表示无限循环；负数视为 1）

    def __post_init__(self) -> None:
        """F4：children 默认 None（不支持子步骤），赋值为 [] 后表示支持但无子步骤"""
        if self.children is None:
            self.children = []
        # F6：trigger_count 负数视为 1
        if self.trigger_count < 0:
            self.trigger_count = 1


class StepCard(ft.Container):
    """单个步骤卡片

    Attributes:
        data: 卡片数据
        on_toggle_enabled: 启用/禁用回调
        on_delete: 删除回调
        on_click: 点击卡片回调（弹出编辑）—— 仅在序号圆圈上触发
        on_execute: 执行按钮回调（F5）
        on_add_child: 添加子步骤回调（F4）
    """

    def __init__(
        self,
        data: StepCardData,
        on_toggle_enabled: Callable[[str, bool], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
        on_click: Callable[[str], None] | None = None,
        on_execute: Callable[[str], None] | None = None,
        on_add_child: Callable[[str], None] | None = None,  # F4 新增
    ) -> None:
        self.data = data
        self._on_toggle_enabled = on_toggle_enabled
        self._on_delete = on_delete
        self._on_click = on_click
        self._on_execute = on_execute
        self._on_add_child = on_add_child  # F4
        # F4：展开/折叠状态（默认折叠）
        self._children_expanded = False

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

        # 序号圆圈（点击触发编辑；其余区域不触发）
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
            bgcolor=_ACCENT,  # accent 主色
            border_radius=14,
            alignment=ft.Alignment.CENTER,
            on_click=self._handle_click,
            tooltip="点击编辑",
        )

        # 步骤图标块（F8：与 HTML PRD .step-icon 一致）
        # 36x36 圆角矩形，accent-light 背景 + Material icon
        # 注意：Flet 0.86 Icon 构造参数是 `icon`（字符串或 ft.Icons 枚举），不是 `name`
        step_icon = ft.Container(
            content=ft.Icon(
                icon=meta.icon,
                color=_ACCENT,
                size=18,
            ),
            width=_ICON_BOX_SIZE,
            height=_ICON_BOX_SIZE,
            bgcolor=_ACCENT_LIGHT,
            border_radius=_ICON_BOX_RADIUS,
            alignment=ft.Alignment.CENTER,
        )

        # 步骤名 + 参数摘要 + 状态徽章（F2: 固定宽度，max_lines=1）
        params_summary = self._format_params_summary(data.params)
        # F6：触发器信息（只在配置了触发日期或非默认触发次数时显示）
        trigger_info = self._format_trigger_info(data.trigger_date, data.trigger_count)
        info_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            data.name_zh or meta.name_zh,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color="#1a1a2e",
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
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
                    color=_MUTED,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ) if params_summary else ft.Container(height=0),
                ft.Text(
                    trigger_info,
                    size=11,
                    color=_ACCENT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    weight=ft.FontWeight.W_500,
                ) if trigger_info else ft.Container(height=0),
            ],
            spacing=2,
            expand=True,
        )

        # 启用开关（B2：阻止冒泡）
        toggle = ft.Switch(
            value=data.enabled,
            on_change=self._handle_toggle,
            scale=0.8,
        )

        # 执行按钮（F5 新增，F9d：22→14 与其他 step-actions 图标统一）
        execute_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=_ACCENT,
            icon_size=14,
            tooltip="执行此步骤",
            on_click=self._handle_execute,
        )

        # 删除按钮（B2：阻止冒泡，F9d：图标 18→14 与 PRD .step-actions 一致）
        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=_DANGER,
            icon_size=14,
            tooltip="删除",
            on_click=self._handle_delete,
        )

        # 右侧按钮区（固定宽度，F2）
        actions_row = ft.Row(
            controls=[execute_btn, toggle, delete_btn],
            spacing=2,
            width=_ACTIONS_WIDTH,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 主行（F2 固定宽度，F8 spacing=12）
        main_row = ft.Row(
            controls=[
                step_num,
                step_icon,
                info_column,
                actions_row,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        # F4：子步骤区（只在有 children 或支持添加子步骤时显示）
        has_children = bool(data.children)
        can_add_child = on_add_child is not None
        children_section: ft.Control
        if has_children or can_add_child:
            # 子步骤标题行：[展开按钮] "子步骤 (N)" [+ 添加子步骤按钮]
            # F9d：操作图标 18→14 与 PRD .step-actions 一致
            expand_btn = ft.IconButton(
                icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                icon_color=_MUTED,
                icon_size=14,
                tooltip="展开/折叠子步骤",
                on_click=self._handle_toggle_expand,
            )
            children_count_text = ft.Text(
                f"子步骤 ({len(data.children)})",
                size=12,
                color=_MUTED,
                weight=ft.FontWeight.W_500,
            )
            add_child_btn = ft.IconButton(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                icon_color=_ACCENT,
                icon_size=14,
                tooltip="添加子步骤",
                on_click=self._handle_add_child,
            )
            children_header = ft.Row(
                controls=[expand_btn, children_count_text, add_child_btn],
                spacing=4,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            # 子步骤列表（默认折叠）
            self._children_list = ft.Column(
                controls=[
                    self._build_child_view(i, child)
                    for i, child in enumerate(data.children, 1)
                ],
                spacing=4,
                visible=False,  # 默认折叠
            )
            # 缩进子步骤区（左侧 padding 表示层级）
            children_section = ft.Container(
                content=ft.Column(
                    controls=[children_header, self._children_list],
                    spacing=4,
                ),
                padding=ft.Padding(left=44, right=0, top=4, bottom=4),
            )
        else:
            self._children_list = None
            children_section = ft.Container(width=0, height=0)

        # 整体容器（F2 固定宽度，F4 Column 包含主行 + 子步骤区）
        # 注意：on_click 不设置在 Container 上，避免子控件事件冒泡触发编辑
        super().__init__(
            content=ft.Column(
                controls=[main_row, children_section],
                spacing=0,
            ),
            width=_CARD_WIDTH,
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor=_BG2,
            border_radius=10,
            border=ft.Border.all(1, _RULE),
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

    @staticmethod
    def _format_trigger_info(trigger_date: str | None, trigger_count: int) -> str:
        """F6：格式化触发器信息（只在非默认时显示）

        Args:
            trigger_date: ISO 格式日期字符串（如 "2026-07-20T14:30:00"）
            trigger_count: 触发次数（1=默认不显示；0=无限循环；>1=指定次数）

        Returns:
            格式化后的触发器信息字符串（空字符串表示不显示）
        """
        parts: list[str] = []
        if trigger_date:
            # 简化显示：取日期和时间部分（去掉秒）
            try:
                # ISO 字符串切分："2026-07-20T14:30:00" → "2026-07-20 14:30"
                date_part = trigger_date.split("T")[0]
                time_part = trigger_date.split("T")[1][:5] if "T" in trigger_date else ""
                if time_part:
                    parts.append(f"📅 {date_part} {time_part}")
                else:
                    parts.append(f"📅 {date_part}")
            except Exception:
                parts.append(f"📅 {trigger_date}")
        if trigger_count == 0:
            parts.append("🔁 无限循环")
        elif trigger_count > 1:
            parts.append(f"🔁 ×{trigger_count}")
        return " · ".join(parts)

    # ---- F4：子步骤处理 ----

    def _build_child_view(self, index: int, child: "StepCardData") -> ft.Row:
        """渲染子步骤的简化视图（序号 + 名称 + 删除按钮）

        简化版：子步骤不嵌套显示自己的 children（避免无限嵌套渲染）
        完整嵌套 UI 留到 M1 任务管理实现。
        """
        return ft.Row(
            controls=[
                ft.Text(
                    f"{index}.",
                    size=12,
                    color=_MUTED,
                    width=20,
                ),
                ft.Text(
                    child.name_zh,
                    size=12,
                    color="#1a1a2e",
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    expand=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=_DANGER,
                    icon_size=14,
                    tooltip="删除子步骤",
                    on_click=lambda e, cid=child.step_id: self._handle_delete_child(cid),
                ),
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _handle_toggle_expand(self, e: ft.ControlEvent) -> None:
        """F4：展开/折叠子步骤列表"""
        e.stop_propagation = True
        if self._children_list is None:
            return
        self._children_expanded = not self._children_expanded
        self._children_list.visible = self._children_expanded
        # 切换按钮图标
        if hasattr(e.control, "icon"):
            e.control.icon = (
                ft.Icons.KEYBOARD_ARROW_UP
                if self._children_expanded
                else ft.Icons.KEYBOARD_ARROW_DOWN
            )
        try:
            self.update()
        except Exception:
            pass

    def _handle_add_child(self, e: ft.ControlEvent) -> None:
        """F4：添加子步骤（触发 on_add_child 回调）"""
        e.stop_propagation = True
        if self._on_add_child:
            self._on_add_child(self.data.step_id)

    def _handle_delete_child(self, child_id: str) -> None:
        """F4：删除子步骤（直接修改 data.children，触发刷新）

        简化版：直接从 data.children 移除，外部不感知。
        如果需要外部感知（如持久化），可在 StepCard 添加 on_delete_child 回调。
        """
        if self.data.children:
            self.data.children = [
                c for c in self.data.children if c.step_id != child_id
            ]
            # 重新渲染子步骤列表
            if self._children_list is not None:
                self._children_list.controls = [
                    self._build_child_view(i, child)
                    for i, child in enumerate(self.data.children, 1)
                ]
                try:
                    self.update()
                except Exception:
                    pass

    def _handle_toggle(self, e: ft.ControlEvent) -> None:
        """启用/禁用切换（阻止冒泡，避免触发卡片 on_click）"""
        e.stop_propagation = True
        new_value = bool(e.control.value)
        self.data.enabled = new_value
        if self._on_toggle_enabled:
            self._on_toggle_enabled(self.data.step_id, new_value)

    def _handle_delete(self, e: ft.ControlEvent) -> None:
        """删除点击（阻止冒泡）

        F9b：弹出 AlertDialog 二次确认，避免误删。
        - 用户点击「确认删除」→ 调用 self._on_delete(step_id)
        - 用户点击「取消」或关闭对话框 → 不删除
        """
        e.stop_propagation = True
        if not self._on_delete:
            return
        page = e.page
        if page is None:
            # 无 page 上下文（如测试环境），直接执行删除
            self._on_delete(self.data.step_id)
            return

        step_name = self.data.name_zh or self.data.step_type.value

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
                self._on_delete(self.data.step_id)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("确认删除"),
            content=ft.Text(
                f"确定要删除步骤「{step_name}」吗？此操作不可撤销。"
            ),
            actions=[
                ft.Button("取消", on_click=_close_dialog),
                ft.Button(
                    "确认删除",
                    on_click=_confirm_delete,
                    bgcolor="#ef4444",
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

    def _handle_execute(self, e: ft.ControlEvent) -> None:
        """执行按钮点击（阻止冒泡）"""
        e.stop_propagation = True
        if self._on_execute:
            self._on_execute(self.data.step_id)

    def _handle_click(self, e: ft.ControlEvent) -> None:
        """整卡点击（只在序号圆圈上设置，事件不冒泡）"""
        e.stop_propagation = True
        if self._on_click:
            self._on_click(self.data.step_id)


def render_step_cards(
    steps: list[StepCardData],
    on_toggle_enabled: Callable[[str, bool], None] | None = None,
    on_delete: Callable[[str], None] | None = None,
    on_click: Callable[[str], None] | None = None,
    on_execute: Callable[[str], None] | None = None,
) -> list[StepCard]:
    """批量渲染步骤卡片列表

    Args:
        steps: 卡片数据列表
        on_toggle_enabled/on_delete/on_click/on_execute: 回调（每个卡片共用）

    Returns:
        StepCard 控件列表（用于 ListView.controls）
    """
    return [
        StepCard(
            data=s,
            on_toggle_enabled=on_toggle_enabled,
            on_delete=on_delete,
            on_click=on_click,
            on_execute=on_execute,
        )
        for s in steps
    ]
