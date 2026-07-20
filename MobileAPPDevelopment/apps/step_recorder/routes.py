"""路由配置

集中管理所有路由，避免散落在各 View 中

变更记录:
- 2026-07: 修复 Flet 0.86 push_route 同路由不触发 route_change 的问题
  （Page.before_event 中 if __last_route == e.route: return False 吞事件）
- 2026-07-20 需求6/F3: 删除 HomeView 入口，默认路由 / -> /step_editor
- 2026-07-20 Q37: 默认路由从 /step_editor 改为 /tasks（M1 引入底部导航后任务列表是更高层级入口）
  覆盖需求6 原"一进入就是步骤界面"的决策
- 2026-07-20 Q40: 加入 /stats 和 /logs 路由占位（M4/M5 后续实现）
- 2026-07-20 Q42: M5 接入 /logs 与 /logs/{id} 独立路由
"""
import re

import flet as ft

from views.home_view import HomeView
from views.log_detail_view import LogDetailView
from views.logs_view import LogsView
from views.settings_view import SettingsView
from views.stats_view import StatsView
from views.step_editor_view import StepEditorView


# 默认路由（Q37：M1 后改为 /tasks 任务列表）
_initial_route = "/tasks"

# /logs/{id} 路由匹配
_LOG_DETAIL_PATTERN = re.compile(r"^/logs/([^/]+)$")


def setup_routes(page: ft.Page) -> None:
    """注册路由

    Args:
        page: Flet 页面对象
    """

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        route = e.route
        # 根路径或未知路径都 fallback 到 /tasks（Q37）
        if route in ("/", ""):
            route = _initial_route

        if route == "/tasks":
            page.views.append(HomeView(page))
        elif route == "/step_editor":
            # 从任务卡片进入步骤编辑器时保留任务列表在栈底
            page.views.append(HomeView(page))
            page.views.append(StepEditorView(page))
        elif route == "/settings":
            # Q50：设置从 AppBar 进入，保留任务列表在栈底（点返回回任务列表）
            page.views.append(HomeView(page))
            page.views.append(SettingsView(page))
        elif route == "/stats":
            # Q50：统计 tab 直接跳路由，保留任务列表在栈底
            page.views.append(HomeView(page))
            page.views.append(StatsView(page))
        elif route == "/logs":
            # Q50：日志 tab 直接跳路由，保留任务列表在栈底
            page.views.append(HomeView(page))
            page.views.append(LogsView(page))
        else:
            # 检查 /logs/{id} 路由
            match = _LOG_DETAIL_PATTERN.match(route)
            if match:
                log_id = match.group(1)
                page.views.append(HomeView(page))
                page.views.append(LogsView(page))
                page.views.append(LogDetailView(page, log_id))
            else:
                # 未知路由也回退到任务列表（避免黑屏）
                page.views.append(HomeView(page))
        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        if not page.views:
            return
        page.views.pop()
        if not page.views:
            page.go(_initial_route)
            return
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Flet 0.86 bug 绕过：客户端连接时 __last_route 已被设为初始 URL，
    # 后续 push_route(同路由) 会被 before_event 吞掉，导致 on_route_change
    # 不触发、views 为空、页面黑屏。这里手动触发一次确保初始视图挂载。
    page.views.append(HomeView(page))
    page.update()
