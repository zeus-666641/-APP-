"""通用可拖拽列表组件（M2-T2.8）

按 Q24-Q29 决策落地：
- Q24：拖拽 + 换位按钮双保险（按钮可独立开关）
- Q25：仅同级排序，不主动提示嵌套
- Q26：拖拽手柄在右侧（默认），可配置左/右
- Q27：拖动时手柄半透明灰色占位
- Q28：合并 ↑/↓ 为单个"换位"按钮 → 弹输入框 → 输入目标行号 → 一键移动
- Q29：输入超范围 → 二级确认对话框（移动到第 1 行 / 最后一行）

设计要点（B2 修复后版本）：
- **关键修复**：Draggable 仅包裹"拖拽手柄"，不再包裹整个 content
  原因：Flet 不允许同一控件对象被两个父控件同时引用（原版 content 被
  Draggable.content 与 placeholder.content 同时引用，导致 Switch、
  IconButton 等子控件的事件被吞，开关/删除/换位按钮全部无响应）。
- 每行结构：DragTarget(Container(Row[handle?, content, handle?, swap_btn?]))
- 手柄结构：Draggable(IconButton(...))
- max_simultaneous_drags=1 避免多指混乱
- on_accept 通过 e.src.data（key）反查 src_index
- 移动语义（非交换）：从 old_index 取出，插入到 new_index，其他项顺延
"""
from __future__ import annotations

from typing import Any, Callable, Literal

import flet as ft


# ---- 默认配置常量 ----

_DEFAULT_GROUP_PREFIX = "draggable_list"
_DEFAULT_SPACING = 8
_PLACEHOLDER_OPACITY = 0.4
_PLACEHOLDER_BGCOLOR = "#f1f5f9"

_HANDLE_ICON = ft.Icons.DRAG_HANDLE
_HANDLE_COLOR = "#94a3b8"
_HANDLE_COLOR_DRAGGING = "#cbd5e1"  # 拖拽中手柄半透明灰
_SWAP_ICON = ft.Icons.SWAP_VERT
_SWAP_COLOR = "#6b7280"


class DraggableList(ft.Column):
    """通用可拖拽列表

    Attributes:
        items: 数据项列表（任意类型）
        item_builder: 渲染单个 item 的回调 (item, index) -> Control
        on_reorder: 重排序回调 (old_index, new_index) -> None
        show_drag_handle: 是否显示拖拽手柄（默认 True）
        show_swap_button: 是否显示换位按钮（默认 True）
        drag_handle_side: 手柄位置 "left" | "right"（默认 "right"，Q26）
        key_extractor: 从 item 提取唯一 key 的回调（默认用 id()）
        page: ft.Page 引用（用于弹对话框，可选；为 None 时换位按钮不弹对话框）
    """

    def __init__(
        self,
        items: list[Any] | None = None,
        item_builder: Callable[[Any, int], ft.Control] | None = None,
        on_reorder: Callable[[int, int], None] | None = None,
        show_drag_handle: bool = True,
        show_swap_button: bool = True,
        drag_handle_side: Literal["left", "right"] = "right",
        key_extractor: Callable[[Any], str] | None = None,
        page: ft.Page | None = None,
        spacing: int = _DEFAULT_SPACING,
    ) -> None:
        self._items: list[Any] = list(items) if items is not None else []
        self._item_builder = item_builder or _default_item_builder
        self._on_reorder = on_reorder
        self._show_drag_handle = show_drag_handle
        self._show_swap_button = show_swap_button
        self._drag_handle_side = drag_handle_side
        self._key_extractor = key_extractor or (lambda x: str(id(x)))
        self._page = page
        # 每个 DraggableList 实例独立 group，避免多个列表互相接受拖拽
        self._group = f"{_DEFAULT_GROUP_PREFIX}_{id(self)}"
        # 拖拽中状态：记录当前正在拖拽的 index，用于高亮
        self._dragging_index: int | None = None

        super().__init__(
            controls=self._render_items(),
            spacing=spacing,
        )

    # ---- 渲染 ----

    def _render_items(self) -> list[ft.Control]:
        """渲染所有项"""
        return [
            self._build_item(item, idx)
            for idx, item in enumerate(self._items)
        ]

    def _build_item(self, item: Any, index: int) -> ft.DragTarget:
        """构建单个可拖拽项

        结构（B2 修复后）：
            DragTarget(
                content=Container(
                    content=Row[handle?, content, handle?, swap_btn?]
                ),
                on_accept=...
            )

        手柄是独立的 Draggable（不再包裹整个 content）。
        """
        key = self._key_extractor(item)
        content = self._item_builder(item, index)

        # 拖拽手柄（Q26）：独立 Draggable，content_when_dragging 是手柄自己的占位
        handle_placeholder = ft.IconButton(
            icon=_HANDLE_ICON,
            icon_size=18,
            icon_color=_HANDLE_COLOR_DRAGGING,
            tooltip="拖动中",
            disabled=True,
        )
        drag_handle = ft.Draggable(
            content=ft.IconButton(
                icon=_HANDLE_ICON,
                icon_size=18,
                icon_color=_HANDLE_COLOR,
                tooltip="拖动排序",
            ),
            group=self._group,
            content_when_dragging=handle_placeholder,
            data=key,
            max_simultaneous_drags=1,
        )

        # 换位按钮（Q28）
        swap_btn = ft.IconButton(
            icon=_SWAP_ICON,
            icon_size=18,
            icon_color=_SWAP_COLOR,
            tooltip="换位",
            on_click=lambda e, idx=index: self._handle_swap_click(idx),
        )

        # 组装 Row：content 不被 Draggable 包裹，事件可正常触发
        row_children: list[ft.Control] = []
        if self._show_drag_handle and self._drag_handle_side == "left":
            row_children.append(drag_handle)
        row_children.append(content)
        if self._show_drag_handle and self._drag_handle_side == "right":
            row_children.append(drag_handle)
        if self._show_swap_button:
            row_children.append(swap_btn)

        # DragTarget 包裹整行（接受拖拽放置）
        return ft.DragTarget(
            content=ft.Container(
                content=ft.Row(
                    controls=row_children,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            group=self._group,
            on_accept=lambda e, target_idx=index: self._handle_drop(e, target_idx),
            on_will_accept=lambda e, target_idx=index: self._handle_will_accept(target_idx),
            on_leave=lambda e, target_idx=index: self._handle_leave(target_idx),
            data=index,
        )

    # ---- 拖拽处理 ----

    def _handle_will_accept(self, target_index: int) -> None:
        """拖拽悬停时高亮目标行（Q27 视觉反馈）"""
        # 简单实现：不做强样式变更，避免重新渲染引起的事件丢失
        pass

    def _handle_leave(self, target_index: int) -> None:
        """拖拽离开目标行"""
        pass

    def _handle_drop(self, e: ft.DragTargetAcceptEvent, target_index: int) -> None:
        """处理拖拽放置（Q24 真拖拽）"""
        src = getattr(e, "src", None)
        if src is None:
            return
        src_key = getattr(src, "data", None)
        if src_key is None:
            return
        # 反查 src_index
        src_index = self._find_index_by_key(src_key)
        if src_index is None or src_index == target_index:
            return
        # 执行移动
        self._reorder(src_index, target_index)

    def _find_index_by_key(self, key: str) -> int | None:
        """根据 key 反查 index"""
        for i, item in enumerate(self._items):
            if self._key_extractor(item) == key:
                return i
        return None

    def _reorder(self, old_index: int, new_index: int) -> None:
        """移动：从 old_index 取出，占据 new_index 位置（其他项顺延）

        语义为「占据 new_index 位置」（直观移动），不是 Flutter 的「插入到 new_index 之前」。
        例：[A,B,C,D] 把 A(0) 移到 2 → [B,C,A,D]
        """
        if old_index == new_index:
            return
        n = len(self._items)
        if not (0 <= old_index < n):
            return
        if not (0 <= new_index < n):
            return
        item = self._items.pop(old_index)
        # pop 后 list 长度 = n-1，new_index 可能等于 n-1（末尾插入合法）
        insert_at = min(new_index, len(self._items))
        self._items.insert(insert_at, item)
        # 重新渲染
        self.controls = self._render_items()
        try:
            self.update()
        except Exception:
            pass
        # 回调传原始 new_index（不是 clamp 后的）
        if self._on_reorder:
            self._on_reorder(old_index, new_index)

    # ---- 换位按钮处理（Q28）----

    def _handle_swap_click(self, current_index: int) -> None:
        """换位按钮点击：弹输入对话框"""
        if self._page is None:
            return

        total = len(self._items)
        text_field = ft.TextField(
            label=f"目标行号 (1-{total})",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )

        def handle_swap_confirm(e: ft.ControlEvent) -> None:
            raw = text_field.value or ""
            raw = raw.strip()
            if not raw or not raw.lstrip("-").isdigit():
                return
            target = int(raw)
            # 关闭输入对话框
            _close_dialog()
            # 校验并执行
            self._handle_swap_with_validation(current_index, target, total)

        def _close_dialog() -> None:
            dialog.open = False
            try:
                self._page.update()
            except Exception:
                pass
            # 从 overlay 移除
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("换位"),
            content=ft.Column(
                controls=[
                    ft.Text(f"当前是第 {current_index + 1} 行，共 {total} 行"),
                    text_field,
                ],
                tight=True,
            ),
            actions=[
                ft.Button("取消", on_click=lambda e: _close_dialog()),
                ft.Button(
                    "一键调换",
                    on_click=handle_swap_confirm,
                    bgcolor="#2563eb",
                    color="white",
                ),
            ],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_swap_with_validation(
        self, current_index: int, target: int, total: int
    ) -> None:
        """校验目标行号并执行移动（Q29）"""
        # target 是 1-based
        if target < 1:
            # Q29：小于 1 → 提示是否移动到第 1 行
            self._show_boundary_confirm(
                current_index=current_index,
                boundary_index=0,
                reason=f"输入的行号 {target} 小于 1",
                boundary_label="第 1 行",
            )
        elif target > total:
            # Q29：大于最后一行 → 提示是否移动到最后一行
            self._show_boundary_confirm(
                current_index=current_index,
                boundary_index=total - 1,
                reason=f"输入的行号 {target} 大于总行数 {total}",
                boundary_label="最后一行",
            )
        elif target - 1 == current_index:
            # 与当前位置相同
            self._show_same_position_notice()
        else:
            # 正常移动
            self._reorder(current_index, target - 1)

    def _show_boundary_confirm(
        self,
        current_index: int,
        boundary_index: int,
        reason: str,
        boundary_label: str,
    ) -> None:
        """Q29：超出范围时弹二级确认对话框"""
        if self._page is None:
            return

        def _close() -> None:
            dialog.open = False
            try:
                self._page.update()
            except Exception:
                pass
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)

        def _confirm() -> None:
            _close()
            self._reorder(current_index, boundary_index)

        dialog = ft.AlertDialog(
            title=ft.Text("行号超出范围"),
            content=ft.Text(f"{reason}，是否移动到{boundary_label}？"),
            actions=[
                ft.Button("取消", on_click=lambda e: _close()),
                ft.Button(
                    "确认移动",
                    on_click=lambda e: _confirm(),
                    bgcolor="#2563eb",
                    color="white",
                ),
            ],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        try:
            self._page.update()
        except Exception:
            pass

    def _show_same_position_notice(self) -> None:
        """提示目标位置与当前位置相同"""
        if self._page is None:
            return

        def _close() -> None:
            dialog.open = False
            try:
                self._page.update()
            except Exception:
                pass
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("提示"),
            content=ft.Text("目标位置与当前位置相同"),
            actions=[
                ft.Button("知道了", on_click=lambda e: _close()),
            ],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        try:
            self._page.update()
        except Exception:
            pass

    # ---- 公共 API ----

    def set_items(self, items: list[Any]) -> None:
        """更新数据项并重新渲染"""
        self._items = list(items)
        self.controls = self._render_items()
        try:
            self.update()
        except Exception:
            pass

    def get_items(self) -> list[Any]:
        """获取当前顺序的数据项"""
        return list(self._items)

    def set_show_drag_handle(self, show: bool) -> None:
        """动态切换拖拽手柄显隐（Q28：设置中可开关）"""
        self._show_drag_handle = show
        self.controls = self._render_items()
        try:
            self.update()
        except Exception:
            pass

    def set_show_swap_button(self, show: bool) -> None:
        """动态切换换位按钮显隐（Q28：设置中可开关）"""
        self._show_swap_button = show
        self.controls = self._render_items()
        try:
            self.update()
        except Exception:
            pass

    def set_drag_handle_side(self, side: Literal["left", "right"]) -> None:
        """动态切换手柄位置（Q26：设置中可切换）"""
        self._drag_handle_side = side
        self.controls = self._render_items()
        try:
            self.update()
        except Exception:
            pass


# ---- 默认 item_builder（用于测试和兜底）----


def _default_item_builder(item: Any, index: int) -> ft.Control:
    """默认 item 渲染：用 Text 显示 str(item)"""
    return ft.Text(str(item), size=14)
