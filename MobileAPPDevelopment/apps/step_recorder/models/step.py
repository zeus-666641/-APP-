"""步骤类型定义

覆盖 PRD 第 5 章全部 30+ 步骤类型，含状态标记：
- AVAILABLE: 完全可用
- LIMITED: 受限可用（部分功能可用）
- NOT_IMPLEMENTED: 未实现（置灰显示，点击弹"尚未完成"提示）

按 PRD 5.1-5.5 分类组织。

变更记录:
- Q17 决策：StepTypeMeta 新增 `fields: tuple[ParamField, ...]` 字段（向后兼容，旧 params_schema 保留）
- Q18 决策：NOT_IMPLEMENTED 类型也填充 fields（允许填参数+保存为占位）
- Q19 决策：FieldType 枚举驱动控件渲染（BOOL→Switch、ENUM→Dropdown、INT_RANGE→Slider、其他→TextField）
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    """步骤类型的实现状态"""

    AVAILABLE = "available"          # 完全可用
    LIMITED = "limited"             # 受限可用
    NOT_IMPLEMENTED = "not_implemented"  # 未实现


class StepCategory(str, Enum):
    """步骤分类（对应 PRD 5.1-5.5）"""

    SIMULATION = "simulation"        # 5.1 模拟操作类
    SYSTEM_CONTROL = "system_control"  # 5.2 系统控制类
    DISPLAY = "display"              # 5.3 显示设置类
    AUDIO_HAPTIC = "audio_haptic"    # 5.4 音频与触感类
    AUXILIARY = "auxiliary"          # 5.5 辅助与通知类


class FieldType(str, Enum):
    """参数字段控件类型（驱动 ParamEditor 渲染，Q19 决策）

    - BOOL → Switch
    - INT → TextField（数字键盘）
    - INT_RANGE → Slider（含 min/max/step）
    - STRING → 单行 TextField
    - TEXTAREA → 多行 TextField
    - ENUM → Dropdown（含 options）
    - COORDINATE → 坐标输入组（X/Y 两字段，UI 视为单控件组）
    """

    BOOL = "bool"
    INT = "int"
    INT_RANGE = "int_range"
    STRING = "string"
    TEXTAREA = "textarea"
    ENUM = "enum"
    COORDINATE = "coordinate"


@dataclass(frozen=True)
class ParamField:
    """参数字段定义（用于动态生成参数表单）

    Attributes:
        key: 参数名（snake_case，存到 params dict 的键）
        label_zh: 中文显示名（表单 label）
        field_type: 控件类型（FieldType 枚举）
        required: 是否必填
        default: 默认值
        options: ENUM 选项列表，每项 (value, label_zh)
        min_value: INT_RANGE 最小值
        max_value: INT_RANGE 最大值
        step: INT_RANGE 步长（int 类型；浮点用 0 表示不限）
        placeholder: STRING/TEXTAREA 输入提示
        help_text: 字段下方帮助文字
    """

    key: str
    label_zh: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    options: tuple[tuple[str, str], ...] = ()
    min_value: int | None = None
    max_value: int | None = None
    step: int = 1
    placeholder: str = ""
    help_text: str = ""


# ENUM 通用选项：开/关（ON_OFF）
_ON_OFF_OPTIONS = (
    ("on", "开"),
    ("off", "关"),
)


@dataclass(frozen=True)
class StepTypeMeta:
    """步骤类型的元数据"""

    type_id: str                            # 枚举值
    name_zh: str                            # 中文名
    icon: str                               # Material icon name
    category: StepCategory                  # 分类
    status: StepStatus                     # 实现状态
    description: str                        # 功能描述
    params_schema: dict                    # 旧字段：参数 schema（字段名: 类型描述，向后兼容）
    fields: tuple[ParamField, ...] = ()     # 新字段：结构化参数定义（Q17 决策）


class StepType(str, Enum):
    """步骤类型枚举（覆盖 PRD 第 5 章全部类型）"""

    # === 5.1 模拟操作类 ===
    CLICK = "click"
    SWIPE = "swipe"
    GO_HOME = "go_home"
    GO_BACK = "go_back"
    OPEN_APP = "open_app"
    SWITCH_APP = "switch_app"
    DIAL = "dial"
    OPEN_URL = "open_url"

    # === 5.2 系统控制类（全部未实现）===
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    AIRPLANE = "airplane"
    LOCATION = "location"
    HOTSPOT = "hotspot"
    NFC = "nfc"
    MOBILE_DATA = "mobile_data"
    DND = "dnd"                        # 勿扰模式
    POWER_SAVE = "power_save"          # 省电模式
    FOCUS = "focus"                    # 专注模式
    DRIVING = "driving"                # 驾车模式
    LOCK_SCREEN = "lock_screen"
    SCREEN_OFF = "screen_off"
    POWER = "power"                    # 开关机

    # === 5.3 显示设置类 ===
    BRIGHTNESS = "brightness"
    AUTO_ROTATE = "auto_rotate"
    DARK_MODE = "dark_mode"
    DISPLAY_SIZE = "display_size"
    FONT_SIZE = "font_size"
    FONT_WEIGHT = "font_weight"
    EYE_CARE = "eye_care"
    KEEP_AWAKE_ON = "keep_awake_on"
    KEEP_AWAKE_OFF = "keep_awake_off"

    # === 5.4 音频与触感类 ===
    VOLUME = "volume"
    MUTE = "mute"
    HAPTIC = "haptic"                   # 改变系统触感
    VIBRATE = "vibrate"                 # 设备振动

    # === 5.5 辅助与通知类 ===
    NOTIFY = "notify"                  # 发送通知
    ALERT = "alert"                    # 弹出提醒
    DELAY = "delay"                    # 延时等待
    SCREEN_RECOGNIZE = "screen_recognize"  # 屏幕内容识别
    RUN_SUBTASK = "run_subtask"        # 执行子任务
    FLASHLIGHT = "flashlight"


# 步骤类型元数据表（PRD 第 5 章逐项实现）
STEP_TYPE_REGISTRY: dict[StepType, StepTypeMeta] = {
    # === 5.1 模拟操作类 ===
    StepType.CLICK: StepTypeMeta(
        type_id="click",
        name_zh="模拟点击",
        icon="ads_click",
        category=StepCategory.SIMULATION,
        status=StepStatus.LIMITED,
        description="App 内控件点击；跨应用点击需 AccessibilityService",
        params_schema={"target": "控件ID或坐标", "coordinate": "坐标(x,y)"},
        fields=(
            ParamField(
                key="target", label_zh="目标控件",
                field_type=FieldType.STRING,
                required=True,
                placeholder="控件 ID",
                help_text="App 内控件的唯一标识",
            ),
            ParamField(
                key="x", label_zh="X 坐标",
                field_type=FieldType.INT,
                default=0, min_value=0,
            ),
            ParamField(
                key="y", label_zh="Y 坐标",
                field_type=FieldType.INT,
                default=0, min_value=0,
            ),
        ),
    ),
    StepType.SWIPE: StepTypeMeta(
        type_id="swipe",
        name_zh="模拟滑动",
        icon="swipe",
        category=StepCategory.SIMULATION,
        status=StepStatus.LIMITED,
        description="App 内控件滑动；跨应用滑动需 AccessibilityService",
        params_schema={"start": "起点", "end": "终点", "duration": "时长(秒)", "repeat": "次数"},
        fields=(
            ParamField(key="start_x", label_zh="起点 X", field_type=FieldType.INT, default=0, min_value=0),
            ParamField(key="start_y", label_zh="起点 Y", field_type=FieldType.INT, default=0, min_value=0),
            ParamField(key="end_x", label_zh="终点 X", field_type=FieldType.INT, default=0, min_value=0),
            ParamField(key="end_y", label_zh="终点 Y", field_type=FieldType.INT, default=0, min_value=0),
            ParamField(
                key="duration", label_zh="时长（秒）",
                field_type=FieldType.INT_RANGE,
                default=1, min_value=1, max_value=10,
            ),
            ParamField(
                key="repeat", label_zh="重复次数",
                field_type=FieldType.INT,
                default=1, min_value=1,
            ),
        ),
    ),
    StepType.GO_HOME: StepTypeMeta(
        type_id="go_home",
        name_zh="返回主界面",
        icon="home",
        category=StepCategory.SIMULATION,
        status=StepStatus.LIMITED,
        description="App 内 NavigationBar 切换；系统 Home 键需 root",
        params_schema={},
        fields=(),
    ),
    StepType.GO_BACK: StepTypeMeta(
        type_id="go_back",
        name_zh="返回上一级",
        icon="arrow_back",
        category=StepCategory.SIMULATION,
        status=StepStatus.LIMITED,
        description="App 内 page.pop()；系统返回键需 AccessibilityService",
        params_schema={},
        fields=(),
    ),
    StepType.OPEN_APP: StepTypeMeta(
        type_id="open_app",
        name_zh="进入应用",
        icon="apps",
        category=StepCategory.SIMULATION,
        status=StepStatus.NOT_IMPLEMENTED,
        description="跨应用启动，需 Android 原生 Intent",
        params_schema={"package": "应用包名", "name": "应用名"},
        fields=(
            ParamField(
                key="package", label_zh="应用包名",
                field_type=FieldType.STRING,
                required=True,
                placeholder="com.example.app",
            ),
            ParamField(
                key="name", label_zh="应用名",
                field_type=FieldType.STRING,
                placeholder="如：微信",
            ),
        ),
    ),
    StepType.SWITCH_APP: StepTypeMeta(
        type_id="switch_app",
        name_zh="切换应用",
        icon="swap_horiz",
        category=StepCategory.SIMULATION,
        status=StepStatus.NOT_IMPLEMENTED,
        description="跨应用切换，需 Android 原生",
        params_schema={"package": "应用包名"},
        fields=(
            ParamField(
                key="package", label_zh="应用包名",
                field_type=FieldType.STRING,
                required=True,
                placeholder="com.example.app",
            ),
        ),
    ),
    StepType.DIAL: StepTypeMeta(
        type_id="dial",
        name_zh="拨号按键",
        icon="dialpad",
        category=StepCategory.SIMULATION,
        status=StepStatus.LIMITED,
        description="Flet 可启动拨号 intent，无法自动拨打",
        params_schema={"phone": "电话号码", "auto_call": "是否自动拨打"},
        fields=(
            ParamField(
                key="phone", label_zh="电话号码",
                field_type=FieldType.STRING,
                required=True,
                placeholder="如：13800138000",
            ),
            ParamField(
                key="auto_call", label_zh="是否自动拨打",
                field_type=FieldType.BOOL,
                default=False,
            ),
        ),
    ),
    StepType.OPEN_URL: StepTypeMeta(
        type_id="open_url",
        name_zh="打开链接",
        icon="link",
        category=StepCategory.SIMULATION,
        status=StepStatus.AVAILABLE,
        description="Flet page.launch_url() 直接支持",
        params_schema={"url": "URL 地址"},
        fields=(
            ParamField(
                key="url", label_zh="URL 地址",
                field_type=FieldType.STRING,
                required=True,
                placeholder="https://example.com",
            ),
        ),
    ),

    # === 5.2 系统控制类（全部未实现）===
    StepType.BLUETOOTH: StepTypeMeta(
        type_id="bluetooth", name_zh="蓝牙开关", icon="bluetooth",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 BLUETOOTH_ADMIN + 系统签名",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.WIFI: StepTypeMeta(
        type_id="wifi", name_zh="WiFi 开关", icon="wifi",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 CHANGE_WIFI_STATE",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.AIRPLANE: StepTypeMeta(
        type_id="airplane", name_zh="飞行模式", icon="flight",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名权限",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.LOCATION: StepTypeMeta(
        type_id="location", name_zh="定位开关", icon="location_on",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 LOCATION 权限 + 系统 API",
        params_schema={"state": "开/关", "mode": "定位模式"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
            ParamField(
                key="mode", label_zh="定位模式",
                field_type=FieldType.ENUM,
                default="high_accuracy",
                options=(
                    ("high_accuracy", "高精度"),
                    ("battery_saving", "省电模式"),
                    ("device_only", "仅设备"),
                ),
            ),
        ),
    ),
    StepType.HOTSPOT: StepTypeMeta(
        type_id="hotspot", name_zh="个人热点", icon="wifi_tethering",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.NFC: StepTypeMeta(
        type_id="nfc", name_zh="NFC 开关", icon="nfc",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="仅系统设置页跳转",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.MOBILE_DATA: StepTypeMeta(
        type_id="mobile_data", name_zh="移动数据", icon="signal_cellular_4_bar",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.DND: StepTypeMeta(
        type_id="dnd", name_zh="勿扰模式", icon="do_not_disturb_on",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 NOTIFICATION_POLICY_ACCESS",
        params_schema={"state": "开/关", "time_range": "时段"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
            ParamField(
                key="time_range_start", label_zh="开始时段",
                field_type=FieldType.STRING,
                placeholder="如：22:00",
            ),
            ParamField(
                key="time_range_end", label_zh="结束时段",
                field_type=FieldType.STRING,
                placeholder="如：07:00",
            ),
        ),
    ),
    StepType.POWER_SAVE: StepTypeMeta(
        type_id="power_save", name_zh="省电模式", icon="battery_saver",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.FOCUS: StepTypeMeta(
        type_id="focus", name_zh="专注模式", icon="center_focus_strong",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统 API",
        params_schema={"mode": "模式类型", "state": "开/关"},
        fields=(
            ParamField(
                key="mode", label_zh="专注模式",
                field_type=FieldType.ENUM,
                default="work",
                options=(
                    ("work", "工作"),
                    ("personal", "个人"),
                    ("sleep", "睡眠"),
                ),
            ),
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="on", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.DRIVING: StepTypeMeta(
        type_id="driving", name_zh="驾车模式", icon="directions_car",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统 API",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.LOCK_SCREEN: StepTypeMeta(
        type_id="lock_screen", name_zh="锁屏", icon="lock",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 Device Admin",
        params_schema={},
        fields=(),
    ),
    StepType.SCREEN_OFF: StepTypeMeta(
        type_id="screen_off", name_zh="控制屏幕息屏", icon="screen_lock_portrait",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名",
        params_schema={"delay": "延迟时间", "immediate": "是否立即"},
        fields=(
            ParamField(
                key="delay", label_zh="延迟（秒）",
                field_type=FieldType.INT_RANGE,
                default=0, min_value=0, max_value=60,
            ),
            ParamField(
                key="immediate", label_zh="立即息屏",
                field_type=FieldType.BOOL,
                default=False,
            ),
        ),
    ),
    StepType.POWER: StepTypeMeta(
        type_id="power", name_zh="开关机", icon="power_settings_new",
        category=StepCategory.SYSTEM_CONTROL, status=StepStatus.NOT_IMPLEMENTED,
        description="需 root",
        params_schema={"action": "关机/重启"},
        fields=(
            ParamField(
                key="action", label_zh="操作",
                field_type=FieldType.ENUM,
                default="shutdown",
                options=(
                    ("shutdown", "关机"),
                    ("restart", "重启"),
                ),
            ),
        ),
    ),

    # === 5.3 显示设置类 ===
    StepType.BRIGHTNESS: StepTypeMeta(
        type_id="brightness", name_zh="调节屏幕亮度", icon="brightness_6",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="需 WRITE_SETTINGS",
        params_schema={"value": "亮度0-100", "auto": "是否自动"},
        fields=(
            ParamField(
                key="value", label_zh="亮度",
                field_type=FieldType.INT_RANGE,
                default=50, min_value=0, max_value=100,
            ),
            ParamField(
                key="auto", label_zh="自动亮度",
                field_type=FieldType.BOOL,
                default=False,
            ),
        ),
    ),
    StepType.AUTO_ROTATE: StepTypeMeta(
        type_id="auto_rotate", name_zh="方向锁定", icon="screen_rotation",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="系统 API",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
        ),
    ),
    StepType.DARK_MODE: StepTypeMeta(
        type_id="dark_mode", name_zh="开关深色模式", icon="dark_mode",
        category=StepCategory.DISPLAY, status=StepStatus.AVAILABLE,
        description="App 内主题切换（非系统级）",
        params_schema={"state": "开/关/跟随系统"},
        fields=(
            ParamField(
                key="state", label_zh="状态",
                field_type=FieldType.ENUM,
                default="follow_system",
                options=(
                    ("on", "开"),
                    ("off", "关"),
                    ("follow_system", "跟随系统"),
                ),
            ),
        ),
    ),
    StepType.DISPLAY_SIZE: StepTypeMeta(
        type_id="display_size", name_zh="调整显示大小", icon="aspect_ratio",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="系统 API",
        params_schema={"level": "尺寸等级"},
        fields=(
            ParamField(
                key="level", label_zh="尺寸",
                field_type=FieldType.ENUM,
                default="default",
                options=(
                    ("small", "小"),
                    ("default", "默认"),
                    ("large", "大"),
                    ("huge", "超大"),
                ),
            ),
        ),
    ),
    StepType.FONT_SIZE: StepTypeMeta(
        type_id="font_size", name_zh="设置字体大小", icon="format_size",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="系统 API",
        params_schema={"level": "字号等级"},
        fields=(
            ParamField(
                key="level", label_zh="字号",
                field_type=FieldType.ENUM,
                default="default",
                options=(
                    ("small", "小"),
                    ("default", "默认"),
                    ("large", "大"),
                    ("huge", "超大"),
                ),
            ),
        ),
    ),
    StepType.FONT_WEIGHT: StepTypeMeta(
        type_id="font_weight", name_zh="设置字体粗细", icon="format_bold",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="系统 API",
        params_schema={"level": "粗细等级"},
        fields=(
            ParamField(
                key="level", label_zh="粗细",
                field_type=FieldType.ENUM,
                default="regular",
                options=(
                    ("light", "细"),
                    ("regular", "常规"),
                    ("medium", "中等"),
                    ("bold", "粗"),
                ),
            ),
        ),
    ),
    StepType.EYE_CARE: StepTypeMeta(
        type_id="eye_care", name_zh="护眼模式", icon="remove_red_eye",
        category=StepCategory.DISPLAY, status=StepStatus.NOT_IMPLEMENTED,
        description="需系统签名",
        params_schema={"state": "开/关", "color_temp": "色温"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="off", options=_ON_OFF_OPTIONS),
            ParamField(
                key="color_temp", label_zh="色温（K）",
                field_type=FieldType.INT_RANGE,
                default=5000, min_value=3000, max_value=7000,
            ),
        ),
    ),
    StepType.KEEP_AWAKE_ON: StepTypeMeta(
        type_id="keep_awake_on", name_zh="屏幕常亮(开)", icon="lightbulb",
        category=StepCategory.DISPLAY, status=StepStatus.AVAILABLE,
        description="Flet window_always_on_top / keep_alive",
        params_schema={},
        fields=(),
    ),
    StepType.KEEP_AWAKE_OFF: StepTypeMeta(
        type_id="keep_awake_off", name_zh="屏幕常亮(关)", icon="lightbulb_outline",
        category=StepCategory.DISPLAY, status=StepStatus.AVAILABLE,
        description="恢复系统默认",
        params_schema={},
        fields=(),
    ),

    # === 5.4 音频与触感类 ===
    StepType.VOLUME: StepTypeMeta(
        type_id="volume", name_zh="调节音量", icon="volume_up",
        category=StepCategory.AUDIO_HAPTIC, status=StepStatus.NOT_IMPLEMENTED,
        description="AudioManager，Flet 无",
        params_schema={"channel": "音量类型", "value": "0-100"},
        fields=(
            ParamField(
                key="channel", label_zh="音量类型",
                field_type=FieldType.ENUM,
                default="media",
                options=(
                    ("media", "媒体"),
                    ("ring", "铃声"),
                    ("alarm", "闹钟"),
                    ("voice", "语音"),
                ),
            ),
            ParamField(
                key="value", label_zh="音量",
                field_type=FieldType.INT_RANGE,
                default=50, min_value=0, max_value=100,
            ),
        ),
    ),
    StepType.MUTE: StepTypeMeta(
        type_id="mute", name_zh="设置静音", icon="volume_off",
        category=StepCategory.AUDIO_HAPTIC, status=StepStatus.NOT_IMPLEMENTED,
        description="AudioManager",
        params_schema={"mode": "静音/振动/正常"},
        fields=(
            ParamField(
                key="mode", label_zh="模式",
                field_type=FieldType.ENUM,
                default="silent",
                options=(
                    ("silent", "静音"),
                    ("vibrate", "振动"),
                    ("normal", "正常"),
                ),
            ),
        ),
    ),
    StepType.HAPTIC: StepTypeMeta(
        type_id="haptic", name_zh="改变系统触感", icon="vibration",
        category=StepCategory.AUDIO_HAPTIC, status=StepStatus.NOT_IMPLEMENTED,
        description="系统 API",
        params_schema={"level": "触感强度"},
        fields=(
            ParamField(
                key="level", label_zh="触感强度",
                field_type=FieldType.ENUM,
                default="medium",
                options=(
                    ("off", "关闭"),
                    ("low", "低"),
                    ("medium", "中"),
                    ("high", "高"),
                ),
            ),
        ),
    ),
    StepType.VIBRATE: StepTypeMeta(
        type_id="vibrate", name_zh="设备振动", icon="vibrate",
        category=StepCategory.AUDIO_HAPTIC, status=StepStatus.LIMITED,
        description="Flet page.vibration(duration)，限制大",
        params_schema={"duration": "振动时长", "pattern": "振动模式"},
        fields=(
            ParamField(
                key="duration", label_zh="振动时长（毫秒）",
                field_type=FieldType.INT_RANGE,
                default=300, min_value=100, max_value=2000, step=100,
            ),
            ParamField(
                key="pattern", label_zh="振动模式",
                field_type=FieldType.ENUM,
                default="short",
                options=(
                    ("short", "短促"),
                    ("long", "持续"),
                    ("rhythm", "节奏"),
                ),
            ),
        ),
    ),

    # === 5.5 辅助与通知类 ===
    StepType.NOTIFY: StepTypeMeta(
        type_id="notify", name_zh="发送通知", icon="notifications",
        category=StepCategory.AUXILIARY, status=StepStatus.LIMITED,
        description="Flet ft.Notification，可发本地通知",
        params_schema={"title": "标题", "body": "内容", "icon": "图标"},
        fields=(
            ParamField(
                key="title", label_zh="标题",
                field_type=FieldType.STRING,
                required=True,
                placeholder="如：提醒",
            ),
            ParamField(
                key="body", label_zh="内容",
                field_type=FieldType.TEXTAREA,
                required=True,
                placeholder="详细内容...",
            ),
            ParamField(
                key="icon", label_zh="图标",
                field_type=FieldType.STRING,
                placeholder="Material icon name（可选）",
            ),
        ),
    ),
    StepType.ALERT: StepTypeMeta(
        type_id="alert", name_zh="弹出提醒", icon="warning",
        category=StepCategory.AUXILIARY, status=StepStatus.AVAILABLE,
        description="Flet AlertDialog 直接支持",
        params_schema={"content": "提醒内容", "confirm": "确认按钮文本"},
        fields=(
            ParamField(
                key="content", label_zh="提醒内容",
                field_type=FieldType.TEXTAREA,
                required=True,
                placeholder="弹窗显示的内容...",
            ),
            ParamField(
                key="confirm", label_zh="确认按钮文本",
                field_type=FieldType.STRING,
                default="确定",
            ),
        ),
    ),
    StepType.DELAY: StepTypeMeta(
        type_id="delay", name_zh="延时等待", icon="schedule",
        category=StepCategory.AUXILIARY, status=StepStatus.AVAILABLE,
        description="asyncio.sleep()",
        params_schema={"duration": "等待时长(秒)"},
        fields=(
            ParamField(
                key="duration", label_zh="等待时长（秒）",
                field_type=FieldType.INT_RANGE,
                default=1, min_value=0, max_value=3600,
            ),
        ),
    ),
    StepType.SCREEN_RECOGNIZE: StepTypeMeta(
        type_id="screen_recognize", name_zh="屏幕内容识别", icon="document_scanner",
        category=StepCategory.AUXILIARY, status=StepStatus.NOT_IMPLEMENTED,
        description="需 MediaProjection + Tesseract OCR",
        params_schema={"target": "目标文本/图像", "threshold": "匹配阈值"},
        fields=(
            ParamField(
                key="target", label_zh="目标内容",
                field_type=FieldType.STRING,
                required=True,
                placeholder="屏幕上要识别的文本或图像路径",
            ),
            ParamField(
                key="threshold", label_zh="匹配阈值（%）",
                field_type=FieldType.INT_RANGE,
                default=80, min_value=0, max_value=100,
            ),
        ),
    ),
    StepType.RUN_SUBTASK: StepTypeMeta(
        type_id="run_subtask", name_zh="执行子任务", icon="call_split",
        category=StepCategory.AUXILIARY, status=StepStatus.AVAILABLE,
        description="子任务嵌套调用",
        params_schema={"subtask_id": "子任务ID", "name": "子任务名"},
        fields=(
            ParamField(
                key="subtask_id", label_zh="子任务 ID",
                field_type=FieldType.STRING,
                required=True,
                placeholder="如：sub_001",
            ),
            ParamField(
                key="name", label_zh="子任务名",
                field_type=FieldType.STRING,
                placeholder="如：每日打卡流程",
            ),
        ),
    ),
    StepType.FLASHLIGHT: StepTypeMeta(
        type_id="flashlight", name_zh="开启手电筒", icon="flashlight_on",
        category=StepCategory.AUXILIARY, status=StepStatus.NOT_IMPLEMENTED,
        description="Camera2 API，Flet 无",
        params_schema={"state": "开/关"},
        fields=(
            ParamField(key="state", label_zh="状态", field_type=FieldType.ENUM, default="on", options=_ON_OFF_OPTIONS),
        ),
    ),
}


def get_step_type_meta(step_type: StepType) -> StepTypeMeta:
    """获取步骤类型元数据"""
    return STEP_TYPE_REGISTRY[step_type]


def get_steps_by_category(category: StepCategory) -> list[StepTypeMeta]:
    """按分类获取步骤类型列表"""
    return [meta for meta in STEP_TYPE_REGISTRY.values() if meta.category == category]


def get_steps_by_status(status: StepStatus) -> list[StepTypeMeta]:
    """按状态获取步骤类型列表"""
    return [meta for meta in STEP_TYPE_REGISTRY.values() if meta.status == status]


def count_by_status() -> dict[StepStatus, int]:
    """统计各状态的步骤类型数量"""
    counts: dict[StepStatus, int] = {s: 0 for s in StepStatus}
    for meta in STEP_TYPE_REGISTRY.values():
        counts[meta.status] += 1
    return counts


def count_by_category() -> dict[StepCategory, int]:
    """统计各分类的步骤类型数量"""
    counts: dict[StepCategory, int] = {c: 0 for c in StepCategory}
    for meta in STEP_TYPE_REGISTRY.values():
        counts[meta.category] += 1
    return counts
