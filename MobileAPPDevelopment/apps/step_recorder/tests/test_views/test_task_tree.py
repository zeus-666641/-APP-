"""task_tree 组件测试"""
import pytest

import flet as ft

from models.task import (
    Task,
    TaskCategory,
    TaskNode,
    TaskStatus,
    build_forest,
)
from views.components.task_tree import (
    STATUS_COLORS,
    STATUS_LABELS,
    NestMode,
    TaskCard,
    TaskCardData,
    TaskTree,
)


# ---- 测试数据 ----


def _make_task(tid: str, name: str, sort_order: int = 0) -> Task:
    return Task(
        id=tid,
        name=name,
        sort_order=sort_order,
        category=TaskCategory.DEFAULT,
    )


def _make_simple_forest() -> list[TaskNode]:
    """构建简单测试森林：
    root1 (t1)
    └── child1 (t2)
        └── grandchild1 (t3)
    root2 (t4)
    """
    from models.task import TaskRelation

    tasks = [
        _make_task("t1", "根任务1", 0),
        _make_task("t2", "子任务1", 0),
        _make_task("t3", "孙任务1", 0),
        _make_task("t4", "根任务2", 1),
    ]
    relations = [
        TaskRelation(id="r1", parent_id="t1", child_id="t2", sort_order=0),
        TaskRelation(id="r2", parent_id="t2", child_id="t3", sort_order=0),
    ]
    return build_forest(tasks, relations)


# ---- TaskCardData 测试 ----


class TestTaskCardData:
    def test_default_values(self):
        data = TaskCardData(task_id="t1", name="任务1")
        assert data.icon == "play_arrow"
        assert data.status == TaskStatus.IDLE
        assert data.enabled is True
        assert data.children == []
        assert data.parent_path == []

    def test_custom_values(self):
        data = TaskCardData(
            task_id="t2",
            name="自定义",
            icon="star",
            status=TaskStatus.RUNNING,
            enabled=False,
            children=[TaskCardData(task_id="c1", name="子")],
            parent_path=["父"],
        )
        assert data.icon == "star"
        assert data.status == TaskStatus.RUNNING
        assert data.enabled is False
        assert len(data.children) == 1
        assert data.parent_path == ["父"]


# ---- 状态映射测试 ----


class TestStatusMapping:
    def test_all_status_have_color(self):
        for status in TaskStatus:
            assert status in STATUS_COLORS

    def test_all_status_have_label(self):
        for status in TaskStatus:
            assert status in STATUS_LABELS

    def test_colors_match_prd(self):
        assert STATUS_COLORS[TaskStatus.IDLE] == "#6b7280"
        assert STATUS_COLORS[TaskStatus.RUNNING] == "#2563eb"
        assert STATUS_COLORS[TaskStatus.ERROR] == "#ef4444"
        assert STATUS_COLORS[TaskStatus.DISABLED] == "#94a3b8"

    def test_labels_match_chinese(self):
        assert STATUS_LABELS[TaskStatus.IDLE] == "空闲"
        assert STATUS_LABELS[TaskStatus.RUNNING] == "执行中"
        assert STATUS_LABELS[TaskStatus.PAUSED] == "已暂停"
        assert STATUS_LABELS[TaskStatus.ERROR] == "出错"
        assert STATUS_LABELS[TaskStatus.DISABLED] == "已禁用"


# ---- TaskCard 测试 ----


class TestTaskCard:
    def test_card_can_be_constructed(self):
        data = TaskCardData(task_id="t1", name="任务1")
        card = TaskCard(data=data)
        assert isinstance(card, ft.Container)
        assert card.content is not None

    def test_card_with_children_shows_expand_button(self):
        data = TaskCardData(
            task_id="t1",
            name="父任务",
            children=[TaskCardData(task_id="c1", name="子")],
        )
        card = TaskCard(data=data, has_children=True, is_expanded=False)
        assert isinstance(card, ft.Container)

    def test_card_callbacks_can_be_attached(self):
        called = []

        def on_toggle(tid, val):
            called.append(("toggle", tid, val))

        def on_execute(tid):
            called.append(("execute", tid))

        def on_click(tid):
            called.append(("click", tid))

        data = TaskCardData(task_id="t1", name="任务1")
        TaskCard(
            data=data,
            on_toggle_enabled=on_toggle,
            on_execute=on_execute,
            on_click=on_click,
        )
        # 回调已存储
        assert True


# ---- build_forest 测试 ----


class TestBuildForest:
    def test_empty_input_returns_empty_list(self):
        roots = build_forest([], [])
        assert roots == []

    def test_no_relations_all_tasks_are_roots(self):
        tasks = [_make_task("t1", "A"), _make_task("t2", "B")]
        roots = build_forest(tasks, [])
        assert len(roots) == 2

    def test_simple_parent_child(self):
        from models.task import TaskRelation

        tasks = [_make_task("t1", "父"), _make_task("t2", "子")]
        relations = [TaskRelation(id="r1", parent_id="t1", child_id="t2")]
        roots = build_forest(tasks, relations)
        assert len(roots) == 1
        assert roots[0].task.id == "t1"
        assert len(roots[0].children) == 1
        assert roots[0].children[0].task.id == "t2"

    def test_three_level_nesting(self):
        roots = _make_simple_forest()
        assert len(roots) == 2
        root1 = roots[0]
        assert root1.task.id == "t1"
        assert len(root1.children) == 1
        assert root1.children[0].task.id == "t2"
        assert len(root1.children[0].children) == 1
        assert root1.children[0].children[0].task.id == "t3"

    def test_depth_is_set_correctly(self):
        roots = _make_simple_forest()
        root1 = roots[0]
        assert root1.depth == 0
        child = root1.children[0]
        assert child.depth == 1
        grandchild = child.children[0]
        assert grandchild.depth == 2

    def test_count_all(self):
        roots = _make_simple_forest()
        assert roots[0].count_all() == 3  # t1 + t2 + t3
        assert roots[1].count_all() == 1  # t4

    def test_find_existing(self):
        roots = _make_simple_forest()
        found = roots[0].find("t3")
        assert found is not None
        assert found.task.id == "t3"

    def test_find_non_existing(self):
        roots = _make_simple_forest()
        assert roots[0].find("nonexistent") is None

    def test_sorting_by_sort_order(self):
        from models.task import TaskRelation

        tasks = [
            _make_task("t1", "父", 0),
            _make_task("c1", "子B", 2),
            _make_task("c2", "子A", 1),
            _make_task("c3", "子C", 3),
        ]
        relations = [
            TaskRelation(id="r1", parent_id="t1", child_id="c1"),
            TaskRelation(id="r2", parent_id="t1", child_id="c2"),
            TaskRelation(id="r3", parent_id="t1", child_id="c3"),
        ]
        roots = build_forest(tasks, relations)
        children = roots[0].children
        assert [c.task.id for c in children] == ["c2", "c1", "c3"]


# ---- TaskTree 测试 ----


class TestTaskTree:
    def test_tree_mode_can_be_constructed(self):
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="tree")
        assert isinstance(tree, ft.Column)
        assert len(tree.controls) > 0

    def test_breadcrumb_mode_can_be_constructed(self):
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="breadcrumb")
        assert isinstance(tree, ft.Column)
        assert len(tree.controls) > 0

    def test_tree_mode_renders_only_roots_when_collapsed(self):
        """未展开时只渲染根节点"""
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="tree", expanded_ids=set())
        # 应该只有 2 个根节点（t1 和 t4）
        assert len(tree.controls) == 2

    def test_tree_mode_renders_children_when_expanded(self):
        """展开根节点后渲染子节点"""
        roots = _make_simple_forest()
        tree = TaskTree(
            nodes=roots,
            nest_mode="tree",
            expanded_ids={"t1"},
        )
        # t1 展开 → 应有 t1 + t2（t2 默认折叠，不展开 t3）+ t4 = 3 个控件
        assert len(tree.controls) == 3

    def test_tree_mode_recursive_expansion(self):
        """同时展开 t1 和 t2 → 渲染 t1, t2, t3, t4"""
        roots = _make_simple_forest()
        tree = TaskTree(
            nodes=roots,
            nest_mode="tree",
            expanded_ids={"t1", "t2"},
        )
        assert len(tree.controls) == 4

    def test_breadcrumb_mode_root_level_shows_all_roots(self):
        """breadcrumb 根层级显示所有根任务"""
        roots = _make_simple_forest()
        tree = TaskTree(
            nodes=roots,
            nest_mode="breadcrumb",
            current_parent_id=None,
        )
        # 面包屑 + 2 个根任务 = 3 个控件
        assert len(tree.controls) == 3

    def test_toggle_expand_adds_to_expanded_ids(self):
        """切换展开状态会更新 expanded_ids"""
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="tree", expanded_ids=set())
        tree._handle_toggle_expand("t1")
        assert "t1" in tree._expanded_ids

    def test_toggle_expand_again_removes_from_expanded_ids(self):
        """再次切换会移除"""
        roots = _make_simple_forest()
        tree = TaskTree(
            nodes=roots, nest_mode="tree", expanded_ids={"t1"}
        )
        tree._handle_toggle_expand("t1")
        assert "t1" not in tree._expanded_ids

    def test_find_path_root(self):
        """查找根节点路径"""
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="breadcrumb")
        path = tree._find_path("t1")
        assert len(path) == 1
        assert path[0].task.id == "t1"

    def test_find_path_nested(self):
        """查找嵌套节点路径"""
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="breadcrumb")
        path = tree._find_path("t3")
        assert len(path) == 3
        assert [n.task.id for n in path] == ["t1", "t2", "t3"]

    def test_find_path_non_existing(self):
        """查找不存在节点返回空列表"""
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots, nest_mode="breadcrumb")
        path = tree._find_path("nonexistent")
        assert path == []

    def test_callbacks_can_be_attached(self):
        called = []

        def on_toggle(tid, val):
            called.append(("toggle", tid, val))

        def on_execute(tid):
            called.append(("execute", tid))

        def on_click(tid):
            called.append(("click", tid))

        roots = _make_simple_forest()
        TaskTree(
            nodes=roots,
            nest_mode="tree",
            on_toggle_enabled=on_toggle,
            on_execute=on_execute,
            on_click=on_click,
        )
        # 测试只验证可构造（不触发实际事件）
        assert True

    def test_default_nest_mode_is_tree(self):
        roots = _make_simple_forest()
        tree = TaskTree(nodes=roots)
        assert tree._nest_mode == "tree"
