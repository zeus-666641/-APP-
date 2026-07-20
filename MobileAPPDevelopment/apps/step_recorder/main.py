"""
Flet App 入口
注意：此文件为模板，step_recorder 等占位符由 scripts/scaffold.py 替换
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

    # setup_routes 内部会挂载初始 StepEditorView（绕过 Flet 0.86 push_route 吞事件 bug）
    # 需求6/F3：一进入 App 就是步骤界面，不再有 HomeView
    setup_routes(page)


if __name__ == "__main__":
    # Flet 0.86 推荐 ft.run()（ft.app() 已废弃）
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        web_renderer=ft.WebRenderer.AUTO,
    )
