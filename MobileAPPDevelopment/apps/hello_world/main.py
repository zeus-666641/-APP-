"""
Flet App 入口
注意：此文件为模板，hello_world 等占位符由 scripts/scaffold.py 替换
"""
import flet as ft

from config.settings import Settings
from routes import setup_routes


def main(page: ft.Page) -> None:
    """Flet 应用入口

    Args:
        page: Flet 页面对象
    """
    settings = Settings()
    page.title = settings.app_name
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.window.width = 400
    page.window.height = 800

    setup_routes(page)
    page.go("/home")


if __name__ == "__main__":
    # 开发期用浏览器预览；发布时改为 ft.AppView.NATIVE
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
