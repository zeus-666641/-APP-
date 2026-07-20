"""首页视图"""
import flet as ft


class HomeView(ft.View):
    """首页

    显示欢迎信息和主要入口
    """

    def __init__(self, page: ft.Page) -> None:
        super().__init__(
            route="/home",
            controls=[
                ft.AppBar(
                    title=ft.Text("首页"),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                ),
                ft.SafeArea(
                    ft.Column(
                        controls=[
                            ft.Text(
                                "欢迎使用 步骤记录器",
                                size=28,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text("v0.1.0", size=12, color=ft.colors.ON_SURFACE_VARIANT),
                            ft.Button(
                                "步骤编辑器",
                                icon=ft.icons.LIST_ALT,
                                on_click=lambda _: page.go("/step_editor"),
                            ),
                            ft.Button(
                                "设置",
                                icon=ft.icons.SETTINGS,
                                on_click=lambda _: page.go("/settings"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                ),
            ],
        )
