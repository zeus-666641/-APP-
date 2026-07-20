"""路由配置

集中管理所有路由，避免散落在各 View 中

变更记录:
- 2026-07: 修复 Flet 0.86 push_route 同路由不触发 route_change 的问题
  （Page.before_event 中 if __last_route == e.route: return False 吞事件）
- 2026-07-20 需求6/F3: 删除 HomeView 入口，默认路由 / -> /step_editor
  一进入 App 就是步骤界面，AppBar 加设置按钮
"""
import flet as ft

from views.settings_view import SettingsView
from views.step_editor_view import StepEditorView


# 默认路由（需求6/F3：一进入就是步骤界面）
_initial_route = "/step_editor"


def setup_routes(page: ft.Page) -> None:
    """注册路由

    Args:
        page: Flet 页面对象
    """

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        route = e.route
        # 根路径或未知路径都 fallback 到 /step_editor（需求6/F3）
        if route in ("/", ""):
            route = _initial_route

        if route == "/step_editor":
            page.views.append(StepEditorView(page))
        elif route == "/settings":
            page.views.append(StepEditorView(page))
            page.views.append(SettingsView(page))
        else:
            # 未知路由也回退到步骤编辑器（避免黑屏）
            page.views.append(StepEditorView(page))
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
    page.views.append(StepEditorView(page))
    page.update()
