"""
Flet App 入口

Bug 3 修复（COEP/CORS）：
TRAE 预览器会在外层注入 previewer-tools.umd.js（来自 bytednsdoc.com），
而 Flet 默认在 FastAPI 中间件里设置了
`Cross-Origin-Embedder-Policy: require-corp`，
该外部脚本未带 CORP 头，被浏览器以
`ERR_BLOCKED_BY_RESPONSE.NotSameOriginAfterDefaultedToSameOriginByCoep` 拦截。

解决方案：用 `ft.run(export_asgi_app=True)` 取回 FastAPI app 实例，
再加一层外层中间件把 COEP 降级为 `credentialless`（允许加载无 CORP 的跨域资源，
仍保留基本的跨源隔离）。
"""
import logging
import os

import flet as ft
import uvicorn

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

    # setup_routes 内部会挂载初始 HomeView（绕过 Flet 0.86 push_route 吞事件 bug）
    setup_routes(page)


def _build_app():
    """构造 FastAPI app 并覆盖 COEP 头

    Returns:
        配置好的 FastAPI app 实例（含外层 COEP 放宽中间件）
    """
    app = ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        web_renderer=ft.WebRenderer.AUTO,
        export_asgi_app=True,  # 返回 app 而非运行事件循环
    )

    @app.middleware("http")
    async def relax_coep(request, call_next):
        """外层中间件：覆盖 Flet 默认 COEP: require-corp

        - require-corp: 要求所有跨源资源显式带 CORP 头（TRAE 预览器脚本不满足）
        - credentialless: 允许加载无 CORP 头的跨源资源（剥离 credentials），
          仍保留 cross-origin 隔离能力，平衡兼容性与安全性
        """
        response = await call_next(request)
        response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
        return response

    return app


if __name__ == "__main__":
    app = _build_app()
    port = int(os.getenv("FLET_SERVER_PORT", "8000"))
    log_level = logging.getLogger("flet").getEffectiveLevel()
    if log_level in (logging.CRITICAL, logging.NOTSET):
        log_level = logging.FATAL
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=log_level)
