"""设置页视图"""
import flet as ft


class SettingsView(ft.View):
    """设置页

    显示应用设置项
    """

    def __init__(self, page: ft.Page) -> None:
        super().__init__(
            route="/settings",
            controls=[
                ft.AppBar(
                    title=ft.Text("设置"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                ft.SafeArea(
                    ft.Column(
                        controls=[
                            ft.Text("应用设置", size=20, weight=ft.FontWeight.BOLD),
                            ft.Switch(label="深色模式", value=False),
                            ft.Switch(label="通知", value=True),
                        ],
                        spacing=10,
                    ),
                    expand=True,
                ),
            ],
        )
