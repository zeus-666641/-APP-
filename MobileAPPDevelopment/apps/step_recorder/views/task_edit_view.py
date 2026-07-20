"""任务编辑视图（M1-T1.3）

抽屉式编辑界面（参照 StepEditorView 的设计语言）：
- 任务名输入
- 描述输入
- 图标选择（常用 Material icons 网格）
- 分类选择（dropdown）
- 父任务选择（dropdown，可选）
- 启用开关
- 屏幕常亮开关
- 保存/取消按钮

变更记录:
- Q21 决策：抽屉式侧滑（与 StepEditorView 一致）
- Q38 决策：与 TaskCard 视觉一致
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import flet as ft

from models.task import Task, TaskCategory

# 配色
_ACCENT = "#2563eb"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_RULE = "#e5e7eb"
_BG2 = "#ffffff"

# 常用 Material 图标列表（PRD 13.3 任务图标可选）
_PRESET_ICONS: list[str] = [
    "play_arrow",
    "check_box",
    "list",
    "work",
    "school",
    "wb_sunny",
    "water_drop",
    "power_settings_new",
    "settings",
    "sports_esports",
    "collections_bookmark",
    "favorite",
    "star",
    "alarm",
    "schedule",
    "home",
    "music_note",
    "camera_alt",
    "edit",
    "delete",
]


@dataclass
class TaskEditData:
    """任务编辑数据模型（与 Task 解耦）"""

    task_id: str | None = None  # None 表示新建
    name: str = ""
    description: str = ""
    icon: str = "play_arrow"
    category: TaskCategory = TaskCategory.DEFAULT
    parent_id: str | None = None
    enabled: bool = True
    keep_screen_on: bool = False

    @classmethod
    def from_task(cls, task: Task) -> "TaskEditData":
        """从 Task 构造编辑数据"""
        return cls(
            task_id=task.id,
            name=task.name,
            description=task.description,
            icon=task.icon,
            category=task.category,
            enabled=task.enabled,
            keep_screen_on=task.keep_screen_on,
        )

    def to_task(self, task_id: str | None = None) -> Task:
        """转换为 Task 实体"""
        return Task(
            id=task_id or self.task_id or "",
            name=self.name,
            description=self.description,
            icon=self.icon,
            category=self.category,
            enabled=self.enabled,
            keep_screen_on=self.keep_screen_on,
        )

    def is_valid(self) -> bool:
        """数据校验：名称非空"""
        return bool(self.name.strip())


class TaskEditDrawer(ft.Container):
    """任务编辑抽屉（抽屉式侧滑，Q21 决策）

    Attributes:
        on_save: 保存回调（参数：TaskEditData）
        on_cancel: 取消回调
        initial_data: 初始数据（编辑模式）或 None（新建模式）
        parent_options: 可选父任务列表 [(task_id, task_name), ...]
    """

    def __init__(
        self,
        on_save: Callable[[TaskEditData], None],
        on_cancel: Callable[[], None],
        initial_data: TaskEditData | None = None,
        parent_options: list[tuple[str, str]] | None = None,
    ) -> None:
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._data = initial_data or TaskEditData()
        self._parent_options = parent_options or []
        self._is_edit_mode = initial_data is not None and initial_data.task_id is not None

        # 表单控件
        self._name_field = ft.TextField(
            label="任务名称",
            value=self._data.name,
            autofocus=True,
            max_length=50,
        )
        self._desc_field = ft.TextField(
            label="任务描述",
            value=self._data.description,
            multiline=True,
            min_lines=2,
            max_lines=4,
            max_length=200,
        )
        self._category_dropdown = ft.Dropdown(
            label="任务分类",
            value=self._data.category.value,
            options=[
                ft.dropdown.Option(key=TaskCategory.DEFAULT.value, text="默认"),
                ft.dropdown.Option(key=TaskCategory.WORK.value, text="工作"),
                ft.dropdown.Option(key=TaskCategory.LIFE.value, text="生活"),
                ft.dropdown.Option(key=TaskCategory.STUDY.value, text="学习"),
                ft.dropdown.Option(
                    key=TaskCategory.ENTERTAINMENT.value, text="娱乐"
                ),
                ft.dropdown.Option(key=TaskCategory.SYSTEM.value, text="系统"),
            ],
        )
        # 父任务 dropdown
        parent_opts = [ft.dropdown.Option(key="", text="无（顶层任务）")]
        for tid, tname in self._parent_options:
            parent_opts.append(ft.dropdown.Option(key=tid, text=tname))
        self._parent_dropdown = ft.Dropdown(
            label="父任务（可选）",
            value=self._data.parent_id or "",
            options=parent_opts,
        )

        # 启用开关
        self._enabled_switch = ft.Switch(
            label="启用此任务",
            value=self._data.enabled,
        )
        self._keep_screen_on_switch = ft.Switch(
            label="执行时保持屏幕常亮",
            value=self._data.keep_screen_on,
        )

        # 图标选择网格
        self._icon_grid = self._build_icon_grid()

        # 操作按钮
        save_btn = ft.Button(
            "保存",
            icon=ft.Icons.SAVE,
            on_click=self._handle_save,
            bgcolor=_ACCENT,
            color="white",
        )
        cancel_btn = ft.Button(
            "取消",
            icon=ft.Icons.CANCEL,
            on_click=self._handle_cancel,
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.EDIT_NOTE if self._is_edit_mode else ft.Icons.ADD_TASK,
                                color=_ACCENT,
                                size=24,
                            ),
                            ft.Text(
                                "编辑任务" if self._is_edit_mode else "新建任务",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                        ],
                        spacing=8,
                    ),
                    self._name_field,
                    self._desc_field,
                    self._category_dropdown,
                    self._parent_dropdown,
                    ft.Text(
                        "任务图标",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=_INK,
                    ),
                    self._icon_grid,
                    self._enabled_switch,
                    self._keep_screen_on_switch,
                    ft.Row(
                        controls=[cancel_btn, save_btn],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8,
                    ),
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=360,
            bgcolor=_BG2,
            padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            border=ft.Border(left=1, right=0, top=0, bottom=0),
        )

    def _build_icon_grid(self) -> ft.Row:
        """构建图标选择网格（5 列）"""
        selected_icon = self._data.icon

        def make_icon_btn(icon_name: str) -> ft.IconButton:
            is_selected = icon_name == selected_icon
            return ft.IconButton(
                icon=icon_name,
                icon_color=_ACCENT if is_selected else _MUTED,
                icon_size=20,
                tooltip=icon_name,
                on_click=lambda e, name=icon_name: self._handle_select_icon(name),
                style=ft.ButtonStyle(
                    bgcolor=_ACCENT if is_selected else None,
                ),
            )

        rows: list[ft.Control] = []
        # 5 列布局
        for i in range(0, len(_PRESET_ICONS), 5):
            chunk = _PRESET_ICONS[i : i + 5]
            rows.append(
                ft.Row(
                    controls=[make_icon_btn(name) for name in chunk],
                    spacing=4,
                    alignment=ft.MainAxisAlignment.START,
                )
            )
        return ft.Column(controls=rows, spacing=4)

    def _handle_select_icon(self, icon_name: str) -> None:
        """选中图标"""
        self._data.icon = icon_name
        # 重新构建图标网格
        new_grid = self._build_icon_grid()
        # 替换原网格（在 content Column 中是第 7 个控件，索引 6）
        # 实际上由于 _build_icon_grid 是新建，需要更新父 Column
        try:
            content_col = self.content
            if isinstance(content_col, ft.Column):
                # 找到图标网格的位置（"任务图标" 文本后）
                for i, ctrl in enumerate(content_col.controls):
                    if isinstance(ctrl, ft.Text) and ctrl.value == "任务图标":
                        content_col.controls[i + 1] = new_grid
                        break
                self.update()
        except Exception:
            pass

    def _handle_save(self, e: ft.ControlEvent) -> None:
        """保存按钮"""
        # 收集表单数据
        self._data.name = self._name_field.value or ""
        self._data.description = self._desc_field.value or ""
        category_str = self._category_dropdown.value
        if category_str:
            try:
                self._data.category = TaskCategory(category_str)
            except ValueError:
                self._data.category = TaskCategory.DEFAULT
        parent_str = self._parent_dropdown.value
        self._data.parent_id = parent_str if parent_str else None
        self._data.enabled = bool(self._enabled_switch.value)
        self._data.keep_screen_on = bool(self._keep_screen_on_switch.value)

        # 校验
        if not self._data.is_valid():
            try:
                self._name_field.error_text = "任务名称不能为空"
                self._name_field.update()
            except Exception:
                pass
            return

        # 调用回调
        if self._on_save:
            self._on_save(self._data)

    def _handle_cancel(self, e: ft.ControlEvent) -> None:
        """取消按钮"""
        if self._on_cancel:
            self._on_cancel()

    def is_dirty(self) -> bool:
        """表单是否有未保存改动（Q20 风格）"""
        return (
            (self._name_field.value or "") != self._data.name
            or (self._desc_field.value or "") != self._data.description
        )

    def get_data(self) -> TaskEditData:
        """获取当前编辑数据"""
        return self._data


class TaskEditView(ft.View):
    """任务编辑全屏视图（备用，通常用抽屉）

    完整的 ft.View 形式，用于需要独立路由的场景。
    """

    def __init__(
        self,
        page: ft.Page,
        on_save: Callable[[TaskEditData], None],
        on_cancel: Callable[[], None],
        initial_data: TaskEditData | None = None,
        parent_options: list[tuple[str, str]] | None = None,
    ) -> None:
        self._page = page
        self._drawer = TaskEditDrawer(
            on_save=on_save,
            on_cancel=on_cancel,
            initial_data=initial_data,
            parent_options=parent_options,
        )

        super().__init__(
            route="/task_edit",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: on_cancel(),
                    ),
                    title=ft.Text("任务编辑"),
                    bgcolor=_ACCENT,
                    color="white",
                ),
                ft.SafeArea(content=self._drawer, expand=True),
            ],
            spacing=0,
        )
