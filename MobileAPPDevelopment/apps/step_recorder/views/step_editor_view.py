"""步骤编辑器主视图（M2-T2.7 首次可运行 + T2.8 拖拽列表）

按 Q21-Q29 决策落地：
- Q21 抽屉式侧滑：右侧滑出宽度 80%，含 StepTypePicker + ParamEditor
- Q22 双入口：FAB（默认）+ 顶部 AppBar 按钮，二者调用同一 add 流程
- Q23 mock 3-5 条示例步骤：覆盖 AVAILABLE/LIMITED/NOT_IMPLEMENTED 三种状态
- Q20 未保存离开：编辑抽屉关闭前检查 dirty，弹 AlertDialog 三选一
- Q24-Q29 DraggableList：拖拽手柄 + 换位按钮（输入目标行号），可独立开关

入口：page.go("/step_editor")
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
    """步骤编辑器主视图

    集成：
    - AppBar（返回 + 标题 + 顶部"添加"按钮）
    - 步骤列表 ListView（StepCard 渲染）
    - FAB 浮动按钮（默认添加入口）
    - 编辑抽屉（StepEditorDrawer）
    - Q20 未保存离开 AlertDialog
    """

    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._notifier = Notifier(page)
        self._steps: list[StepCardData] = _default_mock_steps()
        self._drawer_visible = False

        # 步骤列表（Q24-Q29：DraggableList 替换原 ListView）
        self._steps_list = DraggableList(
            items=self._steps,
            item_builder=self._build_step_card,
            on_reorder=self._handle_reorder,
            key_extractor=lambda s: s.step_id,
            page=page,
            show_drag_handle=True,    # Q28：默认显示
            show_swap_button=True,    # Q28：默认显示
            drag_handle_side="right", # Q26：默认右侧
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
        """主内容区：AppBar + 步骤列表 + FAB"""
        appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self._handle_back,
            ),
            title=ft.Text("步骤编辑器"),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="添加步骤",
                    on_click=self._handle_add_step,
                ),
            ],
            bgcolor="#2563eb",
            color="white",
        )

        # FAB（Q22 决策：默认入口）
        fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=self._handle_add_step,
            bgcolor="#2563eb",
            tooltip="添加步骤",
        )

        return ft.Column(
            controls=[
                appbar,
                ft.SafeArea(
                    content=ft.Stack(
                        controls=[
                            self._steps_list,
                            ft.Container(
                                content=fab,
                                alignment=ft.Alignment.BOTTOM_RIGHT,
                                padding=ft.Padding(left=0, right=16, top=0, bottom=16),
                            ),
                        ],
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
        self._notifier.step_moved(f"从第 {old_index + 1} 行移到第 {new_index + 1} 行")

    # ---- 事件处理 ----

    def _handle_add_step(self, e: ft.ControlEvent | None = None) -> None:
        """打开抽屉添加新步骤"""
        self._drawer.start_add()
        self._show_drawer()

    def _handle_edit_step(self, step_id: str) -> None:
        """点击步骤卡片编辑"""
        step = next((s for s in self._steps if s.step_id == step_id), None)
        if step is None:
            return
        self._drawer.start_edit(step)
        self._show_drawer()

    def _handle_save_step(
        self,
        step_id: str | None,
        step_type: StepType,
        params: dict,
        errors: list[str],
    ) -> None:
        """保存步骤（添加 or 更新）"""
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
            self._steps.append(new_step)
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
        for s in self._steps:
            if s.step_id == step_id:
                s.enabled = enabled
                break
        # 不重新渲染整个列表（避免闪烁）
        self._notifier.info(f"已{'启用' if enabled else '禁用'}步骤")

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
        """返回上一页"""
        self._page.go("/home")

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
