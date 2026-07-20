"""设置页视图（M2 后续）

支持：
- 主题模式（深色/浅色/跟随系统）→ 实时切换 page.theme_mode
- 通知开关（占位，M6 接入通知服务时启用）
- 添加步骤入口（FAB/AppBar/双入口）→ 需求3
- 拖拽手柄显隐 + 位置（左/右）→ Q26/Q28
- 换位按钮显隐 → Q28
- 执行设置（默认屏幕常亮/失败处理/重试次数/通知）→ PRD 11.2
- 步骤间停顿（可随机+可设置随机范围）→ 需求16/F7
- 日志管理（自动清理开关 + 保留条数 1-9999，Q48）
- 关于（版本/作者）→ PRD 11.3
"""
import flet as ft

from config.settings import Settings


# ---- 设置项持久化（轻量 KV，M6 接入 storage 时替换）----
# 暂用内存态，应用重启后回到默认。M0 数据层完成后切换到 storage.py。
_APP_SETTINGS: dict[str, object] = {}


def get_app_setting(key: str, default: object = None) -> object:
    """读取应用设置项"""
    return _APP_SETTINGS.get(key, default)


def set_app_setting(key: str, value: object) -> None:
    """写入应用设置项"""
    _APP_SETTINGS[key] = value


class SettingsView(ft.View):
    """设置页

    显示应用设置项，所有开关均实时生效。
    """

    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._settings = Settings()

        # 主题模式：跟随系统/浅色/深色
        theme_mode_value = get_app_setting("theme_mode", "system")
        theme_options = [
            ft.dropdown.Option(key="system", text="跟随系统"),
            ft.dropdown.Option(key="light", text="浅色"),
            ft.dropdown.Option(key="dark", text="深色"),
        ]

        # 添加步骤入口（需求3）
        add_entry_value = get_app_setting("add_step_entry", "appbar")
        add_entry_options = [
            ft.dropdown.Option(key="appbar", text="仅右上角"),
            ft.dropdown.Option(key="fab", text="仅右下角 FAB"),
            ft.dropdown.Option(key="both", text="双入口"),
        ]

        # 拖拽手柄位置（Q26）
        handle_side_value = get_app_setting("drag_handle_side", "right")
        handle_side_options = [
            ft.dropdown.Option(key="left", text="左侧"),
            ft.dropdown.Option(key="right", text="右侧"),
        ]

        # 执行失败处理（PRD 11.2）
        on_failure_value = get_app_setting("on_failure", "abort")
        on_failure_options = [
            ft.dropdown.Option(key="abort", text="中止任务"),
            ft.dropdown.Option(key="skip", text="跳过继续"),
        ]

        super().__init__(
            route="/settings",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self._handle_back,
                    ),
                    title=ft.Text("设置"),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                ),
                ft.SafeArea(
                    ft.Column(
                        controls=[
                            # === 显示设置 ===
                            self._section_title("显示设置"),
                            ft.Dropdown(
                                label="主题模式",
                                value=str(theme_mode_value),
                                options=theme_options,
                                on_select=self._handle_theme_change,
                            ),
                            ft.Dropdown(
                                label="添加步骤入口",
                                value=str(add_entry_value),
                                options=add_entry_options,
                                on_select=self._handle_add_entry_change,
                                helper_text="默认右上角 AppBar 按钮",
                            ),

                            # === 交互设置（拖拽/换位）===
                            self._section_title("列表交互"),
                            ft.Switch(
                                label="显示拖拽手柄",
                                value=bool(get_app_setting("show_drag_handle", True)),
                                on_change=self._handle_show_drag_handle_change,
                            ),
                            ft.Dropdown(
                                label="拖拽手柄位置",
                                value=str(handle_side_value),
                                options=handle_side_options,
                                on_select=self._handle_handle_side_change,
                            ),
                            ft.Switch(
                                label="显示换位按钮",
                                value=bool(get_app_setting("show_swap_button", True)),
                                on_change=self._handle_show_swap_change,
                            ),

                            # === 执行设置（PRD 11.2）===
                            self._section_title("执行设置"),
                            ft.Switch(
                                label="默认屏幕常亮",
                                value=bool(get_app_setting("default_keep_awake", False)),
                                on_change=self._handle_keep_awake_change,
                            ),
                            ft.Dropdown(
                                label="执行失败处理",
                                value=str(on_failure_value),
                                options=on_failure_options,
                                on_select=self._handle_on_failure_change,
                            ),
                            ft.TextField(
                                label="失败重试次数",
                                value=str(get_app_setting("retry_count", 0)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=self._handle_retry_count_change,
                            ),
                            ft.Switch(
                                label="通知提醒",
                                value=bool(get_app_setting("notify_enabled", True)),
                                on_change=self._handle_notify_change,
                            ),

                            # === 步骤间停顿（需求16/F7）===
                            self._section_title("步骤间停顿"),
                            ft.Switch(
                                label="启用步骤间停顿",
                                value=bool(get_app_setting("inter_step_pause_enabled", False)),
                                on_change=self._handle_pause_enabled_change,
                                helper_text="开启后，每个步骤执行完后会停顿一段时间",
                            ),
                            ft.TextField(
                                label="最小停顿时间（秒）",
                                value=str(get_app_setting("inter_step_pause_min", 0.5)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=self._handle_pause_min_change,
                                helper_text="停顿时间在此范围内随机",
                            ),
                            ft.TextField(
                                label="最大停顿时间（秒）",
                                value=str(get_app_setting("inter_step_pause_max", 2.0)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=self._handle_pause_max_change,
                                helper_text="最小=最大时为固定停顿",
                            ),

                            # === 日志管理（Q48 决策）===
                            self._section_title("日志管理"),
                            ft.Switch(
                                label="启用自动清理",
                                value=bool(get_app_setting("log_auto_cleanup_enabled", False)),
                                on_change=self._handle_log_cleanup_enabled_change,
                                helper_text="开启后自动保留最近的 N 条日志，其余删除",
                            ),
                            ft.TextField(
                                label="保留日志条数（1-9999）",
                                value=str(get_app_setting("log_keep_count", 500)),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                on_change=self._handle_log_keep_count_change,
                                helper_text="范围 1-9999，默认 500",
                            ),

                            # === 关于（PRD 11.3）===
                            self._section_title("关于"),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            self._settings.app_name,
                                            size=16,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text("版本：0.1.0 (MVP)", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                        ft.Text("技术栈：Python + Flet 0.86", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                        ft.Text("目标平台：Android only", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                    ],
                                    spacing=2,
                                ),
                                padding=ft.Padding(left=12, right=12, top=8, bottom=8),
                                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                                border_radius=8,
                            ),
                        ],
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                ),
            ],
        )

    @staticmethod
    def _section_title(text: str) -> ft.Text:
        return ft.Text(
            text,
            size=14,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.PRIMARY,
        )

    # ---- 事件处理 ----

    def _handle_theme_change(self, e: ft.ControlEvent) -> None:
        """主题模式切换"""
        mode = str(e.control.value)
        set_app_setting("theme_mode", mode)
        if mode == "dark":
            self._page.theme_mode = ft.ThemeMode.DARK
        elif mode == "light":
            self._page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self._page.theme_mode = ft.ThemeMode.SYSTEM
        try:
            self._page.update()
        except Exception:
            pass

    def _handle_add_entry_change(self, e: ft.ControlEvent) -> None:
        """添加步骤入口切换（需求3）"""
        set_app_setting("add_step_entry", str(e.control.value))

    def _handle_show_drag_handle_change(self, e: ft.ControlEvent) -> None:
        """显示拖拽手柄开关"""
        set_app_setting("show_drag_handle", bool(e.control.value))

    def _handle_handle_side_change(self, e: ft.ControlEvent) -> None:
        """手柄位置切换"""
        set_app_setting("drag_handle_side", str(e.control.value))

    def _handle_show_swap_change(self, e: ft.ControlEvent) -> None:
        """换位按钮开关"""
        set_app_setting("show_swap_button", bool(e.control.value))

    def _handle_keep_awake_change(self, e: ft.ControlEvent) -> None:
        set_app_setting("default_keep_awake", bool(e.control.value))

    def _handle_on_failure_change(self, e: ft.ControlEvent) -> None:
        set_app_setting("on_failure", str(e.control.value))

    def _handle_retry_count_change(self, e: ft.ControlEvent) -> None:
        raw = str(e.control.value or "").strip()
        try:
            n = max(0, int(raw))
        except ValueError:
            n = 0
        set_app_setting("retry_count", n)

    def _handle_notify_change(self, e: ft.ControlEvent) -> None:
        set_app_setting("notify_enabled", bool(e.control.value))

    # ---- 步骤间停顿（需求16/F7）----

    def _handle_pause_enabled_change(self, e: ft.ControlEvent) -> None:
        """启用/禁用步骤间停顿"""
        set_app_setting("inter_step_pause_enabled", bool(e.control.value))

    def _handle_pause_min_change(self, e: ft.ControlEvent) -> None:
        """最小停顿时间变更（秒）"""
        raw = str(e.control.value or "").strip()
        try:
            value = float(raw)
            if value < 0:
                value = 0.0
        except ValueError:
            value = 0.5
        set_app_setting("inter_step_pause_min", value)
        # 同步约束：min 不能大于 max
        max_v = float(get_app_setting("inter_step_pause_max", 2.0))
        if value > max_v:
            set_app_setting("inter_step_pause_max", value)

    def _handle_pause_max_change(self, e: ft.ControlEvent) -> None:
        """最大停顿时间变更（秒）"""
        raw = str(e.control.value or "").strip()
        try:
            value = float(raw)
            if value < 0:
                value = 0.0
        except ValueError:
            value = 2.0
        set_app_setting("inter_step_pause_max", value)
        # 同步约束：max 不能小于 min
        min_v = float(get_app_setting("inter_step_pause_min", 0.5))
        if value < min_v:
            set_app_setting("inter_step_pause_min", value)

    # ---- 日志管理（Q48）----

    def _handle_log_cleanup_enabled_change(self, e: ft.ControlEvent) -> None:
        """启用自动清理开关"""
        set_app_setting("log_auto_cleanup_enabled", bool(e.control.value))

    def _handle_log_keep_count_change(self, e: ft.ControlEvent) -> None:
        """保留日志条数变更（1-9999）"""
        raw = str(e.control.value or "").strip()
        try:
            n = int(raw)
        except ValueError:
            n = 500
        # 范围约束：1-9999
        if n < 1:
            n = 1
        elif n > 9999:
            n = 9999
        set_app_setting("log_keep_count", n)

    def _handle_back(self, e: ft.ControlEvent | None = None) -> None:
        """返回任务列表（Q50：设置从 AppBar 进入）"""
        self._page.go("/tasks")
