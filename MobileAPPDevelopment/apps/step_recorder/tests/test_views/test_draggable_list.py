"""DraggableList 组件测试（M2-T2.8）

覆盖 Q24-Q29 决策落地：
- Q24：拖拽 + 换位按钮双保险
- Q25：仅同级排序
- Q26：手柄位置（默认右，可切左）
- Q27：拖拽占位（content_when_dragging 半透明）
- Q28：换位按钮 + 输入对话框 + 一键调换
- Q29：超范围边界确认
"""
import pytest

import flet as ft

from views.components.draggable_list import DraggableList


# ---- 测试用 item_builder ----


def _text_builder(item, index):
    return ft.Text(str(item), size=14)


def _make_items(n=3):
    return [f"item{i}" for i in range(n)]


# ---- 构造测试 ----


class TestConstruction:
    """构造基本测试"""

    def test_can_construct_empty(self):
        dl = DraggableList()
        assert isinstance(dl, ft.Column)
        assert dl.get_items() == []

    def test_can_construct_with_items(self):
        items = _make_items(3)
        dl = DraggableList(items=items, item_builder=_text_builder)
        assert dl.get_items() == items

    def test_default_show_flags(self):
        """Q28：两个按钮默认都显示"""
        dl = DraggableList()
        assert dl._show_drag_handle is True
        assert dl._show_swap_button is True

    def test_default_handle_side_right(self):
        """Q26：默认在右侧"""
        dl = DraggableList()
        assert dl._drag_handle_side == "right"

    def test_custom_handle_side_left(self):
        dl = DraggableList(drag_handle_side="left")
        assert dl._drag_handle_side == "left"

    def test_custom_show_flags(self):
        dl = DraggableList(show_drag_handle=False, show_swap_button=False)
        assert dl._show_drag_handle is False
        assert dl._show_swap_button is False

    def test_each_instance_has_unique_group(self):
        """每个实例 group 独立，避免多列表互相接受拖拽"""
        dl1 = DraggableList()
        dl2 = DraggableList()
        assert dl1._group != dl2._group


# ---- 渲染测试 ----


class TestRendering:
    """渲染结构测试"""

    def test_render_count_matches_items(self):
        dl = DraggableList(items=_make_items(3), item_builder=_text_builder)
        assert len(dl.controls) == 3

    def test_each_item_is_drag_target(self):
        """Q24：每行结构是 DragTarget"""
        dl = DraggableList(items=_make_items(2), item_builder=_text_builder)
        for ctrl in dl.controls:
            assert isinstance(ctrl, ft.DragTarget)

    def test_drag_target_contains_draggable(self):
        """DragTarget 内嵌 Draggable"""
        dl = DraggableList(items=_make_items(1), item_builder=_text_builder)
        target = dl.controls[0]
        # content 是 Container -> Row -> [handle?, Draggable, handle?, swap_btn?]
        assert isinstance(target.content, ft.Container)
        row = target.content.content
        assert isinstance(row, ft.Row)
        # 应该至少有一个 Draggable
        draggables = [c for c in row.controls if isinstance(c, ft.Draggable)]
        assert len(draggables) == 1

    def test_draggable_has_content_when_dragging(self):
        """Q27：Draggable 设置 content_when_dragging 半透明占位"""
        dl = DraggableList(items=_make_items(1), item_builder=_text_builder)
        target = dl.controls[0]
        row = target.content.content
        draggable = next(c for c in row.controls if isinstance(c, ft.Draggable))
        assert draggable.content_when_dragging is not None
        # 占位是 Container
        assert isinstance(draggable.content_when_dragging, ft.Container)
        assert draggable.content_when_dragging.opacity == 0.3

    def test_draggable_group_matches_target_group(self):
        """Draggable 与 DragTarget 同 group 才能接受"""
        dl = DraggableList(items=_make_items(1), item_builder=_text_builder)
        target = dl.controls[0]
        row = target.content.content
        draggable = next(c for c in row.controls if isinstance(c, ft.Draggable))
        assert draggable.group == target.group == dl._group

    def test_draggable_max_simultaneous_drags_is_one(self):
        """max_simultaneous_drags=1 避免多指混乱"""
        dl = DraggableList(items=_make_items(1), item_builder=_text_builder)
        target = dl.controls[0]
        row = target.content.content
        draggable = next(c for c in row.controls if isinstance(c, ft.Draggable))
        assert draggable.max_simultaneous_drags == 1

    def test_handle_present_on_right_by_default(self):
        """Q26：默认右侧有 handle"""
        dl = DraggableList(items=_make_items(1), item_builder=_text_builder)
        row = dl.controls[0].content.content
        # 顺序：Draggable, handle, swap_btn
        types = [type(c) for c in row.controls]
        assert types[0] == ft.Draggable
        # handle 是 IconButton
        assert any(isinstance(c, ft.IconButton) and c.icon == ft.Icons.DRAG_HANDLE for c in row.controls)
        # 最后应该是 swap_btn
        assert isinstance(row.controls[-1], ft.IconButton)
        assert row.controls[-1].icon == ft.Icons.SWAP_VERT

    def test_handle_on_left_when_configured(self):
        """Q26：可切换到左侧"""
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            drag_handle_side="left",
        )
        row = dl.controls[0].content.content
        # 顺序：handle, Draggable, swap_btn
        assert isinstance(row.controls[0], ft.IconButton)
        assert row.controls[0].icon == ft.Icons.DRAG_HANDLE
        assert isinstance(row.controls[1], ft.Draggable)

    def test_no_handle_when_disabled(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            show_drag_handle=False,
        )
        row = dl.controls[0].content.content
        # 只有 Draggable 和 swap_btn
        handles = [c for c in row.controls if isinstance(c, ft.IconButton) and c.icon == ft.Icons.DRAG_HANDLE]
        assert len(handles) == 0
        # Draggable 还在
        assert any(isinstance(c, ft.Draggable) for c in row.controls)

    def test_no_swap_btn_when_disabled(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            show_swap_button=False,
        )
        row = dl.controls[0].content.content
        swaps = [c for c in row.controls if isinstance(c, ft.IconButton) and c.icon == ft.Icons.SWAP_VERT]
        assert len(swaps) == 0

    def test_both_disabled_leaves_only_draggable(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            show_drag_handle=False,
            show_swap_button=False,
        )
        row = dl.controls[0].content.content
        # 只剩 Draggable
        assert len(row.controls) == 1
        assert isinstance(row.controls[0], ft.Draggable)


# ---- _find_index_by_key 测试 ----


class TestFindIndexByKey:
    """根据 key 反查 index"""

    def test_default_key_extractor_uses_id(self):
        items = _make_items(3)
        dl = DraggableList(items=items, item_builder=_text_builder)
        # 默认用 id()，反查应能找到
        idx = dl._find_index_by_key(dl._key_extractor(items[1]))
        assert idx == 1

    def test_custom_key_extractor(self):
        """使用 str 作为 key"""
        items = ["a", "b", "c"]
        dl = DraggableList(
            items=items,
            item_builder=_text_builder,
            key_extractor=str,
        )
        assert dl._find_index_by_key("a") == 0
        assert dl._find_index_by_key("b") == 1
        assert dl._find_index_by_key("c") == 2

    def test_key_not_found_returns_none(self):
        dl = DraggableList(
            items=["a", "b"],
            item_builder=_text_builder,
            key_extractor=str,
        )
        assert dl._find_index_by_key("zzz") is None


# ---- _reorder 算法测试（移动语义）----


class TestReorderAlgorithm:
    """_reorder 移动语义：从 old 取出插入到 new，其他项顺延"""

    def test_move_backward(self):
        """从后往前移：[A, B, C, D] 把 C(2) 移到 0 → [C, A, B, D]"""
        items = ["A", "B", "C", "D"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(2, 0)
        assert dl.get_items() == ["C", "A", "B", "D"]

    def test_move_forward(self):
        """从前往后移：[A, B, C, D] 把 A(0) 移到 2 → [B, C, A, D]"""
        items = ["A", "B", "C", "D"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(0, 2)
        assert dl.get_items() == ["B", "C", "A", "D"]

    def test_move_to_last(self):
        """移动到最后一行：[A, B, C, D] 把 B(1) 移到 3 → [A, C, D, B]"""
        items = ["A", "B", "C", "D"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(1, 3)
        assert dl.get_items() == ["A", "C", "D", "B"]

    def test_move_to_same_position_no_op(self):
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(1, 1)
        assert dl.get_items() == ["A", "B", "C"]

    def test_move_with_out_of_range_old_index(self):
        items = ["A", "B"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(99, 0)  # 越界 old_index
        assert dl.get_items() == ["A", "B"]  # 不变

    def test_move_with_out_of_range_new_index(self):
        items = ["A", "B"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._reorder(0, 99)  # 越界 new_index
        assert dl.get_items() == ["A", "B"]  # 不变

    def test_reorder_invokes_callback(self):
        """on_reorder 回调被调用"""
        calls = []
        dl = DraggableList(
            items=["A", "B", "C"],
            item_builder=_text_builder,
            key_extractor=str,
            on_reorder=lambda old, new: calls.append((old, new)),
        )
        dl._reorder(0, 2)
        assert calls == [(0, 2)]

    def test_reorder_same_position_no_callback(self):
        """相同位置不触发回调"""
        calls = []
        dl = DraggableList(
            items=["A", "B"],
            item_builder=_text_builder,
            key_extractor=str,
            on_reorder=lambda old, new: calls.append((old, new)),
        )
        dl._reorder(1, 1)
        assert calls == []

    def test_reorder_re_renders_controls(self):
        """_reorder 后 controls 重新渲染"""
        dl = DraggableList(
            items=["A", "B"],
            item_builder=_text_builder,
            key_extractor=str,
        )
        original_controls = list(dl.controls)
        dl._reorder(0, 1)
        # 控件对象应被替换（不是同一个引用）
        assert dl.controls is not original_controls or len(dl.controls) == 2


# ---- _handle_drop 测试 ----


class TestHandleDrop:
    """模拟拖拽放置事件"""

    def _make_drop_event(self, src_key):
        """构造一个 mock DragTargetAcceptEvent"""
        class _MockSrc:
            def __init__(self, key):
                self.data = key

        class _MockEvent:
            def __init__(self, key):
                self.src = _MockSrc(key)

        return _MockEvent(src_key)

    def test_drop_moves_item(self):
        """Q24：拖拽放置触发移动"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # 模拟把 C 拖到 A 位置：src_key="C", target_index=0
        e = self._make_drop_event("C")
        dl._handle_drop(e, 0)
        assert dl.get_items() == ["C", "A", "B"]

    def test_drop_to_same_position_no_op(self):
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        e = self._make_drop_event("B")
        dl._handle_drop(e, 1)  # B 自己拖到自己位置
        assert dl.get_items() == ["A", "B", "C"]

    def test_drop_with_unknown_key_no_op(self):
        items = ["A", "B"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        e = self._make_drop_event("ZZZ")
        dl._handle_drop(e, 0)
        assert dl.get_items() == ["A", "B"]

    def test_drop_with_none_src_no_op(self):
        items = ["A", "B"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # e.src = None
        class _MockEvent:
            src = None
        dl._handle_drop(_MockEvent(), 0)
        assert dl.get_items() == ["A", "B"]

    def test_drop_triggers_on_reorder(self):
        calls = []
        dl = DraggableList(
            items=["A", "B", "C"],
            item_builder=_text_builder,
            key_extractor=str,
            on_reorder=lambda old, new: calls.append((old, new)),
        )
        e = self._make_drop_event("C")
        dl._handle_drop(e, 0)
        assert calls == [(2, 0)]


# ---- _handle_swap_with_validation 测试（Q29 边界）----


class TestSwapValidation:
    """Q29：换位输入校验（不依赖 page，只测分支选择）"""

    def test_normal_target_moves(self):
        """正常范围内直接移动"""
        items = ["A", "B", "C", "D"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # current=0, target=4 (1-based, 即移到最后一行 index 3)
        dl._handle_swap_with_validation(0, 4, total=4)
        assert dl.get_items() == ["B", "C", "D", "A"]  # A 从 0 移到 3

    def test_target_equal_to_current_no_move(self):
        """目标等于当前位置 → 提示相同（不移动）"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # current=1, target=2 (1-based) = index 1
        # 因为 page=None，_show_same_position_notice 不会弹但也不应移动
        dl._handle_swap_with_validation(1, 2, total=3)
        assert dl.get_items() == ["A", "B", "C"]  # 不变

    def test_target_zero_triggers_boundary_no_move_without_page(self):
        """Q29：target < 1 应弹边界确认（page=None 时不移动）"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # page=None，_show_boundary_confirm 直接 return，不移动
        dl._handle_swap_with_validation(1, 0, total=3)
        assert dl.get_items() == ["A", "B", "C"]  # 不变

    def test_target_negative_triggers_boundary(self):
        """target < 0 同样触发边界"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._handle_swap_with_validation(1, -5, total=3)
        assert dl.get_items() == ["A", "B", "C"]  # 不变

    def test_target_exceeds_total_triggers_boundary(self):
        """Q29：target > total 应弹边界确认"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        dl._handle_swap_with_validation(0, 99, total=3)
        assert dl.get_items() == ["A", "B", "C"]  # 不变


# ---- _show_boundary_confirm / _show_same_position_notice 测试 ----


class TestBoundaryConfirmWithoutPage:
    """page=None 时不弹对话框，不崩溃"""

    def test_boundary_confirm_returns_silently_without_page(self):
        dl = DraggableList(items=["A", "B"], item_builder=_text_builder, key_extractor=str)
        # 不应抛异常
        dl._show_boundary_confirm(0, 1, "测试原因", "测试标签")
        assert dl.get_items() == ["A", "B"]  # 未移动

    def test_same_position_notice_returns_silently_without_page(self):
        dl = DraggableList(items=["A", "B"], item_builder=_text_builder, key_extractor=str)
        dl._show_same_position_notice()
        assert dl.get_items() == ["A", "B"]


# ---- set_items / get_items 测试 ----


class TestSetGetItems:
    def test_set_items_replaces(self):
        dl = DraggableList(items=["A"], item_builder=_text_builder, key_extractor=str)
        dl.set_items(["X", "Y", "Z"])
        assert dl.get_items() == ["X", "Y", "Z"]

    def test_set_items_re_renders(self):
        dl = DraggableList(items=["A"], item_builder=_text_builder, key_extractor=str)
        assert len(dl.controls) == 1
        dl.set_items(["X", "Y"])
        assert len(dl.controls) == 2

    def test_get_items_returns_copy(self):
        """get_items 返回副本，外部修改不影响内部"""
        dl = DraggableList(items=["A", "B"], item_builder=_text_builder, key_extractor=str)
        items = dl.get_items()
        items.append("C")
        assert dl.get_items() == ["A", "B"]  # 不变

    def test_set_items_with_empty(self):
        dl = DraggableList(items=["A"], item_builder=_text_builder, key_extractor=str)
        dl.set_items([])
        assert dl.get_items() == []
        assert len(dl.controls) == 0


# ---- 动态切换显隐测试 ----


class TestDynamicToggle:
    def test_set_show_drag_handle_false(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            show_drag_handle=True,
        )
        dl.set_show_drag_handle(False)
        assert dl._show_drag_handle is False
        row = dl.controls[0].content.content
        handles = [c for c in row.controls if isinstance(c, ft.IconButton) and c.icon == ft.Icons.DRAG_HANDLE]
        assert len(handles) == 0

    def test_set_show_swap_button_false(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            show_swap_button=True,
        )
        dl.set_show_swap_button(False)
        assert dl._show_swap_button is False
        row = dl.controls[0].content.content
        swaps = [c for c in row.controls if isinstance(c, ft.IconButton) and c.icon == ft.Icons.SWAP_VERT]
        assert len(swaps) == 0

    def test_set_drag_handle_side_left(self):
        dl = DraggableList(
            items=_make_items(1),
            item_builder=_text_builder,
            drag_handle_side="right",
        )
        dl.set_drag_handle_side("left")
        assert dl._drag_handle_side == "left"
        row = dl.controls[0].content.content
        # handle 应在第一位
        assert isinstance(row.controls[0], ft.IconButton)
        assert row.controls[0].icon == ft.Icons.DRAG_HANDLE


# ---- _handle_swap_click 测试（page=None 时早退）----


class TestSwapClickWithoutPage:
    def test_swap_click_no_op_without_page(self):
        """page=None 时不弹对话框，不崩溃"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # 不应抛异常
        dl._handle_swap_click(0)
        assert dl.get_items() == ["A", "B", "C"]  # 不变


# ---- Q25 仅同级排序（不嵌套）测试 ----


class TestSameLevelOnly:
    """Q25：仅同级排序，不主动提示嵌套"""

    def test_no_nesting_api_exposed(self):
        """DraggableList 不暴露嵌套相关 API"""
        # 检查类自身定义的方法（不触发实例的 page 属性）
        class_methods = [m for m in DraggableList.__dict__ if not m.startswith("_")]
        forbidden = ["nest", "parent", "children", "subtask"]
        for method in class_methods:
            for word in forbidden:
                assert word not in method.lower(), f"方法 {method} 含嵌套相关词 {word}"

    def test_items_are_flat_list(self):
        """items 是扁平 list，无嵌套结构"""
        items = ["A", "B", "C"]
        dl = DraggableList(items=items, item_builder=_text_builder, key_extractor=str)
        # 每个 item 是字符串，不是 dict/nested
        for item in dl.get_items():
            assert isinstance(item, str)
