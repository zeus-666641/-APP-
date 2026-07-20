# PRD · step_recorder 步骤记录器（Flet 子集版）

> 移动App工厂 · 项目2 产品规划 · 输出
> 骨架对应：2.1 PRD撰写 / 2.2 架构设计 / 2.3 任务拆解
> 基础 PRD：`步骤记录器v1.0`（HTML）
> 实现范围：`docs/prd/scope.md`

## 0. 元信息

| 项 | 值 |
|---|---|
| App 名 | `step_recorder`（英文蛇形） |
| 中文名 | 步骤记录器 |
| 版本 | 0.1.0 (MVP) |
| 平台 | Android only（API 24+） |
| 技术栈 | Python 3.10+ / Flet 0.86+ / pydantic 2 / uv |
| 仓库路径 | `apps/step_recorder/` |
| 立项决策 | 详见 `记忆/决策.md`（栈冲突后用户选择 Flet 子集实现） |
| 工作分支 | `step-recorder`（origin/zeus-666641-步骤记录器） |
| 关键约束 | UI 中置灰显示不可做项 + 点击弹"尚未完成"提示 |

## 1. Flet 子集功能清单（基于原 PRD 13 章节裁剪）

### M0 数据模型层（最后做）

**5 表设计**（基于原 PRD 13.2 ER 图 + 父子任务扩展）：

```python
# Task：任务
class Task:
    id: str                        # uuid
    name: str
    description: str = ""
    icon: str = "play_arrow"       # Material icon
    category: str = "default"
    enabled: bool = True
    keep_screen_on: bool = False
    created_at: datetime
    updated_at: datetime

# TaskRelation：父子关系（独立关系表）
class TaskRelation:
    id: str
    parent_id: str                  # FK Task
    child_id: str                   # FK Task
    sort_order: int                 # 同级排序

# Step：步骤
class Step:
    id: str
    task_id: str                    # FK Task
    step_order: int                 # 顺序
    type: StepType                  # 步骤类型枚举
    params: dict                    # 参数
    enabled: bool = True
    on_failure: str = "abort"       # abort | skip

# Trigger：触发器
class Trigger:
    id: str
    task_id: str                    # FK Task
    trigger_type: str               # manual | timer | interval | random
    trigger_config: dict            # 配置
    condition_config: dict = {}

# ExecutionLog：执行日志
class ExecutionLog:
    id: str
    task_id: str
    start_time: datetime
    end_time: datetime | None
    status: str                     # running | success | failed | aborted
    trigger_source: str
    duration_ms: int = 0

# StepLog：步骤日志
class StepLog:
    id: str
    execution_id: str               # FK ExecutionLog
    step_id: str
    step_order: int
    status: str                     # success | failed | skipped | not_implemented
    error_message: str = ""
    duration_ms: int = 0
```

**StepType 枚举**（覆盖 PRD 第 5 章全部类型，含"未实现"标记）：

```python
class StepType(str, Enum):
    # 5.1 模拟操作类
    CLICK = "click"                          # ⚠️ 受限（App内）
    SWIPE = "swipe"                          # ⚠️ 受限（App内）
    GO_HOME = "go_home"                      # ⚠️ 受限（App内）
    GO_BACK = "go_back"                      # ⚠️ 受限（App内）
    OPEN_APP = "open_app"                    # ❌ 未实现
    SWITCH_APP = "switch_app"                # ❌ 未实现
    DIAL = "dial"                            # ⚠️ 受限（intent启动）
    OPEN_URL = "open_url"                    # ✅

    # 5.2 系统控制类（全部 ❌ 未实现）
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    AIRPLANE = "airplane"
    LOCATION = "location"
    HOTSPOT = "hotspot"
    NFC = "nfc"
    MOBILE_DATA = "mobile_data"
    DND = "dnd"
    POWER_SAVE = "power_save"
    FOCUS = "focus"
    DRIVING = "driving"
    LOCK_SCREEN = "lock_screen"
    SCREEN_OFF = "screen_off"
    POWER = "power"

    # 5.3 显示设置类
    BRIGHTNESS = "brightness"                # ❌
    AUTO_ROTATE = "auto_rotate"              # ❌
    DARK_MODE = "dark_mode"                  # ✅（App内）
    DISPLAY_SIZE = "display_size"            # ❌
    FONT_SIZE = "font_size"                  # ❌
    FONT_WEIGHT = "font_weight"              # ❌
    EYE_CARE = "eye_care"                    # ❌
    KEEP_AWAKE_ON = "keep_awake_on"          # ✅
    KEEP_AWAKE_OFF = "keep_awake_off"         # ✅

    # 5.4 音频与触感类
    VOLUME = "volume"                        # ❌
    MUTE = "mute"                            # ❌
    HAPTIC = "haptic"                        # ❌
    VIBRATE = "vibrate"                      # ⚠️ 受限

    # 5.5 辅助与通知类
    NOTIFY = "notify"                        # ⚠️ 受限（本地通知）
    ALERT = "alert"                          # ✅
    DELAY = "delay"                          # ✅
    SCREEN_RECOGNIZE = "screen_recognize"    # ❌
    RUN_SUBTASK = "run_subtask"              # ✅
    FLASHLIGHT = "flashlight"                # ❌
```

### M1 任务管理层

- 任务 CRUD（增/删/改/查）
- 任务分组（category 字段）
- 任务启停（enabled 字段）
- **父子任务嵌套**（独立 TaskRelation 表）
  - 父任务下挂子任务
  - 树形 UI 展示（缩进 + 折叠）
  - 拖动调整父子关系
- 任务列表拖拽排序
- 底部导航（4 个 tab：任务 / 步骤 / 统计 / 设置）
- 深色模式切换

### M2 步骤编辑器（先做）

- 步骤列表 UI（卡片式，按 step_order 排序）
- 添加步骤弹窗（5 大分类网格展示所有 StepType）
  - ✅ 类型可正常选择
  - ⚠️ 受限类型加角标"受限"
  - ❌ 不可做类型加角标"未实现"，置灰但可点击
  - 选中 ❌ 类型弹提示"该功能尚未完成，是否继续保存为占位？"
- 步骤参数编辑面板（按 type 动态显示参数表单）
- 步骤列表项支持拖拽排序
- 步骤启用/禁用切换
- 步骤删除
- 子任务嵌套调用步骤（run_subtask）

### 触发器系统（M3 后续）
- 手动触发 ✅
- 定时/间隔/随机触发 ⚠️（前台 asyncio.sleep）
- App 启动时弹引导：「请去系统设置开启自启动白名单 + 电池优化不限制」
- 条件引擎 4 类（时间/网络/应用/系统状态）
  - 时间类 ⚠️ 前台可用
  - 其他 ❌

### 统计模块（M4 后续）
- 执行次数/成功率/平均时长
- 按任务/按天/按触发源统计
- ECharts 风格图表（用 Flet Canvas 自绘）

### 执行日志模块（M5 后续）
- 日志列表 + 详情
- 步骤级日志展开

### 系统设置（M6 后续）
- 深色模式（跟随系统/亮/暗）
- 字号（App 内）
- 执行参数（失败处理策略/默认延时）
- 关于（版本/作者）

## 2. UI 设计规范（PRD 第 12 章 全部保留）

| 项 | 规范 |
|---|---|
| 设计风格 | 企业级极简 |
| 主色 | 深蓝 #2563eb + 紫 #7c3aed |
| 暗色模式 | 自适应 |
| 底部导航 | 4 tab：任务/步骤/统计/设置 |
| 卡片圆角 | 12px |
| 触控区域 | ≥48dp |
| 字体 | PingFang SC / Microsoft YaHei |
| 表格行 hover | 浅蓝背景 |

## 3. 启动引导

App 首次启动 + 每次启动后第一次显示：
1. 欢迎卡片
2. 「为保证后台触发器正常工作，请去系统设置 → 应用 → step_recorder → 开启自启动 + 电池优化不限制」
3. 「不再提示」按钮

## 4. 不可做项处理规范

- UI 中正常显示该步骤类型，但加角标「未实现」
- 用户点击不可做项类型时：
  1. 弹 AlertDialog：「该功能需要 Android 原生 API 支持，Flet 框架暂不提供。是否保存为占位步骤？后续接入原生插件时可激活。」
  2. 选「保存为占位」→ 创建步骤，运行时跳过并记录 StepLog.status="not_implemented"
  3. 选「取消」→ 不创建
- 执行时遇到 not_implemented 步骤：跳过，写日志，不报错

## 5. 验收标准

- [ ] 可创建/编辑/删除任务
- [ ] 任务支持父子嵌套（≥2 层）
- [ ] 任务列表与步骤列表支持拖拽排序
- [ ] 步骤编辑器可显示全部 30+ 种 StepType
- [ ] 不可做项类型点击弹「尚未完成」提示
- [ ] 步骤参数表单按 type 动态渲染
- [ ] 底部 4 tab 导航生效
- [ ] 深色模式切换
- [ ] 启动引导显示并支持「不再提示」
- [ ] 手动触发可执行任务流
- [ ] 不可做项执行时跳过并记日志
- [ ] 延时/弹窗/通知/打开链接/子任务调用可正常执行

## 6. 架构设计（基于模板扩展）

```
apps/step_recorder/
├── main.py                          # Flet 入口
├── pyproject.toml                   # 依赖
├── routes.py                        # 路由表
├── config/
│   └── settings.py
├── models/                          # M0 数据层
│   ├── task.py                      # Task + TaskRelation
│   ├── step.py                      # Step + StepType 枚举
│   ├── trigger.py                   # Trigger
│   └── log.py                       # ExecutionLog + StepLog
├── services/                        # M0 业务层
│   ├── storage.py                   # JSON 存储
│   ├── task_service.py              # M1
│   ├── step_service.py              # M2
│   ├── relation_service.py          # M1 父子关系
│   ├── trigger_service.py           # M3
│   ├── executor_service.py          # 执行引擎
│   └── stats_service.py             # M4
├── controllers/
│   ├── task_controller.py
│   ├── step_controller.py
│   └── executor_controller.py
├── views/                           # M2/M1 UI 层
│   ├── home_view.py                 # 任务列表（M1）
│   ├── step_editor_view.py          # 步骤编辑器（M2）
│   ├── task_edit_view.py            # 任务编辑（M1）
│   ├── stats_view.py                # 统计（M4）
│   ├── logs_view.py                 # 日志（M5）
│   ├── settings_view.py            # 设置（M6）
│   └── components/
│       ├── step_card.py             # 步骤卡片（M2）
│       ├── step_type_picker.py      # 步骤类型选择面板（M2）
│       ├── param_editor.py          # 参数动态表单（M2）
│       ├── task_tree.py             # 父子树形列表（M1）
│       ├── draggable_list.py        # 拖拽列表组件
│       └── not_implemented_dialog.py # 不可做项提示对话框
├── i18n/
│   ├── zh.json
│   └── en.json
└── tests/
    ├── test_step_type.py
    ├── test_step_service.py
    ├── test_task_service.py
    ├── test_relation_service.py
    ├── test_executor.py
    └── test_storage.py
```

## 7. 任务清单（M2→M1→M0 顺序，详见 step_recorder_tasks.md）

UI-first 开发模式：
- M2 步骤编辑器 UI（用 mock 数据）
- M1 任务管理 UI（接入部分数据）
- M0 数据模型 + 存储（重构 mock 为真实存储）
- M3-M6 后续迭代
