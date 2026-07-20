"""任务模型定义

M1 任务管理模块的数据模型：
- Task：任务（含图标、分类、启用状态、屏幕常亮）
- TaskRelation：父子关系（独立关系表，Q9 决策）

按 PRD 13.2 ER 图 + 父子任务扩展设计。

变更记录:
- Q9 决策：独立关系表（不单表 parent_id 自关联）
- Q37 决策：默认路由改为 /tasks，task 是首屏入口
- Q38 决策：TaskCard 用 PRD 原样样式
- Q39 决策：task_tree 支持树形展开 + 面包屑双模式
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskCategory(str, Enum):
    """任务分类（PRD category 字段）"""

    DEFAULT = "default"          # 默认/未分类
    WORK = "work"                # 工作
    LIFE = "life"                # 生活
    STUDY = "study"              # 学习
    ENTERTAINMENT = "entertainment"  # 娱乐
    SYSTEM = "system"           # 系统


class TaskStatus(str, Enum):
    """任务状态（用于 TaskCard 状态点显示，PRD 原样样式）"""

    IDLE = "idle"                # 空闲（未执行）
    RUNNING = "running"          # 执行中
    PAUSED = "paused"            # 已暂停
    ERROR = "error"              # 出错
    DISABLED = "disabled"        # 已禁用


@dataclass
class Task:
    """任务实体（PRD 13.2 ER 图 + 扩展字段）

    Attributes:
        id: 任务唯一标识（uuid）
        name: 任务名
        description: 任务描述
        icon: Material icon 名称（默认 play_arrow）
        category: 任务分类
        enabled: 是否启用
        keep_screen_on: 执行时是否保持屏幕常亮
        sort_order: 同级排序
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: str
    name: str
    description: str = ""
    icon: str = "play_arrow"
    category: TaskCategory = TaskCategory.DEFAULT
    enabled: bool = True
    keep_screen_on: bool = False
    sort_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskRelation:
    """父子任务关系（Q9 独立关系表）

    Attributes:
        id: 关系唯一标识
        parent_id: 父任务 ID
        child_id: 子任务 ID
        sort_order: 子任务在父任务下的排序
    """

    id: str
    parent_id: str
    child_id: str
    sort_order: int = 0


@dataclass
class TaskNode:
    """任务树节点（用于 task_tree 渲染）

    将 Task + 子任务列表组合成树形结构。

    Attributes:
        task: 当前任务
        children: 子任务节点列表（空列表表示叶子节点）
        depth: 在树中的深度（根节点为 0）
    """

    task: Task
    children: list["TaskNode"] = field(default_factory=list)
    depth: int = 0

    def add_child(self, child: "TaskNode") -> None:
        """添加子节点"""
        child.depth = self.depth + 1
        self.children.append(child)

    def find(self, task_id: str) -> "TaskNode | None":
        """在树中查找指定 ID 的节点（深度优先）"""
        if self.task.id == task_id:
            return self
        for child in self.children:
            found = child.find(task_id)
            if found is not None:
                return found
        return None

    def count_all(self) -> int:
        """统计树中所有节点数（含自身）"""
        return 1 + sum(c.count_all() for c in self.children)


def build_forest(
    tasks: list[Task],
    relations: list[TaskRelation],
) -> list[TaskNode]:
    """根据扁平任务列表和关系列表构建任务森林

    Args:
        tasks: 所有任务列表
        relations: 所有父子关系列表

    Returns:
        根节点列表（每个根节点带完整的子树）
    """
    task_map: dict[str, TaskNode] = {t.id: TaskNode(task=t) for t in tasks}
    child_ids: set[str] = set()

    for rel in relations:
        parent_node = task_map.get(rel.parent_id)
        child_node = task_map.get(rel.child_id)
        if parent_node is None or child_node is None:
            continue
        parent_node.add_child(child_node)
        child_ids.add(rel.child_id)

    # 根节点 = 不在任何关系中的 child 位的任务
    roots = [task_map[t.id] for t in tasks if t.id not in child_ids]
    # 按 sort_order 排序
    roots.sort(key=lambda n: n.task.sort_order)
    # 递归排序子节点
    for root in roots:
        _sort_children_recursive(root)
    return roots


def _sort_children_recursive(node: TaskNode) -> None:
    """递归按 sort_order 排序子节点"""
    node.children.sort(key=lambda n: n.task.sort_order)
    for child in node.children:
        _sort_children_recursive(child)
