"""任务树组件

M1 模块的核心 UI 组件，支持 Q39 决策的两种嵌套模式：
- tree: 树形展开 + 缩进（默认）
- breadcrumb: 面包屑导航

变更记录:
- Q38: TaskCard 用 PRD 原样样式（任务名 + 图标 + 状态点 + 启用开关 + 执行按钮）
- Q39: 双模式 nest_mode 切换，默认 tree
- Q25: 仅同级拖拽排序（嵌套不通过拖拽实现）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

import flet as ft

from models.task import TaskNode, TaskStatus

# 配色（与 StepCard 一致，参照 PRD HTML :root CSS 变量）
_ACCENT = "#2563eb"
_ACCENT_LIGHT = "#dbeafe"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_DANGER = "#ef4444"
_SUCCESS = "#10b981"

# 状态色板
STATUS_COLORS: dict[TaskStatus, str] = {
    TaskStatus.IDLE: _MUTED,
    TaskStatus.RUNNING: _ACCENT,
    TaskStatus.PAUSED: "#f59e0b",
    TaskStatus.ERROR: _DANGER,
    TaskStatus.DISABLED: "#94a3b8",
}

STATUS_LABELS: dict[TaskStatus, str] = {
    TaskStatus.IDLE: "空闲",
    TaskStatus.RUNNING: "执行中",
    TaskStatus.PAUSED: "已暂停",
    TaskStatus.ERROR: "出错",
    TaskStatus.DISABLED: "已禁用",
}

# 缩进宽度（每层 24px，与 PRD .tree-item 一致）
_INDENT_STEP = 24
# 卡片固定宽度
_CARD_WIDTH = 360
# 操作区固定宽度
_ACTIONS_WIDTH = 130


@dataclass
class TaskCardData:
    """TaskCard 数据模型（与 Task 解耦，方便 mock 和测试）

    Attributes:
        task_id: 任务 ID
        name: 任务名
        icon: Material icon 名称
        status: 任务状态
        enabled: 是否启用
        sort_order: 同级排序
        category: 任务分类（用于分组显示）
        children: 子任务数据列表
        parent_path: 父任务名称链（面包屑模式用，如 ["父任务", "祖父任务"]）
    """

    task_id: str
    name: str
    icon: str = "play_arrow"
    status: TaskStatus = TaskStatus.IDLE
    enabled: bool = True
    sort_order: int = 0
    category: str = "default"
    children: list["TaskCardData"] = None
    parent_path: list[str] = None

    def __post_init__(self) -> None:
        if self.children is None:
            self.children = []
        if self.parent_path is None:
            self.parent_path = []


NestMode = Literal["tree", "breadcrumb"]


class TaskCard(ft.Container):
    """单个任务卡片（PRD 原样样式，Q38 决策）

    布局：[图标块] [任务名 + 状态点] [执行按钮 + 启用开关 + 展开按钮]

    Attributes:
        data: 卡片数据
        depth: 在树中的深度（用于缩进）
        on_toggle_enabled: 启用/禁用回调
        on_execute: 执行按钮回调
        on_click: 点击卡片回调（进详情）
        on_toggle_expand: 展开/折叠子任务回调
        has_children: 是否有子任务
        is_expanded: 当前是否展开
    """

    def __init__(
        self,
        data: TaskCardData,
        depth: int = 0,
        on_toggle_enabled: Callable[[str, bool], None] | None = None,
        on_execute: Callable[[str], None] | None = None,
        on_click: Callable[[str], None] | None = None,
        on_toggle_expand: Callable[[str], None] | None = None,
        has_children: bool = False,
        is_expanded: bool = False,
    ) -> None:
        self.data = data
        self._depth = depth
        self._on_toggle_enabled = on_toggle_enabled
        self._on_execute = on_execute
        self._on_click = on_click
        self._on_toggle_expand = on_toggle_expand
        self._has_children = has_children
        self._is_expanded = is_expanded

        status_color = STATUS_COLORS[data.status]
        status_label = STATUS_LABELS[data.status]

        # 任务图标块（与 StepCard step_icon 一致，36x36 圆角矩形）
        icon_box = ft.Container(
            content=ft.Icon(
                icon=data.icon,
                color=_ACCENT,
                size=18,
            ),
            width=36,
            height=36,
            bgcolor=_ACCENT_LIGHT,
            border_radius=8,
            alignment=ft.Alignment.CENTER,
        )

        # 任务名 + 状态点（PRD 原样：状态点 8x8 圆点 + 状态文本）
        name_row = ft.Row(
            controls=[
                ft.Text(
                    data.name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=_INK if data.enabled else _MUTED,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    expand=True,
                ),
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=status_color,
                    border_radius=4,
                ),
                ft.Text(
                    status_label,
                    size=10,
                    color=status_color,
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        info_column = ft.Column(
            controls=[name_row],
            spacing=2,
            expand=True,
        )

        # 启用开关
        toggle = ft.Switch(
            value=data.enabled,
            on_change=self._handle_toggle,
            scale=0.8,
        )

        # 执行按钮（PLAY_CIRCLE_OUTLINE 与 StepCard execute 一致）
        execute_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            icon_color=_ACCENT,
            icon_size=14,
            tooltip="执行此任务",
            on_click=self._handle_execute,
        )

        # 展开/折叠按钮（仅有子任务时显示）
        if has_children:
            expand_btn = ft.IconButton(
                icon=(
                    ft.Icons.KEYBOARD_ARROW_UP
                    if is_expanded
                    else ft.Icons.KEYBOARD_ARROW_DOWN
                ),
                icon_color=_MUTED,
                icon_size=14,
                tooltip="展开/折叠子任务",
                on_click=self._handle_toggle_expand,
            )
            actions_controls = [execute_btn, toggle, expand_btn]
        else:
            actions_controls = [execute_btn, toggle]

        actions_row = ft.Row(
            controls=actions_controls,
            spacing=2,
            width=_ACTIONS_WIDTH,
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 主行
        main_row = ft.Row(
            controls=[icon_box, info_column, actions_row],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        # 卡片容器（带缩进 padding，树形模式用）
        super().__init__(
            content=main_row,
            width=_CARD_WIDTH,
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            bgcolor=_BG2,
            border_radius=10,
            border=ft.Border.all(1, _RULE),
            on_click=self._handle_click,
        )

    def _handle_toggle(self, e: ft.ControlEvent) -> None:
        e.stop_propagation = True
        new_value = bool(e.control.value)
        self.data.enabled = new_value
        if self._on_toggle_enabled:
            self._on_toggle_enabled(self.data.task_id, new_value)

    def _handle_execute(self, e: ft.ControlEvent) -> None:
        e.stop_propagation = True
        if self._on_execute:
            self._on_execute(self.data.task_id)

    def _handle_click(self, e: ft.ControlEvent) -> None:
        e.stop_propagation = True
        if self._on_click:
            self._on_click(self.data.task_id)

    def _handle_toggle_expand(self, e: ft.ControlEvent) -> None:
        e.stop_propagation = True
        if self._on_toggle_expand:
            self._on_toggle_expand(self.data.task_id)


class TaskTree(ft.Column):
    """任务树组件（支持 tree / breadcrumb 两种模式，Q39 决策）

    tree 模式：
    - 根任务 → 子任务 → 孙任务，缩进显示
    - 父任务可展开/折叠

    breadcrumb 模式：
    - 同级任务列表（无缩进）
    - 点击父任务进详情，顶部显示面包屑路径
    - 子任务列表通过 on_navigate 回调切换

    Attributes:
        nodes: 任务节点列表（根节点）
        nest_mode: 嵌套模式（默认 "tree"）
        on_toggle_enabled: 启用/禁用回调
        on_execute: 执行回调
        on_click: 点击任务回调
        on_navigate: 面包屑模式下切换层级回调
        expanded_ids: 当前展开的任务 ID 集合（tree 模式）
    """

    def __init__(
        self,
        nodes: list[TaskNode],
        nest_mode: NestMode = "tree",
        on_toggle_enabled: Callable[[str, bool], None] | None = None,
        on_execute: Callable[[str], None] | None = None,
        on_click: Callable[[str], None] | None = None,
        on_navigate: Callable[[str | None], None] | None = None,
        expanded_ids: set[str] | None = None,
        current_parent_id: str | None = None,
    ) -> None:
        self._nodes = nodes
        self._nest_mode = nest_mode
        self._on_toggle_enabled = on_toggle_enabled
        self._on_execute = on_execute
        self._on_click = on_click
        self._on_navigate = on_navigate
        self._expanded_ids = expanded_ids or set()
        self._current_parent_id = current_parent_id

        super().__init__(
            controls=self._render(),
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

    def _render(self) -> list[ft.Control]:
        """根据 nest_mode 渲染当前视图"""
        if self._nest_mode == "tree":
            return self._render_tree_mode()
        else:
            return self._render_breadcrumb_mode()

    def _render_tree_mode(self) -> list[ft.Control]:
        """树形模式：递归渲染所有展开的节点"""
        controls: list[ft.Control] = []

        def render_node(node: TaskNode, depth: int) -> None:
            data = TaskCardData(
                task_id=node.task.id,
                name=node.task.name,
                icon=node.task.icon,
                status=TaskStatus.IDLE,
                enabled=node.task.enabled,
                sort_order=node.task.sort_order,
                category=node.task.category.value,
            )
            has_children = bool(node.children)
            is_expanded = node.task.id in self._expanded_ids

            # 缩进容器
            card = TaskCard(
                data=data,
                depth=depth,
                on_toggle_enabled=self._on_toggle_enabled,
                on_execute=self._on_execute,
                on_click=self._on_click,
                on_toggle_expand=self._handle_toggle_expand,
                has_children=has_children,
                is_expanded=is_expanded,
            )
            indent_container = ft.Container(
                content=card,
                padding=ft.Padding(left=depth * _INDENT_STEP, right=0, top=0, bottom=0),
            )
            controls.append(indent_container)

            # 子任务（仅在展开时显示）
            if has_children and is_expanded:
                for child in node.children:
                    render_node(child, depth + 1)

        for root in self._nodes:
            render_node(root, 0)

        return controls

    def _render_breadcrumb_mode(self) -> list[ft.Control]:
        """面包屑模式：显示当前层级的同级任务"""
        controls: list[ft.Control] = []

        # 面包屑导航条
        breadcrumb = self._build_breadcrumb()
        if breadcrumb is not None:
            controls.append(breadcrumb)

        # 当前层级的任务列表
        if self._current_parent_id is None:
            siblings = self._nodes
        else:
            parent_node = None
            for root in self._nodes:
                found = root.find(self._current_parent_id)
                if found is not None:
                    parent_node = found
                    break
            siblings = parent_node.children if parent_node else []

        for node in siblings:
            data = TaskCardData(
                task_id=node.task.id,
                name=node.task.name,
                icon=node.task.icon,
                status=TaskStatus.IDLE,
                enabled=node.task.enabled,
                sort_order=node.task.sort_order,
                category=node.task.category.value,
            )
            card = TaskCard(
                data=data,
                depth=0,
                on_toggle_enabled=self._on_toggle_enabled,
                on_execute=self._on_execute,
                on_click=self._handle_card_click_breadcrumb,
                on_toggle_expand=None,
                has_children=bool(node.children),
                is_expanded=False,
            )
            controls.append(card)

        return controls

    def _build_breadcrumb(self) -> ft.Control | None:
        """构建面包屑导航条（仅 breadcrumb 模式）"""
        if self._current_parent_id is None:
            # 根层级，显示"全部任务"
            return ft.Row(
                controls=[
                    ft.Text(
                        "全部任务",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=_INK,
                    ),
                ],
            )

        # 查找父任务链
        path = self._find_path(self._current_parent_id)
        if not path:
            return None

        crumbs: list[ft.Control] = [
            ft.Button(
                "全部任务",
                on_click=lambda e: self._handle_navigate(None),
                style=ft.ButtonStyle(color=_ACCENT),
            ),
        ]
        for i, node in enumerate(path):
            is_last = i == len(path) - 1
            crumbs.append(ft.Text(" / ", size=12, color=_MUTED))
            if is_last:
                crumbs.append(
                    ft.Text(
                        node.task.name,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=_INK,
                    )
                )
            else:
                crumbs.append(
                    ft.Button(
                        node.task.name,
                        on_click=lambda e, tid=node.task.id: self._handle_navigate(tid),
                        style=ft.ButtonStyle(color=_ACCENT),
                    )
                )

        return ft.Row(controls=crumbs, wrap=True)

    def _find_path(self, task_id: str) -> list[TaskNode]:
        """查找从根到指定节点的路径"""
        for root in self._nodes:
            path = self._find_path_recursive(root, task_id, [])
            if path:
                return path
        return []

    def _find_path_recursive(
        self, node: TaskNode, target_id: str, acc: list[TaskNode]
    ) -> list[TaskNode] | None:
        acc = acc + [node]
        if node.task.id == target_id:
            return acc
        for child in node.children:
            result = self._find_path_recursive(child, target_id, acc)
            if result:
                return result
        return None

    def _handle_toggle_expand(self, task_id: str) -> None:
        """切换展开/折叠状态（tree 模式）"""
        if task_id in self._expanded_ids:
            self._expanded_ids.discard(task_id)
        else:
            self._expanded_ids.add(task_id)
        self.controls = self._render()
        try:
            self.update()
        except Exception:
            pass

    def _handle_card_click_breadcrumb(self, task_id: str) -> None:
        """breadcrumb 模式下点击任务卡片"""
        # 检查是否有子任务，有则进入下一层；无则触发 on_click
        for root in self._nodes:
            node = root.find(task_id)
            if node and node.children:
                self._handle_navigate(task_id)
                return
        if self._on_click:
            self._on_click(task_id)

    def _handle_navigate(self, target_id: str | None) -> None:
        """面包屑导航切换层级"""
        self._current_parent_id = target_id
        self.controls = self._render()
        try:
            self.update()
        except Exception:
            pass
        if self._on_navigate:
            self._on_navigate(target_id)
