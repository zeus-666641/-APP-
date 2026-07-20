"""步骤编辑器主视图（M2-T2.7 + T2.8 + 需求6/F3 + 需求9/F5）

按 Q21-Q29 决策落地：
- Q21 抽屉式侧滑：右侧滑出宽度 80%，含 StepTypePicker + ParamEditor
- Q22 双入口：FAB（默认）+ 顶部 AppBar 按钮，二者调用同一 add 流程
- Q23 mock 3-5 条示例步骤：覆盖 AVAILABLE/LIMITED/NOT_IMPLEMENTED 三种状态
- Q20 未保存离开：编辑抽屉关闭前检查 dirty，弹 AlertDialog 三选一
- Q24-Q29 DraggableList：拖拽手柄 + 换位按钮（输入目标行号），可独立开关

需求6（F3）：
- 删除 HomeView 入口，启动后直接进入步骤编辑器
- AppBar 添加设置按钮（齿轮图标），点击跳转 /settings

需求9（F5）：
- 步骤卡片右侧添加执行按钮（play_circle）
- 点击触发 on_execute 回调，调用步骤执行逻辑（M7 完整接入）

需求3（F1）：
- 默认只显示右上角 AppBar 的"添加步骤"按钮，FAB 默认隐藏
- 通过设置中"添加步骤入口"项可切换为 fab / appbar / both

入口：page.go("/step_editor") —— 应用启动后默认路由
"""
from __future__ import annotations

from typing import Any

import flet as ft

from models.step import StepStatus, StepType, get_step_type_meta
from views.components.draggable_list import DraggableList
from views.components.notifier import Notifier
from views.components.param_editor import ParamEditor
from views.components.step_card import StepCard, StepCardData
from views.components.step_type_picker import StepTypePicker
from views.settings_view import get_app_setting


# ---- Mock 数据（Q23 决策）----


def _default_mock_steps() -> list[StepCardData]:
    """生成 5 条示例步骤，覆盖三种状态"""
    return [
        StepCardData(
            step_id="step_001",
            step_order=1,
            step_type=StepType.OPEN_URL,
            name_zh="打开首页",
            params={"url": "https://example.com"},
            enabled=True,
            is_placeholder=False,
        ),
        StepCardData(
            step_id="step_002",
            step_order=2,
            step_type=StepType.DELAY,
            name_zh="等待 2 秒",
            params={"duration": 2},
            enabled=True,
            is_placeholder=False,
        ),
        StepCardData(
            step_id="step_003",
            step_order=3,
            step_type=StepType.DARK_MODE,
            name_zh="切换深色模式",
            params={"state": "follow_system"},
            enabled=True,
            is_placeholder=False,
        ),
        StepCardData(
            step_id="step_004",
            step_order=4,
            step_type=StepType.CLICK,
            name_zh="点击登录按钮",
            params={"target": "btn_login", "x": 100, "y": 200},
            enabled=False,
            is_placeholder=False,
        ),
        StepCardData(
            step_id="step_005",
            step_order=5,
            step_type=StepType.BLUETOOTH,
            name_zh="打开蓝牙",
            params={"state": "on"},
            enabled=True,
            is_placeholder=True,
        ),
    ]


# ---- 编辑抽屉（Q21 决策）----


class StepEditorDrawer(ft.Container):
    """步骤编辑抽屉

    从右侧滑出，宽度 80%。
    内含两个阶段：
    - 阶段 1：StepTypePicker（选择类型）
    - 阶段 2：ParamEditor（编辑参数）

    通过 on_save / on_cancel 回调与外部通信。
    """

    def __init__(
        self,
        on_save: Any = None,
        on_cancel: Any = None,
    ) -> None:
        self._on_save = on_save
        self._on_cancel = on_cancel

        # 当前编辑状态
        self._editing_step_id: str | None = None
        self._selected_step_type: StepType | None = None
        self._param_editor: ParamEditor | None = None

        # 标题栏
        self._title = ft.Text(
            "添加步骤",
            size=16,
            weight=ft.FontWeight.W_600,
            color="#1a1a2e",
        )

        # 类型选择面板
        self._type_picker = StepTypePicker(
            on_select=self._handle_type_selected,
        )

        # 参数编辑器容器（动态切换）
        self._param_container = ft.Container(
            content=ft.Text(
                "请先选择步骤类型",
                size=13,
                color="#94a3b8",
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.Padding(left=12, right=12, top=24, bottom=24),
            alignment=ft.Alignment.CENTER,
        )

        # 底部按钮栏
        self._save_btn = ft.Button(
            "保存",
            icon=ft.Icons.SAVE,
            on_click=self._handle_save,
            bgcolor="#2563eb",
            color="white",
            disabled=True,
        )
        self._cancel_btn = ft.Button(
            "取消",
            on_click=self._handle_cancel,
        )

        super().__init__(
            content=ft.Column(
                controls=[
                    # 顶部标题 + 关闭
                    ft.Row(
                        controls=[
                            self._title,
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color="#6b7280",
                                on_click=self._handle_cancel,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # 类型选择（选中类型后折叠）
                    self._type_picker,
                    # 参数编辑区
                    self._param_container,
                    # 底部操作按钮
                    ft.Row(
                        controls=[
                            self._cancel_btn,
                            self._save_btn,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8,
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            width=320,  # 实际宽度由父级控制，这里只是默认
            height=800,  # 同上
            padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            bgcolor="#ffffff",
            border_radius=12,
        )

    # ---- 流程控制 ----

    def start_add(self) -> None:
        """开始添加新步骤"""
        self._editing_step_id = None
        self._selected_step_type = None
        self._param_editor = None
        self._title.value = "添加步骤"
        self._save_btn.disabled = True
        self._reset_param_container()

    def start_edit(self, step_data: StepCardData) -> None:
        """开始编辑已有步骤"""
        self._editing_step_id = step_data.step_id
        self._selected_step_type = step_data.step_type
        self._title.value = f"编辑步骤 · {step_data.name_zh}"
        self._save_btn.disabled = False
        # 直接进入参数编辑阶段
        self._param_editor = ParamEditor(
            step_type=step_data.step_type,
            initial_params=step_data.params,
        )
        self._param_container.content = self._param_editor

    def _reset_param_container(self) -> None:
        """重置参数区为初始提示"""
        self._param_container.content = ft.Text(
            "请先选择步骤类型",
            size=13,
            color="#94a3b8",
            text_align=ft.TextAlign.CENTER,
        )

    # ---- 事件处理 ----

    def _handle_type_selected(self, step_type: StepType, is_placeholder: bool) -> None:
        """类型选中回调"""
        self._selected_step_type = step_type
        self._param_editor = ParamEditor(step_type=step_type)
        self._param_container.content = self._param_editor
        self._save_btn.disabled = False

    def _handle_save(self, e: ft.ControlEvent) -> None:
        """保存按钮"""
        if self._selected_step_type is None or self._param_editor is None:
            return
        # 校验
        errors = self._param_editor.validate()
        if errors:
            # 校验失败，弹错误提示
            if self._on_save:
                # 把错误传出去，由外部展示
                self._on_save(
                    step_id=self._editing_step_id,
                    step_type=self._selected_step_type,
                    params=self._param_editor.get_values(),
                    errors=errors,
                )
            return
        if self._on_save:
            self._on_save(
                step_id=self._editing_step_id,
                step_type=self._selected_step_type,
                params=self._param_editor.get_values(),
                errors=[],
            )

    def _handle_cancel(self, e: ft.ControlEvent) -> None:
        """取消按钮"""
        if self._on_cancel:
            self._on_cancel()

    # ---- dirty 检测（Q20 决策）----

    def is_dirty(self) -> bool:
        """检测当前编辑是否有未保存修改"""
        if self._param_editor is None:
            return False
        return self._param_editor.is_dirty()


# ---- 主视图 ----


class StepEditorView(ft.View):
    """步骤编辑器主视图（默认首屏，需求6）

    集成：
    - AppBar（标题 + 设置按钮 + 添加步骤按钮，需求6/F3）
    - 步骤列表 DraggableList（StepCard 渲染，含执行按钮 F5）
    - FAB 浮动按钮（默认隐藏，设置可调节，需求3/F1）
    - 编辑抽屉（StepEditorDrawer）
    - Q20 未保存离开 AlertDialog
    """

    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._notifier = Notifier(page)
        self._steps: list[StepCardData] = _default_mock_steps()
        self._drawer_visible = False
        # F4：当前正在添加子步骤的父步骤 ID（None 表示不在添加子步骤模式）
        self._editing_parent_id: str | None = None
        # F9c：section-title 引用（_build_main_content 中赋值）
        self._section_title: ft.Row | None = None

        # 步骤列表（Q24-Q29：DraggableList 替换原 ListView）
        self._steps_list = DraggableList(
            items=self._steps,
            item_builder=self._build_step_card,
            on_reorder=self._handle_reorder,
            key_extractor=lambda s: s.step_id,
            page=page,
            show_drag_handle=bool(get_app_setting("show_drag_handle", True)),
            show_swap_button=bool(get_app_setting("show_swap_button", True)),
            drag_handle_side=str(get_app_setting("drag_handle_side", "right")),  # type: ignore[arg-type]
            spacing=8,
        )

        # 编辑抽屉（Q21 决策）
        self._drawer = StepEditorDrawer(
            on_save=self._handle_save_step,
            on_cancel=self._handle_close_drawer,
        )

        # 抽屉遮罩（点击关闭）
        self._overlay = ft.Container(
            content=self._drawer,
            alignment=ft.Alignment.CENTER_RIGHT,
            bgcolor="#00000000",  # 透明背景
            visible=False,
            expand=True,
        )

        # 主容器（叠加：步骤列表 + 抽屉遮罩）
        main_stack = ft.Stack(
            controls=[
                self._build_main_content(),
                self._overlay,
            ],
            expand=True,
        )

        # 调用父类构造
        super().__init__(
            route="/step_editor",
            controls=[
                main_stack,
            ],
        )

    def _build_main_content(self) -> ft.Column:
        """主内容区：AppBar + 步骤列表 + 可选 FAB"""
        # 需求6/F3：AppBar 加设置按钮 + 添加步骤按钮
        # 需求3/F1：默认隐藏 FAB，仅 AppBar 入口
        # F9a：添加步骤按钮改胶囊状（ft.Button 替代 IconButton，与 PRD .add-btn 一致）
        add_entry = str(get_app_setting("add_step_entry", "appbar"))
        appbar_actions: list[ft.Control] = [
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="设置",
                on_click=self._handle_open_settings,
            ),
        ]
        # 仅 appbar 或 both 时在 AppBar 显示胶囊按钮
        if add_entry in ("appbar", "both"):
            appbar_actions.append(
                ft.Button(
                    "添加步骤",
                    icon=ft.Icons.ADD,
                    on_click=self._handle_add_step,
                    bgcolor="#2563eb",
                    color="white",
                    tooltip="添加步骤",
                )
            )

        appbar = ft.AppBar(
            title=ft.Text("步骤编辑器"),
            actions=appbar_actions,
            bgcolor="#2563eb",
            color="white",
        )

        # FAB（需求3/F1：默认隐藏，仅 fab 或 both 时显示）
        fab_container: ft.Control
        if add_entry in ("fab", "both"):
            fab = ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                on_click=self._handle_add_step,
                bgcolor="#2563eb",
                tooltip="添加步骤",
            )
            fab_container = ft.Container(
                content=fab,
                alignment=ft.Alignment.BOTTOM_RIGHT,
                padding=ft.Padding(left=0, right=16, top=0, bottom=16),
            )
        else:
            fab_container = ft.Container(width=0, height=0)

        # F9c：步骤列表上方 section-title 分组标题（参照 PRD .section-title 样式）
        # 14px W_600，左标题右统计，两端对齐
        self._section_title = ft.Row(
            controls=[
                ft.Text(
                    "执行步骤",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color="#1a1a2e",
                ),
                ft.Text(
                    f"共 {len(self._steps)} 项",
                    size=12,
                    color="#6b7280",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Column(
            controls=[
                appbar,
                ft.SafeArea(
                    content=ft.Column(
                        controls=[
                            # 顶部 padding 8 给标题留呼吸空间
                            ft.Container(
                                content=self._section_title,
                                padding=ft.Padding(left=16, right=16, top=8, bottom=4),
                            ),
                            ft.Stack(
                                controls=[
                                    self._steps_list,
                                    fab_container,
                                ],
                                expand=True,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    # ---- 渲染 ----

    def _build_step_card(self, data: StepCardData, index: int) -> StepCard:
        """为 DraggableList 构建单个 StepCard（item_builder）"""
        # 同步 step_order（拖拽后顺序变化）
        if data.step_order != index + 1:
            data.step_order = index + 1
        return StepCard(
            data=data,
            on_toggle_enabled=self._handle_toggle_step,
            on_delete=self._handle_delete_step,
            on_click=self._handle_edit_step,
            on_execute=self._handle_execute_step,
            on_add_child=self._handle_add_child_step,  # F4
        )

    def _render_step_cards(self) -> list[StepCard]:
        """批量渲染所有步骤卡片（保留兼容）"""
        return [
            self._build_step_card(step, i)
            for i, step in enumerate(self._steps)
        ]

    def _refresh_step_list(self) -> None:
        """刷新步骤列表控件"""
        self._steps_list.set_items(self._steps)
        # F9c：同步 section-title 的步骤计数
        if self._section_title is not None and len(self._section_title.controls) >= 2:
            self._section_title.controls[1] = ft.Text(
                f"共 {len(self._steps)} 项",
                size=12,
                color="#6b7280",
            )
        try:
            self._page.update()
        except Exception:
            pass

    # ---- 拖拽 / 换位回调（Q24-Q29）----

    def _handle_reorder(self, old_index: int, new_index: int) -> None:
        """拖拽或换位后重排序（Q24-Q29）"""
        # 同步 self._steps 的顺序与 DraggableList 内部一致
        if old_index == new_index:
            return
        if not (0 <= old_index < len(self._steps)):
            return
        if not (0 <= new_index < len(self._steps)):
            return
        item = self._steps.pop(old_index)
        insert_at = min(new_index, len(self._steps))
        self._steps.insert(insert_at, item)
        # 重新编号 step_order
        for i, s in enumerate(self._steps, 1):
            s.step_order = i
        # 刷新 DraggableList（重新渲染以反映新序号）
        self._steps_list.set_items(self._steps)
        # 修正调用方式：step_moved 接受 (step_name, new_position)
        moved_name = next((s.name_zh for s in self._steps if s.step_order == new_index + 1), "")
        self._notifier.step_moved(moved_name, new_index + 1)

    # ---- 事件处理 ----

    def _handle_add_step(self, e: ft.ControlEvent | None = None) -> None:
        """打开抽屉添加新步骤（顶层）"""
        # F4：清除父步骤标记，确保是顶层添加
        self._editing_parent_id = None
        self._drawer.start_add()
        self._show_drawer()

    def _handle_edit_step(self, step_id: str) -> None:
        """点击步骤卡片编辑"""
        # F4：编辑顶层步骤时清除父步骤标记
        self._editing_parent_id = None
        step = next((s for s in self._steps if s.step_id == step_id), None)
        if step is None:
            return
        self._drawer.start_edit(step)
        self._show_drawer()

    def _handle_execute_step(self, step_id: str) -> None:
        """执行单个步骤（需求9/F5）

        M7 执行引擎未完成时，仅弹出 SnackBar 提示。
        M7 完成后调用 executor_service.run_single_step(step_id)。
        """
        step = next((s for s in self._steps if s.step_id == step_id), None)
        if step is None:
            return
        meta = get_step_type_meta(step.step_type)
        if meta.status == StepStatus.NOT_IMPLEMENTED:
            self._notifier.warning(f"步骤「{step.name_zh}」尚未实现，已跳过")
            return
        if not step.enabled:
            self._notifier.warning(f"步骤「{step.name_zh}」已禁用，请先启用")
            return
        # M7 未完成：占位实现
        self._notifier.info(f"开始执行步骤「{step.name_zh}」（M7 引擎待接入）")

    def _handle_add_child_step(self, parent_step_id: str) -> None:
        """添加子步骤到指定父步骤（需求7/F4）

        当前实现：弹出抽屉添加新步骤，保存时将其加入父步骤的 children 列表。
        M1 任务管理接入后，可改为独立的关系表存储。
        """
        parent = next((s for s in self._steps if s.step_id == parent_step_id), None)
        if parent is None:
            return
        self._editing_parent_id = parent_step_id
        self._drawer.start_add()
        self._show_drawer()
        self._notifier.info(f"正在为「{parent.name_zh}」添加子步骤")

    def _handle_open_settings(self, e: ft.ControlEvent | None = None) -> None:
        """打开设置页（需求6/F3）"""
        self._page.go("/settings")

    def _handle_save_step(
        self,
        step_id: str | None,
        step_type: StepType,
        params: dict,
        errors: list[str],
    ) -> None:
        """保存步骤（添加 or 更新）

        F4：如果 _editing_parent_id 不为 None，将新步骤加入父步骤的 children
        """
        if errors:
            # 校验失败，显示错误
            self._notifier.error("校验失败：" + "；".join(errors[:2]))
            return

        meta = get_step_type_meta(step_type)
        if step_id is None:
            # 新增
            new_step = StepCardData(
                step_id=f"step_{len(self._steps) + 1:03d}",
                step_order=len(self._steps) + 1,
                step_type=step_type,
                name_zh=meta.name_zh,
                params=params,
                enabled=True,
                is_placeholder=meta.status == StepStatus.NOT_IMPLEMENTED,
            )
            if self._editing_parent_id is not None:
                # F4：添加为子步骤
                parent = next(
                    (s for s in self._steps if s.step_id == self._editing_parent_id),
                    None,
                )
                if parent is not None:
                    # 子步骤 ID 用 parent_id_child_N 格式
                    new_step.step_id = (
                        f"{self._editing_parent_id}_child_{len(parent.children) + 1}"
                    )
                    parent.children.append(new_step)
                    self._notifier.step_saved(f"{parent.name_zh} → {meta.name_zh}")
                # 清除父步骤标记
                self._editing_parent_id = None
                self._refresh_step_list()
                self._hide_drawer()
                return
            # 顶层新增
            self._steps.append(new_step)
            if meta.status == StepStatus.NOT_IMPLEMENTED:
                self._notifier.placeholder_saved(meta.name_zh)
            else:
                self._notifier.step_saved(meta.name_zh)
        else:
            # 更新
            for i, s in enumerate(self._steps):
                if s.step_id == step_id:
                    self._steps[i] = StepCardData(
                        step_id=s.step_id,
                        step_order=s.step_order,
                        step_type=step_type,
                        name_zh=meta.name_zh,
                        params=params,
                        enabled=s.enabled,
                        is_placeholder=meta.status == StepStatus.NOT_IMPLEMENTED,
                    )
                    break
            self._notifier.step_saved(meta.name_zh)

        self._refresh_step_list()
        self._hide_drawer()

    def _handle_close_drawer(self) -> None:
        """关闭抽屉（Q20 决策：检查 dirty）"""
        if self._drawer.is_dirty():
            # 弹保存确认对话框
            self._show_unsaved_dialog()
            return
        self._hide_drawer()

    def _show_unsaved_dialog(self) -> None:
        """Q20：未保存离开对话框"""
        dialog = ft.AlertDialog(
            title=ft.Text("有未保存的修改"),
            content=ft.Text("当前编辑有未保存的修改，要怎么处理？"),
            actions=[
                ft.Button(
                    "不保存退出",
                    on_click=lambda e: self._handle_dialog_choice("discard"),
                ),
                ft.Button(
                    "继续编辑",
                    on_click=lambda e: self._handle_dialog_choice("continue"),
                ),
                ft.Button(
                    "保存并退出",
                    on_click=lambda e: self._handle_dialog_choice("save"),
                    bgcolor="#2563eb",
                    color="white",
                ),
            ],
        )
        # 添加到 page.overlay 显示
        self._page.overlay.append(dialog)
        dialog.open = True
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_dialog_choice(self, choice: str) -> None:
        """处理对话框选择"""
        # 关闭对话框
        for ctrl in list(self._page.overlay):
            if isinstance(ctrl, ft.AlertDialog):
                ctrl.open = False
        try:
            self._page.update()
        except Exception:
            pass

        if choice == "save":
            # 触发保存（_handle_save 不使用 e 参数，传 None 安全）
            self._drawer._handle_save(None)  # type: ignore[arg-type]
        elif choice == "discard":
            self._hide_drawer()
        elif choice == "continue":
            pass  # 关闭对话框，继续编辑

    def _handle_toggle_step(self, step_id: str, enabled: bool) -> None:
        """启用/禁用步骤"""
        # 同步 self._steps 与 DraggableList._items
        for s in self._steps:
            if s.step_id == step_id:
                s.enabled = enabled
                break
        # 同步 DraggableList 内部数据
        for item in self._steps_list.get_items():
            if getattr(item, "step_id", None) == step_id:
                item.enabled = enabled
                break
        # 不重新渲染整个列表（避免闪烁），只更新页面
        self._notifier.info(f"已{'启用' if enabled else '禁用'}步骤")
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_delete_step(self, step_id: str) -> None:
        """删除步骤"""
        step = next((s for s in self._steps if s.step_id == step_id), None)
        if step is None:
            return
        name = step.name_zh
        self._steps = [s for s in self._steps if s.step_id != step_id]
        # 重新编号
        for i, s in enumerate(self._steps, 1):
            s.step_order = i
        self._refresh_step_list()
        self._notifier.step_deleted(name)

    def _handle_back(self, e: ft.ControlEvent | None = None) -> None:
        """返回（步骤编辑器是首屏，无返回目标，留空）"""
        # 需求6：一进入就是步骤界面，无返回按钮
        pass

    # ---- 抽屉显示/隐藏 ----

    def _show_drawer(self) -> None:
        """显示抽屉"""
        self._overlay.visible = True
        self._overlay.bgcolor = "#80000000"  # 半透明黑
        try:
            self._page.update()
        except Exception:
            pass

    def _hide_drawer(self) -> None:
        """隐藏抽屉"""
        self._overlay.visible = False
        self._overlay.bgcolor = "#00000000"
        try:
            self._page.update()
        except Exception:
            pass
