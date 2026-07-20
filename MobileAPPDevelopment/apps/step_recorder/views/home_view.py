"""任务列表视图（M1 主视图）

底部导航 3 tab（Q50 调整）：
- 任务 tab（/tasks，默认）：TaskTree 任务列表 + 添加按钮
- 统计 tab（/stats）：点击直接跳转 StatsView
- 日志 tab（/logs）：点击直接跳转 LogsView
- 设置图标常驻 AppBar（添加任务左边）→ /settings

变更记录:
- Q37: 默认路由改为 /tasks（覆盖需求6）
- Q38: TaskCard 用 PRD 原样样式
- Q39: TaskTree 支持 tree/breadcrumb 双模式（设置可切换，默认 tree）
- Q40: 4 tab 框架（任务/步骤/统计/设置）
- Q50: 调整为 3 tab（任务/统计/日志）+ AppBar 设置；步骤 tab 去掉
- Q50: 任务卡片左下角加删除按钮（二次确认）
- Q50: 抽屉关闭改为点击遮罩 + 取消按钮双关闭
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

TabKey = Literal["tasks", "stats", "logs"]


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
            on_delete=self._handle_delete_task,
            expanded_ids=set(),
        )

        # 任务编辑抽屉（T1.3，初始隐藏）
        # 抽屉遮罩容器：点击空白处关闭抽屉（Q50）
        self._drawer = TaskEditDrawer(
            on_save=self._handle_save_task,
            on_cancel=self._handle_close_drawer,
        )
        self._drawer_visible = False
        self._overlay = ft.Container(
            content=self._drawer,
            alignment=ft.Alignment.CENTER_RIGHT,
            bgcolor="#80000000",  # 半透明黑色遮罩
            visible=False,
            expand=True,
            on_click=self._handle_overlay_click,
        )

        # 设置按钮（常驻 AppBar 左侧，Q50 需求12）
        settings_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            on_click=self._handle_goto_settings,
            tooltip="设置",
            icon_color="white",
        )

        # 添加任务按钮（Q50：设置在左，添加在右）
        add_btn = ft.Button(
            "添加任务",
            icon=ft.Icons.ADD,
            on_click=self._handle_add_task,
            bgcolor="white",
            color=_ACCENT,
            tooltip="添加任务",
        )

        # AppBar（设置在左，添加任务在右）
        appbar = ft.AppBar(
            leading=settings_btn,
            title=ft.Text("任务管理"),
            actions=[add_btn],
            bgcolor=_ACCENT,
            color="white",
        )

        # 底部导航（3 tab，Q50：任务/统计/日志）
        nav_bar = ft.NavigationBar(
            selected_index=self._tab_to_index(initial_tab),
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CHECK_BOX_OUTLINED,
                    selected_icon=ft.Icons.CHECK_BOX,
                    label="任务",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART_OUTLINED,
                    selected_icon=ft.Icons.BAR_CHART,
                    label="统计",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIST_ALT_OUTLINED,
                    selected_icon=ft.Icons.LIST,
                    label="日志",
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
        """构建主内容（任务列表 + 抽屉）"""
        return self._build_tasks_tab()

    # ---- tab 渲染 ----

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

    # ---- tab 转换 ----

    @staticmethod
    def _tab_to_index(tab: TabKey) -> int:
        """tab key 转 NavigationBar selected_index"""
        return {"tasks": 0, "stats": 1, "logs": 2}[tab]

    @staticmethod
    def _index_to_tab(index: int) -> TabKey:
        """NavigationBar selected_index 转 tab key"""
        mapping = {0: "tasks", 1: "stats", 2: "logs"}
        return mapping.get(index, "tasks")  # type: ignore[return-value]

    # ---- 事件处理 ----

    def _handle_tab_change(self, e: ft.NavigationBarEvent) -> None:
        """tab 切换：统计/日志直接跳路由，任务保持"""
        new_tab = self._index_to_tab(
            int(e.control.selected_index) if hasattr(e.control, "selected_index") else 0
        )
        self._current_tab = new_tab
        try:
            self._page.update()
        except Exception:
            pass

        # 路由跳转
        route_map = {
            "tasks": "/tasks",
            "stats": "/stats",
            "logs": "/logs",
        }
        target_route = route_map.get(new_tab, "/tasks")
        if new_tab != "tasks":
            # 统计/日志跳转到独立路由
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

    def _handle_close_drawer(self, e: ft.ControlEvent | None = None) -> None:
        """关闭抽屉（清除遮罩 + 清空 content 引用，避免黑屏）"""
        # 阻止遮罩点击触发取消后再次冒泡
        if e is not None:
            try:
                e.stop_propagation = True
            except Exception:
                pass
        self._drawer_visible = False
        self._overlay.visible = False
        # 清空遮罩内容引用，避免下次 update 时引用失效的控件
        self._overlay.content = None
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_overlay_click(self, e: ft.ControlEvent) -> None:
        """点击遮罩空白处关闭抽屉（Q50）"""
        # 仅当点击的是遮罩本身（而非内部抽屉）时关闭
        if e.control == self._overlay:
            self._handle_close_drawer(e)

    def _refresh_task_tree(self) -> None:
        """刷新任务树"""
        new_tree = TaskTree(
            nodes=build_forest(self._tasks, self._relations),
            nest_mode=self._task_tree._nest_mode,
            on_toggle_enabled=self._handle_toggle_task,
            on_execute=self._handle_execute_task,
            on_click=self._handle_click_task,
            on_navigate=self._handle_breadcrumb_navigate,
            on_delete=self._handle_delete_task,
            expanded_ids=self._task_tree._expanded_ids,
            current_parent_id=self._task_tree._current_parent_id,
        )
        # 替换原任务树引用
        self._task_tree = new_tree
        # 重新构建视图
        self.controls = [
            self.controls[0],  # AppBar
            ft.SafeArea(content=self._build_main_content(), expand=True),
            self.controls[2],  # NavigationBar
        ]
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

    def _handle_delete_task(self, task_id: str) -> None:
        """删除任务（Q50 需求11：二次确认后删除）"""
        # 找到任务
        task = next((t for t in self._tasks if t.id == task_id), None)
        if task is None:
            return
        # 从任务列表中删除
        self._tasks = [t for t in self._tasks if t.id != task_id]
        # 删除相关的关系（作为父或子）
        self._relations = [
            r for r in self._relations if r.parent_id != task_id and r.child_id != task_id
        ]
        # 刷新任务树
        self._refresh_task_tree()
        # 通知用户
        try:
            self._page.snackbar = ft.SnackBar(ft.Text(f"任务「{task.name}」已删除"))
            self._page.update()
        except Exception:
            pass

    def _handle_breadcrumb_navigate(self, target_id: str | None) -> None:
        """面包屑导航切换层级（仅 breadcrumb 模式触发）"""
        # TaskTree 内部已更新，这里只做额外处理（如持久化当前层级）
        pass

    def _handle_goto_settings(self, e: ft.ControlEvent) -> None:
        """跳转到设置页（Q50 需求12：AppBar 设置按钮）"""
        try:
            self._page.go("/settings")
        except Exception:
            pass
