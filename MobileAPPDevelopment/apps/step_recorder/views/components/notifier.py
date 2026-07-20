"""轻量通知组件（基于 Flet SnackBar）

按 Q14 决策"自动保存占位"配套：占位保存、步骤删除、复制等场景
统一走 SnackBar 而非 dialog，避免打断用户操作。

设计要点：
- build_snackbar(message, level) 是纯函数，返回 ft.SnackBar 实例（便于单测）
- Notifier 类封装 page 引用，调用时附加到 page.overlay 并触发显示
- 视觉与 step_card 色板一致：成功/警告/占位/信息
"""
from __future__ import annotations

from enum import Enum
from typing import Any

import flet as ft


class NotificationLevel(str, Enum):
    """通知级别（与状态色板一致）"""

    SUCCESS = "success"        # 绿色：操作成功
    INFO = "info"              # 蓝色：中性提示
    WARNING = "warning"        # 黄色：受限或需要用户注意
    PLACEHOLDER = "placeholder"  # 灰色：占位保存（区别于普通成功）
    ERROR = "error"            # 红色：操作失败


# 级别 → 背景色（与 step_card.py STATUS_COLORS 对齐）
LEVEL_COLORS: dict[NotificationLevel, str] = {
    NotificationLevel.SUCCESS: "#10b981",
    NotificationLevel.INFO: "#2563eb",
    NotificationLevel.WARNING: "#f59e0b",
    NotificationLevel.PLACEHOLDER: "#6b7280",  # 区别于绿色成功
    NotificationLevel.ERROR: "#ef4444",
}

# 默认显示时长（毫秒）
DEFAULT_DURATION_MS = 2500


def build_snackbar(
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
    duration_ms: int = DEFAULT_DURATION_MS,
    action_text: str | None = None,
    on_action: Any = None,
) -> ft.SnackBar:
    """构造 SnackBar 控件（纯函数，便于单测）

    Args:
        message: 提示文案
        level: 通知级别（决定背景色）
        duration_ms: 显示时长（毫秒）
        action_text: 可选操作按钮文本（如"撤销"）
        on_action: 操作按钮回调

    Returns:
        ft.SnackBar 实例（未附加到页面）
    """
    return ft.SnackBar(
        content=ft.Text(
            message,
            color="white",
            size=13,
        ),
        bgcolor=LEVEL_COLORS[level],
        duration=duration_ms,
        action=action_text,  # str 或 None
        on_action=on_action,
        show_close_icon=False,
    )


# ---- 预设文案工厂（按业务场景）----


def placeholder_saved_snackbar(step_name: str) -> ft.SnackBar:
    """占位步骤已保存提示（Q14 核心场景）"""
    return build_snackbar(
        message=f"已保存占位步骤「{step_name}」（尚未实现）",
        level=NotificationLevel.PLACEHOLDER,
    )


def step_saved_snackbar(step_name: str) -> ft.SnackBar:
    """步骤已保存提示"""
    return build_snackbar(
        message=f"步骤「{step_name}」已保存",
        level=NotificationLevel.SUCCESS,
    )


def step_deleted_snackbar(step_name: str) -> ft.SnackBar:
    """步骤已删除提示"""
    return build_snackbar(
        message=f"步骤「{step_name}」已删除",
        level=NotificationLevel.INFO,
    )


def step_moved_snackbar(step_name: str, new_position: int) -> ft.SnackBar:
    """步骤已移动提示"""
    return build_snackbar(
        message=f"步骤「{step_name}」已移动到第 {new_position} 位",
        level=NotificationLevel.INFO,
    )


def step_copied_snackbar(step_name: str) -> ft.SnackBar:
    """步骤已复制提示"""
    return build_snackbar(
        message=f"步骤「{step_name}」已复制",
        level=NotificationLevel.SUCCESS,
    )


def error_snackbar(message: str) -> ft.SnackBar:
    """错误提示"""
    return build_snackbar(
        message=message,
        level=NotificationLevel.ERROR,
        duration_ms=4000,  # 错误提示更久
    )


class Notifier:
    """通知器：把 SnackBar 附加到 page 并触发显示

    用法:
        notifier = Notifier(page)
        notifier.placeholder_saved("蓝牙开关")
        notifier.error("保存失败：网络错误")

    设计：
    - 持有 page 引用（弱依赖，不负责 page 生命周期）
    - 暴露高层语义方法（按业务场景命名）
    - 内部调用 build_*_snackbar + show
    """

    def __init__(self, page: ft.Page | None = None) -> None:
        self._page = page

    @property
    def page(self) -> ft.Page | None:
        return self._page

    @page.setter
    def page(self, value: ft.Page | None) -> None:
        self._page = value

    def attach(self, page: ft.Page) -> "Notifier":
        """链式设置 page"""
        self._page = page
        return self

    # ---- 底层显示方法 ----

    def show(self, snackbar: ft.SnackBar) -> None:
        """显示一个 SnackBar

        Args:
            snackbar: 已构造的 SnackBar 实例
        """
        if self._page is None:
            return  # 无 page 静默失败（便于单测）
        # Flet 0.86: page.overlay.append + snackbar.open=True
        # 兼容 page.open(snackbar) 新 API（如果存在）
        self._page.overlay.append(snackbar)
        snackbar.open = True
        try:
            self._page.update()
        except Exception:
            pass  # update 在测试环境可能失败

    # ---- 高层语义方法 ----

    def placeholder_saved(self, step_name: str) -> None:
        self.show(placeholder_saved_snackbar(step_name))

    def step_saved(self, step_name: str) -> None:
        self.show(step_saved_snackbar(step_name))

    def step_deleted(self, step_name: str) -> None:
        self.show(step_deleted_snackbar(step_name))

    def step_moved(self, step_name: str, new_position: int) -> None:
        self.show(step_moved_snackbar(step_name, new_position))

    def step_copied(self, step_name: str) -> None:
        self.show(step_copied_snackbar(step_name))

    def info(self, message: str) -> None:
        self.show(build_snackbar(message, NotificationLevel.INFO))

    def warning(self, message: str) -> None:
        self.show(build_snackbar(message, NotificationLevel.WARNING))

    def error(self, message: str) -> None:
        self.show(error_snackbar(message))
