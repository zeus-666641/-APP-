# step_recorder UI 设计规范

> 本文件是 step_recorder App 的视觉与交互规范，开发者必读。
> 配套 HTML 高保真原型：`step_recorder_ui.html`（同目录，浏览器打开可查所有页面/状态）。
> 所有 Flet 视图与组件必须严格遵守本规范的 Design Tokens。
>
> 变更记录:
> - 2026-07-20 初版（基于 M1+M2+M4+M5 已实现代码逆向提取）

---

## 一、Design Tokens（设计令牌）

### 1.1 配色（Color Palette）

| Token | HEX | 用途 | 使用位置 |
|---|---|---|---|
| `--accent` | `#2563eb` | 主色（链接、按钮、激活态） | AppBar、添加按钮、执行按钮、图标块 |
| `--accent-light` | `#dbeafe` | 主色浅色（图标块背景） | 任务图标块、统计卡片图标块 |
| `--ink` | `#1a1a2e` | 主文字（标题、卡片主名） | 任务名、统计数值、section-title |
| `--muted` | `#6b7280` | 次要文字（描述、计数、时间） | "共 N 项"、相对时间、触发源 |
| `--rule` | `#e5e7eb` | 分隔线、卡片描边 | 卡片 border、分隔线、空进度条 |
| `--bg2` | `#ffffff` | 卡片背景 | 所有卡片 |
| `--danger` | `#ef4444` | 危险/失败 | 删除按钮、失败状态、错误信息 |
| `--success` | `#10b981` | 成功 | 成功状态徽章、成功率柱状条 |
| `--warning` | `#f59e0b` | 警告/受限 | 暂停状态、平均时长、警告 |
| `--disabled` | `#94a3b8` | 禁用 | 禁用任务、未实现步骤 |

### 1.2 任务状态色板（TaskStatus）

| 状态 | 标签 | 颜色 |
|---|---|---|
| IDLE（空闲） | 灰色 | `--muted` |
| RUNNING（执行中） | 蓝色 | `--accent` |
| PAUSED（已暂停） | 橙色 | `--warning` |
| ERROR（出错） | 红色 | `--danger` |
| DISABLED（已禁用） | 灰色 | `--disabled` |

### 1.3 执行日志状态徽章色（ExecutionStatus）

| 状态 | 中文 | 颜色 |
|---|---|---|
| SUCCESS | 成功 | `--success` |
| FAILED | 失败 | `--danger` |
| ABORTED | 已中止 | `--muted` |
| RUNNING | 执行中 | `--accent` |
| SKIPPED | 已跳过 | `--warning` |

### 1.4 字号（Font Size）

| Token | px | Weight | 用途 |
|---|---|---|---|
| `--fs-title-lg` | 18 | W_600 | 页面标题（AppBar title、抽屉标题） |
| `--fs-title` | 16 | W_600 | 关于卡片 app 名 |
| `--fs-body-strong` | 14 | W_600 | 任务名、section-title、统计数值大字 |
| `--fs-body` | 13 | W_500 | 任务排行任务名 |
| `--fs-meta` | 12 | W_400 | 计数（"共 N 项"）、相对时间、触发源、日期短格式 |
| `--fs-caption` | 11 | W_400 | "N 个步骤"、卡片描述 |
| `--fs-micro` | 10 | W_500 | 状态文字、状态徽章 |

### 1.5 间距（Spacing）

| Token | px | 用途 |
|---|---|---|
| `--sp-page-x` | 16 | 页面左右内边距（SafeArea 内的内容） |
| `--sp-card-x` | 12 | 卡片左右内边距 |
| `--sp-card-y-top` | 10 | 卡片上内边距 |
| `--sp-card-y-bottom` | 8 | 卡片下内边距 |
| `--sp-list-gap` | 8 | 列表项之间间距 |
| `--sp-section-y` | 8 | section-title 上下间距 |
| `--sp-indent-step` | 24 | 任务树每层缩进 |
| `--sp-icon-text` | 8 | 图标与文字之间间距 |

### 1.6 圆角（Border Radius）

| Token | px | 用途 |
|---|---|---|
| `--br-card` | 10 | 所有卡片 |
| `--br-icon-block` | 8 | 图标块、统计卡片图标块 |
| `--br-badge` | 4 | 状态徽章、状态点 |
| `--br-button` | 8 | TextField、Dropdown |

### 1.7 尺寸（Size）

| Token | px | 用途 |
|---|---|---|
| `--size-icon-block` | 36×36 | 任务图标块、统计图标块 |
| `--size-icon-block-radius` | 8 | 图标块圆角 |
| `--size-status-dot` | 8×8 | 任务卡片状态点 |
| `--size-touch-min` | 48×48 | 触控最小点击区域（MOB3） |
| `--size-app-width` | 400 | 应用窗口宽度（开发期） |
| `--size-app-height` | 800 | 应用窗口高度（开发期） |

---

## 二、组件规范（Component Spec）

### 2.1 TaskCard（任务卡片）

> 用于任务列表（home_view tasks tab）和任务树渲染。

**布局**（自上而下）:
1. **主行** Row：`[图标块] [任务名 + 状态点 + 状态文字] [执行按钮 + 启用开关 + (展开按钮)]`
2. **底部行** Row：`[删除按钮] [expand]`

**视觉**:
- 容器：`bg2` 背景，`rule` 描边 1px，`br-card` 圆角
- padding：`sp-card-x, sp-card-x, sp-card-y-top, sp-card-y-bottom`
- 图标块：`size-icon-block`，`accent-light` 背景，`br-icon-block` 圆角，内含 18px `accent` 色 Icon
- 任务名：`fs-body-strong`，`ink` 色（禁用时 `muted`）
- 状态点：`size-status-dot`，状态色
- 状态文字：`fs-micro`，状态色
- 执行按钮：`accent` 色 IconButton 14px
- 启用开关：`Switch` scale=0.8
- 展开按钮：`muted` 色 IconButton 14px（仅有子任务时显示）
- 删除按钮：`danger` 色 TextButton + DELETE_OUTLINE 图标（左下角）

**交互**:
- 卡片整体点击 → 进入详情（`on_click`）
- 删除按钮点击 → 二次确认 AlertDialog（modal，红色"确认删除"按钮）
- 删除按钮 `e.stop_propagation = True` 阻止冒泡到卡片
- 启用开关切换 → `on_toggle_enabled(task_id, value)`
- 执行按钮点击 → `on_execute(task_id)`
- 展开按钮点击 → `on_toggle_expand(task_id)`
- 鼠标悬停 → `bgcolor` 变 `#f9fafb`

### 2.2 StepCard（步骤卡片）

> 用于步骤编辑器列表。

**布局**:
- 序号圆圈 + 图标块 + 步骤名/参数摘要 + 执行按钮 + 状态开关 + 操作按钮组（删除/展开/添加子步骤）
- 所有操作图标统一 14px

### 2.3 LogCard（执行日志卡片）

> 用于 logs_view 列表。

**布局**（自上而下）:
1. **任务名行** Row：`[任务图标块] [任务名 + 步骤数] [状态徽章]`
2. **元信息行** Row：`[触发源标签] [相对时间] [耗时]`
3. **错误信息**（仅失败/中止时显示）：红底容器 + 红色文字
4. **底部行** Row：`[删除按钮] [expand]`

**视觉**:
- 任务图标块：`size-icon-block`，`accent-light` 背景
- 任务名：`fs-body-strong`，`ink` 色
- 状态徽章：状态色背景，白字 `fs-micro`
- 触发源标签：`rule` 灰底 + `muted` 字 `fs-meta`
- 删除按钮：`danger` 色 TextButton + DELETE_OUTLINE（左下角，与 TaskCard 一致）

### 2.4 section-title（分区分组标题）

> 列表上方"全部任务 / 共 N 项"风格的分组标题。

**布局**:
- Row：`[标题（fs-body-strong, ink, W_600）] [计数（fs-meta, muted）]`
- `MainAxisAlignment.SPACE_BETWEEN`
- padding：`sp-page-x, sp-page-x, 8, 4`

**变体**:
- 统计页：标题 + 右侧补充（如 "Top 5"、"最近 7 天" + "N 次"）
- 日志列表：标题 + 计数（"共 N 项"）

### 2.5 AppBar（应用栏）

**布局**:
- `leading`：设置 IconButton（白色图标）
- `title`：ft.Text("任务管理")，白色
- `actions`：添加任务 Button（白底 + accent 蓝字 + ADD 图标）
- `bgcolor`：`accent`
- `color`：white

**变体**:
- 详情页 AppBar：`leading`=返回 IconButton（ARROW_BACK）+ `title`=页面标题
- 抽屉编辑：图标 + "新建任务"/"编辑任务" 标题

### 2.6 NavigationBar（底部导航）

**3 tab（Q50 决策）**:
1. 任务（CHECK_BOX_OUTLINED / CHECK_BOX）
2. 统计（BAR_CHART_OUTLINED / BAR_CHART）
3. 日志（LIST_ALT_OUTLINED / LIST）

**交互**:
- 任务 tab：保持当前页（默认）
- 统计/日志 tab：点击直接 `page.go("/stats")` 或 `page.go("/logs")` 跳路由

### 2.7 Dialog（对话框）

**AlertDialog**（二次确认，modal）:
- `title`：ft.Text("确认删除")
- `content`：ft.Text("确定要删除任务「X」吗？此操作不可撤销。")
- `actions`：[取消 Button, 确认删除 Button（danger 背景白字）]
- 通过 `page.overlay.append(dialog)` + `dialog.open = True` 显示

### 2.8 StatsCard（统计卡片）

**布局**:
- Row：`[图标块（36x36 accent-light）] [标题 + 数值]`
- 图标块图标 20px，颜色按类型（accent/success/warning）
- 标题：`fs-meta` muted
- 数值：`fs-body-strong` ink W_600

### 2.9 Drawer（抽屉式侧滑）

**布局**:
- 容器 width=360（实际通过 Stack + alignment=RIGHT 实现侧滑效果）
- 内含 Column：标题 + 表单字段 + 图标网格 + 开关 + 操作按钮
- 外层 `_overlay` Container：半透明黑色遮罩 `#80000000`，visible=False 默认隐藏

**交互**（Q52）:
- 点击遮罩关闭（`_handle_overlay_click`）
- 取消按钮关闭（`_handle_cancel`）
- 关闭时清 `_overlay.content = None` 防止黑屏
- `e.stop_propagation = True` 阻止内部按钮事件冒泡

---

## 三、页面规范（Page Spec）

### 3.1 /tasks（任务列表，HomeView）

**结构**:
```
AppBar（设置 + 任务管理 + 添加任务）
SafeArea
  Stack
    Column
      section-title: "全部任务" + "共 N 项"
      TaskTree（scroll）
    _overlay（抽屉遮罩，默认隐藏）
NavigationBar（3 tab）
```

### 3.2 /stats（统计页，StatsView）

**结构**:
```
AppBar（返回 + 执行统计）
SafeArea
  Column（scroll）
    section-title: "汇总统计"
    OverallCards（2x2 网格：总执行次数 / 成功率 / 平均时长 / 任务数）
    section-title: "任务排行" + "Top 5"
    TopTasksList（排名徽章 + 任务名 + 成功率柱状条）
    section-title: "最近 7 天" + "N 次"
    DailyChart（柱状图）
    section-title: "按触发源"
    TriggerSourceList（标签 + 柱状条 + 百分比）
```

### 3.3 /logs（日志列表，LogsView）

**结构**:
```
AppBar（返回 + 执行日志）
SafeArea
  Column（scroll）
    SearchField（搜索框）
    FilterRow1: 状态 Dropdown + 触发源 Dropdown
    FilterRow2: 任务 Dropdown + 时间范围 Dropdown
    GroupModeSegmented（按日期 / 平铺）
    section-title: "执行日志" + "共 N 项"
    ListContainer
      LogCard × N（按日期分组时每组前有分组标题）
    EmptyState（无日志时）
```

### 3.4 /logs/{id}（日志详情，LogDetailView）

**结构**:
```
AppBar（返回 + 任务名）
SafeArea
  Column（scroll）
    OverviewCard（任务名 + 状态徽章 + 开始时间 + 耗时 + 触发源）
    ErrorBlock（失败时显示错误信息）
    SectionTitle: "执行步骤"
    Timeline（时间轴步骤列表）
      TimelineNode × N: [序号圆圈 + 图标 + 步骤名 + 状态点 + 耗时]
```

### 3.5 /settings（设置页，SettingsView）

**结构**:
```
AppBar（返回 + 设置）
SafeArea
  Column（scroll）
    SectionTitle: "显示设置"
    Dropdown: 主题模式 / 添加步骤入口
    SectionTitle: "列表交互"
    Switch: 显示拖拽手柄 / 显示换位按钮
    Dropdown: 拖拽手柄位置
    SectionTitle: "执行设置"
    Switch: 默认屏幕常亮 / 通知提醒
    Dropdown: 执行失败处理
    TextField: 失败重试次数
    SectionTitle: "步骤间停顿"
    Switch: 启用停顿
    TextField: 最小停顿 / 最大停顿
    SectionTitle: "日志管理"
    Switch: 启用自动清理
    TextField: 保留日志条数（1-9999）
    SectionTitle: "关于"
    AboutCard（应用名 + 版本 + 技术栈 + 平台）
```

### 3.6 /step_editor（步骤编辑器）

**结构**:
```
AppBar（返回 + 步骤编辑 + 添加步骤按钮）
SafeArea
  Column（scroll）
    section-title: "执行步骤" + "共 N 项"
    DraggableList（StepCard × N）
    StepTypePicker（抽屉/底部展开，5 分类标签 + 4 列网格）
    ParamEditor（抽屉，按 FieldType 动态表单）
```

---

## 四、交互规范（Interaction Spec）

### 4.1 触控优化（MOB3）
- 所有可点击元素最小 48×48dp
- 删除按钮虽小，但通过 IconButton 内边距扩展触控区域
- 卡片整体可点击，避免误触

### 4.2 二次确认（危险操作）
- 删除任务、删除日志、删除步骤：均弹 AlertDialog（modal）
- 标题："确认删除"
- 内容："确定要删除 X 吗？此操作不可撤销。"
- 按钮：[取消, 确认删除（红色）]

### 4.3 反馈
- 操作成功：SnackBar（如"任务已保存"）
- 操作失败：SnackBar（错误信息）
- 长操作：进度提示（M7 接入）
- 鼠标悬停：卡片 `bgcolor` 变 `#f9fafb`

### 4.4 路由跳转
- 统计/日志 tab 点击 → `page.go("/stats")` / `page.go("/logs")`
- 任务卡片点击 → `page.go("/step_editor")`（M1 后从卡片进步骤编辑器）
- 日志卡片点击 → `page.go("/logs/{id}")`
- 返回按钮 → `page.go("/tasks")`（栈底保留 HomeView）

### 4.5 抽屉关闭（Q52）
- 点击遮罩空白处关闭
- 取消按钮关闭
- 关闭时清 `_overlay.content = None` 避免黑屏
- `e.stop_propagation = True` 阻止内部事件冒泡

---

## 五、文件组织规范

```
docs/ui_design/
├── ui_design_spec.md      # 本文件（开发者读）
└── step_recorder_ui.html  # HTML 高保真原型（设计审阅）
```

---

## 六、变更与维护

- 任何 UI 视觉变更（配色、字号、间距、组件结构）必须同步更新本规范
- 任何新增页面/组件必须先更新本规范再编码
- 任何 Design Token 变更必须更新所有使用该 Token 的组件
- HTML 原型与实际 Flet 视图应保持视觉一致（允许细微渲染差异）
