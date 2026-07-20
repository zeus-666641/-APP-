"""任务列表视图（M1 主视图）

底部导航 4 tab（PRD 12 章）：
- 任务 tab（/tasks，默认）：TaskTree 任务列表 + 添加按钮
- 步骤 tab（/step_editor）：跳转 StepEditorView
- 统计 tab（/stats）：M4 模块（M1 阶段先占位）
- 设置 tab（/settings）：跳转 SettingsView

变更记录:
- Q37: 默认路由改为 /tasks（覆盖需求6）
- Q38: TaskCard 用 PRD 原样样式
- Q39: TaskTree 支持 tree/breadcrumb 双模式（设置可切换，默认 tree）
- Q40: 4 tab 框架，统计/日志 tab 先占位
"""
from __future__ import annotations

from typing import Literal

import flet as ft

from config.settings import Settings
from models.task import Task, TaskCategory, TaskRelation, TaskStatus, build_forest
from views.components.task_tree import TaskTree
from views.task_edit_view import TaskEditData, TaskEditDrawer

# 配色
_ACCENT = "#2563eb"
_INK = "#1a1a2e"
_MUTED = "#6b7280"
_RULE = "#e5e7eb"

TabKey = Literal["tasks", "steps", "stats", "settings"]


# ---- mock 数据（T1.4 将扩展） ----


def _default_mock_tasks() -> list[Task]:
    """默认 mock 任务列表（覆盖根任务、父子嵌套、不同状态）"""
    return [
        Task(
            id="t1",
            name="早晨例行程序",
            icon="wb_sunny",
            category=TaskCategory.LIFE,
            sort_order=0,
        ),
        Task(
            id="t2",
            name="工作日报生成",
            icon="work",
            category=TaskCategory.WORK,
            sort_order=1,
        ),
        Task(
            id="t3",
            name="学习计划",
            icon="school",
            category=TaskCategory.STUDY,
            sort_order=2,
        ),
        Task(
            id="t4",
            name="娱乐时间",
            icon="sports_esports",
            category=TaskCategory.ENTERTAINMENT,
            enabled=False,
            sort_order=3,
        ),
        Task(
            id="t5",
            name="系统优化",
            icon="settings",
            category=TaskCategory.SYSTEM,
            sort_order=4,
        ),
        # 子任务
        Task(
            id="t1_1",
            name="开机检查",
            icon="power_settings_new",
            category=TaskCategory.LIFE,
            sort_order=0,
        ),
        Task(
            id="t1_2",
            name="喝水提醒",
            icon="water_drop",
            category=TaskCategory.LIFE,
            sort_order=1,
        ),
        Task(
            id="t2_1",
            name="收集工作内容",
            icon="collections_bookmark",
            category=TaskCategory.WORK,
            sort_order=0,
        ),
    ]


def _default_mock_relations() -> list[TaskRelation]:
    """默认 mock 关系列表（父子嵌套）"""
    return [
        TaskRelation(id="r1", parent_id="t1", child_id="t1_1", sort_order=0),
        TaskRelation(id="r2", parent_id="t1", child_id="t1_2", sort_order=1),
        TaskRelation(id="r3", parent_id="t2", child_id="t2_1", sort_order=0),
    ]


class HomeView(ft.View):
    """任务列表主视图（M1 默认首屏）

    Attributes:
        page: Flet 页面对象
        current_tab: 当前激活的 tab（默认 "tasks"）
    """

    def __init__(self, page: ft.Page, initial_tab: TabKey = "tasks") -> None:
        self._page = page
        self._settings = Settings()
        self._tasks = _default_mock_tasks()
        self._relations = _default_mock_relations()
        self._current_tab: TabKey = initial_tab
        self._editing_parent_id: str | None = None

        # 任务树（Q39 双模式，默认 tree）
        nest_mode = "tree"  # 默认 tree，可在设置中切换
        self._task_tree = TaskTree(
            nodes=build_forest(self._tasks, self._relations),
            nest_mode=nest_mode,  # type: ignore[arg-type]
            on_toggle_enabled=self._handle_toggle_task,
            on_execute=self._handle_execute_task,
            on_click=self._handle_click_task,
            on_navigate=self._handle_breadcrumb_navigate,
            expanded_ids=set(),
        )

        # 任务编辑抽屉（T1.3，初始隐藏）
        self._drawer = TaskEditDrawer(
            on_save=self._handle_save_task,
            on_cancel=self._handle_close_drawer,
        )
        self._drawer_visible = False
        self._overlay = ft.Container(
            content=self._drawer,
            alignment=ft.Alignment.CENTER_RIGHT,
            bgcolor="#00000000",  # 透明背景
            visible=False,
            expand=True,
        )

        # 添加任务按钮（参照 F9a：胶囊状）
        add_btn = ft.Button(
            "添加任务",
            icon=ft.Icons.ADD,
            on_click=self._handle_add_task,
            bgcolor=_ACCENT,
            color="white",
            tooltip="添加任务",
        )

        # AppBar
        appbar = ft.AppBar(
            title=ft.Text("任务管理"),
            actions=[add_btn],
            bgcolor=_ACCENT,
            color="white",
        )

        # 底部导航（4 tab，Q40 决策）
        nav_bar = ft.NavigationBar(
            selected_index=self._tab_to_index(initial_tab),
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CHECK_BOX_OUTLINED,
                    selected_icon=ft.Icons.CHECK_BOX,
                    label="任务",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIST_OUTLINED,
                    selected_icon=ft.Icons.LIST,
                    label="步骤",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART_OUTLINED,
                    selected_icon=ft.Icons.BAR_CHART,
                    label="统计",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="设置",
                ),
            ],
            on_change=self._handle_tab_change,
        )

        # 主内容容器（叠加：主内容 + 抽屉遮罩）
        main_stack = ft.Stack(
            controls=[
                self._build_main_content(),
                self._overlay,
            ],
            expand=True,
        )

        super().__init__(
            route="/tasks",
            controls=[
                appbar,
                ft.SafeArea(
                    content=main_stack,
                    expand=True,
                ),
                nav_bar,
            ],
            spacing=0,
        )

    def _build_main_content(self) -> ft.Control:
        """构建主内容（含 tab 切换 + 抽屉）"""
        return self._build_tab_content()

    # ---- tab 渲染 ----

    def _build_tab_content(self) -> ft.Control:
        """根据当前 tab 渲染对应内容"""
        if self._current_tab == "tasks":
            return self._build_tasks_tab()
        elif self._current_tab == "steps":
            return self._build_steps_tab()
        elif self._current_tab == "stats":
            return self._build_stats_tab()
        else:  # settings
            return self._build_settings_tab()

    def _build_tasks_tab(self) -> ft.Control:
        """任务 tab：section-title + TaskTree"""
        # F9c 风格的 section-title
        section_title = ft.Row(
            controls=[
                ft.Text(
                    "全部任务",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=_INK,
                ),
                ft.Text(
                    f"共 {len(self._tasks)} 项",
                    size=12,
                    color=_MUTED,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Column(
            controls=[
                ft.Container(
                    content=section_title,
                    padding=ft.Padding(left=16, right=16, top=8, bottom=4),
                ),
                ft.Container(
                    content=self._task_tree,
                    padding=ft.Padding(left=16, right=16, top=0, bottom=16),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _build_steps_tab(self) -> ft.Control:
        """步骤 tab：跳转到 /step_editor"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.LIST_ALT,
                                color=_ACCENT,
                                size=48,
                            ),
                            ft.Text(
                                "步骤编辑器",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                            ft.Text(
                                "点击下方按钮进入步骤编辑器",
                                size=12,
                                color=_MUTED,
                            ),
                            ft.Button(
                                "进入步骤编辑器",
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=self._handle_goto_steps,
                                bgcolor=_ACCENT,
                                color="white",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _build_stats_tab(self) -> ft.Control:
        """统计 tab：跳转到 /stats（M4）+ /logs（M5）"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.BAR_CHART,
                                color=_ACCENT,
                                size=48,
                            ),
                            ft.Text(
                                "执行统计与日志",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                            ft.Text(
                                "查看任务执行次数、成功率、平均时长等统计数据\n查看每次任务执行的详细日志",
                                size=12,
                                color=_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Button(
                                        "进入统计页",
                                        icon=ft.Icons.BAR_CHART_OUTLINED,
                                        on_click=self._handle_goto_stats,
                                        bgcolor=_ACCENT,
                                        color="white",
                                        expand=True,
                                    ),
                                    ft.Button(
                                        "进入日志页",
                                        icon=ft.Icons.LIST_ALT,
                                        on_click=self._handle_goto_logs,
                                        bgcolor="#1a1a2e",
                                        color="white",
                                        expand=True,
                                    ),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _build_settings_tab(self) -> ft.Control:
        """设置 tab：跳转到 /settings"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icon=ft.Icons.SETTINGS,
                                color=_ACCENT,
                                size=48,
                            ),
                            ft.Text(
                                "系统设置",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                            ft.Text(
                                "点击下方按钮进入设置页",
                                size=12,
                                color=_MUTED,
                            ),
                            ft.Button(
                                "进入设置",
                                icon=ft.Icons.ARROW_FORWARD,
                                on_click=self._handle_goto_settings,
                                bgcolor=_ACCENT,
                                color="white",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _build_placeholder(
        self, icon: str, title: str, message: str
    ) -> ft.Control:
        """通用占位页（Q5 决策：预留接口 + 显示"尚未完成"）"""
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                icon=icon,
                                color=_MUTED,
                                size=48,
                            ),
                            ft.Text(
                                title,
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=_INK,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    "尚未完成",
                                    size=12,
                                    color="white",
                                    weight=ft.FontWeight.W_500,
                                ),
                                bgcolor=_MUTED,
                                padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                                border_radius=8,
                            ),
                            ft.Text(
                                message,
                                size=12,
                                color=_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )

    # ---- tab 转换 ----

    @staticmethod
    def _tab_to_index(tab: TabKey) -> int:
        """tab key 转 NavigationBar selected_index"""
        return {"tasks": 0, "steps": 1, "stats": 2, "settings": 3}[tab]

    @staticmethod
    def _index_to_tab(index: int) -> TabKey:
        """NavigationBar selected_index 转 tab key"""
        mapping = {0: "tasks", 1: "steps", 2: "stats", 3: "settings"}
        return mapping.get(index, "tasks")  # type: ignore[return-value]

    # ---- 事件处理 ----

    def _handle_tab_change(self, e: ft.NavigationBarEvent) -> None:
        """tab 切换"""
        new_tab = self._index_to_tab(int(e.control.selected_index) if hasattr(e.control, "selected_index") else 0)
        self._current_tab = new_tab
        # 重新构建视图内容
        self.controls = [
            self.controls[0],  # AppBar
            ft.SafeArea(content=self._build_tab_content(), expand=True),
            self.controls[2],  # NavigationBar
        ]
        try:
            self._page.update()
        except Exception:
            pass

        # 路由跳转
        route_map = {
            "tasks": "/tasks",
            "steps": "/step_editor",
            "stats": "/stats",
            "settings": "/settings",
        }
        target_route = route_map.get(new_tab, "/tasks")
        if new_tab in ("steps", "settings"):
            # steps 和 settings 跳转到独立 View
            try:
                self._page.go(target_route)
            except Exception:
                pass

    def _handle_add_task(self, e: ft.ControlEvent) -> None:
        """添加任务 → 打开抽屉新建模式"""
        self._editing_parent_id = None
        # 重置抽屉为新建模式
        self._drawer = TaskEditDrawer(
            on_save=self._handle_save_task,
            on_cancel=self._handle_close_drawer,
            parent_options=self._get_parent_options(),
        )
        self._overlay.content = self._drawer
        self._drawer_visible = True
        self._overlay.visible = True
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_save_task(self, data: TaskEditData) -> None:
        """保存任务（新建或更新）"""
        if data.task_id is None:
            # 新建：生成新 ID
            new_id = f"t{len(self._tasks) + 1}_{id(data) % 10000}"
            task = data.to_task(new_id)
            task.sort_order = len(self._tasks)
            self._tasks.append(task)
            # 如果有父任务，添加关系
            if data.parent_id:
                new_rel = TaskRelation(
                    id=f"r{len(self._relations) + 1}",
                    parent_id=data.parent_id,
                    child_id=new_id,
                    sort_order=0,
                )
                self._relations.append(new_rel)
        else:
            # 更新：找到原任务并更新字段
            for i, t in enumerate(self._tasks):
                if t.id == data.task_id:
                    self._tasks[i] = data.to_task(data.task_id)
                    break
        # 关闭抽屉
        self._handle_close_drawer()
        # 刷新任务树
        self._refresh_task_tree()
        # 通知用户
        try:
            self._page.snackbar = ft.SnackBar(ft.Text("任务已保存"))
            self._page.update()
        except Exception:
            pass

    def _handle_close_drawer(self) -> None:
        """关闭抽屉"""
        self._drawer_visible = False
        self._overlay.visible = False
        try:
            self._page.update()
        except Exception:
            pass

    def _refresh_task_tree(self) -> None:
        """刷新任务树"""
        new_tree = TaskTree(
            nodes=build_forest(self._tasks, self._relations),
            nest_mode=self._task_tree._nest_mode,
            on_toggle_enabled=self._handle_toggle_task,
            on_execute=self._handle_execute_task,
            on_click=self._handle_click_task,
            on_navigate=self._handle_breadcrumb_navigate,
            expanded_ids=self._task_tree._expanded_ids,
            current_parent_id=self._task_tree._current_parent_id,
        )
        # 替换原任务树引用
        self._task_tree = new_tree
        # 更新主内容（需要重新构建视图）
        try:
            self._page.update()
        except Exception:
            pass

    def _get_parent_options(
        self, exclude_id: str | None = None
    ) -> list[tuple[str, str]]:
        """获取可选父任务列表（排除 exclude_id 及其子树，避免循环嵌套）

        Args:
            exclude_id: 要排除的任务 ID（编辑模式下排除自身及子树）

        Returns:
            [(task_id, task_name), ...]
        """
        # 简化版：排除 exclude_id 本身（不递归排除子树，M0 数据层接入后改进）
        return [
            (t.id, t.name)
            for t in self._tasks
            if t.id != exclude_id
        ]

    def _handle_toggle_task(self, task_id: str, enabled: bool) -> None:
        """启用/禁用任务"""
        for task in self._tasks:
            if task.id == task_id:
                task.enabled = enabled
                task.updated_at = task.updated_at  # 触发 dataclass 默认？保留原值
                break
        # 不重新渲染，避免打断交互

    def _handle_execute_task(self, task_id: str) -> None:
        """执行任务（占位，M7 接入执行引擎）"""
        try:
            self._page.snackbar = ft.SnackBar(
                ft.Text(f"执行任务功能将在 M7 实现（任务 ID: {task_id}）")
            )
            self._page.update()
        except Exception:
            pass

    def _handle_click_task(self, task_id: str) -> None:
        """点击任务卡片 → 打开抽屉编辑模式"""
        task = next((t for t in self._tasks if t.id == task_id), None)
        if task is None:
            return
        self._editing_parent_id = task.id
        edit_data = TaskEditData.from_task(task)
        # 排除当前任务及其子树作为父选项（避免循环）
        parent_options = self._get_parent_options(exclude_id=task_id)
        self._drawer = TaskEditDrawer(
            on_save=self._handle_save_task,
            on_cancel=self._handle_close_drawer,
            initial_data=edit_data,
            parent_options=parent_options,
        )
        self._overlay.content = self._drawer
        self._drawer_visible = True
        self._overlay.visible = True
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_breadcrumb_navigate(self, target_id: str | None) -> None:
        """面包屑导航切换层级（仅 breadcrumb 模式触发）"""
        # TaskTree 内部已更新，这里只做额外处理（如持久化当前层级）
        pass

    def _handle_goto_steps(self, e: ft.ControlEvent) -> None:
        """跳转到步骤编辑器"""
        try:
            self._page.go("/step_editor")
        except Exception:
            pass

    def _handle_goto_stats(self, e: ft.ControlEvent) -> None:
        """跳转到统计页（M4）"""
        try:
            self._page.go("/stats")
        except Exception:
            pass

    def _handle_goto_logs(self, e: ft.ControlEvent) -> None:
        """跳转到日志页（M5）"""
        try:
            self._page.go("/logs")
        except Exception:
            pass

    def _handle_goto_settings(self, e: ft.ControlEvent) -> None:
        """跳转到设置页"""
        try:
            self._page.go("/settings")
        except Exception:
            pass
