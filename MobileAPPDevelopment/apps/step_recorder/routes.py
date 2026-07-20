"""路由配置

集中管理所有路由，避免散落在各 View 中
"""
import flet as ft

from views.home_view import HomeView
from views.settings_view import SettingsView


def setup_routes(page: ft.Page) -> None:
    """注册路由

    Args:
        page: Flet 页面对象
    """

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        if e.route == "/home":
            page.views.append(HomeView(page))
        elif e.route == "/settings":
            page.views.append(HomeView(page))
            page.views.append(SettingsView(page))
        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
