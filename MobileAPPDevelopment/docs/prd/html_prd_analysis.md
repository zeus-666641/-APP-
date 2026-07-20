# 步骤记录器 · HTML PRD 学习与分析

> 来源：`步骤记录器v1.0`（HTML PRD，13 章节）
> 目的：分析 PRD 中的界面设计、可复用样式、可借鉴的交互模式，对比当前 Flet 实现差距，提出改进建议（需用户决策）。
> 与 `scope.md` 互补：scope 关注"能不能实现"，本文关注"实现得好不好/像不像"。

---

## 一、HTML PRD 设计风格速览

### 1.1 视觉风格
- **定位**：极简企业风（PRD 第 12 章 12.1）
- **配色体系**（CSS 变量）：
  - `--bg: #f5f6f8`（页面背景 浅灰）
  - `--bg2: #ffffff`（卡片背景 白）
  - `--ink: #1a1a2e`（主文字 深蓝黑）
  - `--muted: #6b7280`（辅助文字 中灰）
  - `--rule: #e5e7eb`（分隔线/边框 浅灰）
  - `--accent: #2563eb`（主色 蓝）
  - `--accent2: #7c3aed`（副主色 深紫）
  - `--accent-light: #eff6ff`（主色浅背景）
  - `--success: #10b981`（成功 绿）
  - `--warning: #f59e0b`（警告 黄）
  - `--danger: #ef4444`（危险 红）
- **深色模式**：
  - `--bg: #0f172a`（深蓝黑）
  - `--bg2: #1e293b`（卡片背景）
  - `--ink: #f1f5f9`（主文字 接近白）
  - `--muted: #94a3b8`
  - `--rule: #334155`
  - `--accent: #3b82f6`（亮蓝，深色模式下更亮）
  - `--accent-light: #1e3a5f`
- **布局规范**：
  - 圆角 10–12px
  - 间距增量 8/12/16/20/24px
  - 字号层级 大标题 18-20 / 正文 14-15 / 辅助 12-13

### 1.2 组件样式对照表（与当前 Flet 实现）

| 组件 | HTML PRD CSS | 当前 Flet 实现 | 差距 |
|---|---|---|---|
| `.step-item` 卡片 | gap:12, padding:12, border-radius:10, border 1px `--rule` | `_CARD_WIDTH=360, padding=12, border_radius=10, border 1px _RULE, spacing=12` | ✅ 已对齐 |
| `.step-num` 序号圆圈 | 28x28, `--accent` 背景, 白字 13px W_600, border-radius 50% | 28x28, `_ACCENT` 背景, 白字 13px W_600, border_radius=14 | ✅ 已对齐 |
| `.step-icon` 图标块 | 36x36, `--accent-light` 背景, 18px 图标, border-radius 8 | 36x36, `_ACCENT_LIGHT` 背景, 18px icon, border_radius 8 | ✅ F8 已对齐 |
| `.step-name` 标题 | 14px W_600 `--ink` | 14px W_600 `#1a1a2e` | ✅ 已对齐 |
| `.step-detail` 副标题 | 12px `--muted` | 12px `_MUTED` | ✅ 已对齐 |
| `.step-actions` 操作按钮 | gap:4, 14px 图标, `--muted` 主色 | IconButton 18px, gap=2 | ⚠️ 图标尺寸偏大 |
| `.add-btn` 添加按钮 | `--accent` 背景, 白字 14px W_500, border-radius 10, padding 10px | IconButton（齿轮+加号） | ⚠️ 风格不一致，PRD 是胶囊状按钮 |
| `.section-title` 分组标题 | 14px W_600, flex 两端对齐 | 未实现 | ❌ 缺失 |
| `.trigger-tabs` 触发器标签页 | flex, gap 6, 12px W_500, 选中项 `--accent` 背景白字 | 未实现（M3 触发器系统） | ❌ 待 M3 |
| `.toggle-row` 开关行 | flex 两端对齐, padding 14px 0, border-bottom 1px `--rule` | 仅在卡片内 Switch，未独立成行 | ⚠️ 设置页可借鉴 |
| `.stats-row` 统计卡片 | grid 3 列, gap 8, padding 12, border-radius 10 | 未实现（M4 统计） | ❌ 待 M4 |
| `.rank-item` 排行项 | flex, gap 10, padding 10px 0, border-bottom 1px | 未实现（M4） | ❌ 待 M4 |
| `.bottom-nav` 底部导航 | absolute bottom, flex 三栏均分, padding 12px 0 | 未实现 | ❌ 待 M1（任务管理 UI） |
| `.phone-frame` 手机外壳 | 320px 宽, border-radius 32, padding 12, 2px border | 不需要（Flet 在真机/模拟器无外壳） | — |
| `.modal-overlay` 底部弹窗 | absolute 全屏, 半透明黑, items-align flex-end | Stack + overlay（已实现抽屉） | ✅ 等价 |
| `.fab` 浮动按钮 | 56x56, `--accent` 背景, 白字 24px, border-radius 50%, 阴影 | FAB（已实现，可开关） | ✅ 已对齐 |
| `.callout` 提示框 | `--accent-light` 背景, 4px 左边框, padding 16x20 | 未实现 | ⚠️ 可借鉴 |
| `.feature-card` 功能卡片 | hover 蓝边 + 上浮 2px + 阴影 | 未实现 | ⚠️ 桌面端语义，移动端可不要 |

---

## 二、章节级差距分析

### 2.1 已实现（M2 完成 + 23 条需求）

| PRD 章节 | 当前实现 | 状态 |
|---|---|---|
| 四、步骤编辑器 | 步骤列表 + 添加抽屉 + 拖拽 + 换位 + 卡片样式 | ✅ |
| 四.1 添加步骤弹窗 | StepTypePicker + ParamEditor | ✅ |
| 五、步骤类型 30+ | 全部枚举 + StepTypeMeta + ParamField | ✅ |
| 六、触发器系统（部分） | StepCardData 加 trigger_date / trigger_count 字段 | ⚠️ 仅字段，UI 未实现 |
| 十一、系统设置 | theme_mode/add_step_entry/drag_handle/swap/pause 等 | ✅ |

### 2.2 缺失但可实现（按模块排期）

| PRD 章节 | 缺失内容 | 模块 | 优先级 |
|---|---|---|---|
| 三、任务管理 | Task 列表 + 编辑 + 父子嵌套 + 启停 | M1 | 高 |
| 三.2 任务列表（含子任务嵌套调用） | 任务树 + 缩进 + 折叠 | M1 | 高 |
| 六、触发器配置 UI | 4 种触发模式标签页 + 表单 | M3 | 中 |
| 七、条件触发引擎（前台部分） | 条件组合逻辑 UI | M3 扩展 | 低 |
| 八、数据统计 | stats_row + chart-card + rank-item | M4 | 中 |
| 九、执行日志 | log 列表 + 详情 + 步骤展开 | M5 | 中 |
| 十二、底部导航 | 3 栏 NavigationBar（任务/日志/统计） | M1 | 高（M1 时引入） |
| 十二、UI 规范（部分细节） | callout / section-title / toggle-row | 渐进 | 低 |

### 2.3 不可实现（已在 unsupported_features.md 记录）

| PRD 章节 | 不可实现内容 | 原因 |
|---|---|---|
| 五.2 系统控制类 14 项 | 蓝牙/WiFi/飞行/定位/热点/NFC/移动数据/勿扰/省电/专注/驾车/锁屏/息屏/开关机 | 系统签名权限 + Flet 无 API |
| 五.3 部分显示设置 | 亮度/方向锁定/显示大小/字体大小/字体粗细/护眼模式 | 系统 API |
| 五.4 部分音频触感 | 调节音量/静音/触感 | AudioManager |
| 五.5 屏幕内容识别 | OCR | 需 MediaProjection |
| 五.5 开启手电筒 | Camera2 API | Flet 无 |
| 七.2 网络条件监听 | 后台 BroadcastReceiver | Flet 无 |
| 七.3 应用类条件 | UsageStatsManager | Flet 无 |
| 七.4 系统状态类条件 | BroadcastReceiver | Flet 无 |
| 十、悬浮窗快捷操作 | WindowManager TYPE_APPLICATION_OVERLAY | Flet 无（U2） |
| 十一.3 无障碍服务绑定 | AccessibilityService | Flet 无（U1） |
| 六 后台定时触发器 | AlarmManager | Flet 无 |

---

## 三、关键交互模式分析

### 3.1 步骤项交互（PRD 第 4 章）
**HTML PRD 原文**：
1. 点击"+ 添加步骤"按钮弹出步骤类型选择面板（底部弹窗） ✅ 已实现
2. 长按步骤项可进入拖拽排序模式 → 当前实现：拖拽手柄（IconButton）+ 换位按钮
3. 点击步骤项可展开/收起详细参数配置 → 当前实现：点击序号圆圈触发编辑抽屉
4. 删除按钮点击后需二次确认，防止误操作 → ⚠️ **当前未实现二次确认**

### 3.2 任务卡片交互（PRD 第 3.2 章）
- 任务卡片显示：任务名称、简要描述、启用状态开关、最近执行时间
- 快速启停、进入编辑、右上角创建新任务
- ⚠️ **当前未实现任务列表（M1 模块未开始）**

### 3.3 添加步骤弹窗设计（PRD 第 4.1 章）
- 底部弹窗，3 列网格布局
- 每种类型有彩色图标（不同色系增强辨识度）
- 支持上滑关闭和点击遮罩关闭
- 步骤类型数量较多时支持纵向滚动
- 可按分类标签筛选步骤类型（badge "建议"）
- ⚠️ **当前 StepTypePicker 5 分类网格 + 彩色背景**，但未实现"分类标签筛选"

### 3.4 触发器配置区（PRD 第 6 章）
- 标签页切换设计（4 个 tab 横向排列，选中项高亮）
- 4 种模式：定时 / 间隔 / 随机间隔 / 手动
- 任务级"屏幕常亮"开关
- ⚠️ **当前仅 StepCardData 加了字段，UI 未实现**

### 3.5 统计页面（PRD 第 8 章）
- 顶部三栏卡片：总执行次数、成功率、活跃任务数
- 7 天柱状图趋势（当日高亮）
- Top 5 排行榜（带进度条）
- ⚠️ **M4 未实现**

### 3.6 底部导航（PRD 第 12.2 章）
- 三栏式：任务 / 日志 / 统计
- 选中项主色高亮，未选中项灰色
- ⚠️ **当前无底部导航**（M1 时引入）

---

## 四、与"图片一二三"对照

> 用户提到"参考仓库里面的图片一二三"，但仓库内**未找到**独立的图片文件。
> 推测："图片一二三"指用户最初向 PRD 生成器描述需求时附带的 3 张设计图，PRD 中以 "图片识别" / "图片补充功能" 标签标记（共 10 处）：
> - 3.2 任务列表（图片识别"执行子任务 · 任务ID: 2"）
> - 5.1 打开链接（图片识别）
> - 5.3 屏幕常亮开/关（图片识别 ×2）
> - 5.4 设备振动（图片识别）
> - 5.5 发送通知 / 弹出提醒 / 延时等待 / 屏幕内容识别 / 执行子任务（图片识别 ×5）

**结论**：图片已在 PRD 文本中"消化"，但**用户可能仍持有原始图片**，可在 Q 阶段向用户确认是否提供。

---

## 五、改进建议（需用户决策）

### 5.1 立即可做（小改动，大提升）
1. **添加步骤按钮改胶囊状**：当前是 IconButton，PRD 是 `+ 添加步骤` 胶囊按钮 → 更明显
2. **删除二次确认**：StepCard 删除按钮点击后弹 AlertDialog "确认删除？"
3. **section-title 分组标题**：在步骤列表上方加"执行步骤"标题
4. **step-actions 图标尺寸**：从 18px 降到 14px（与 PRD 一致）

### 5.2 M1 阶段引入
1. **底部导航 NavigationBar**：3 栏 任务/日志/统计
2. **任务列表卡片**：与 StepCard 风格统一
3. **任务卡片显示子任务嵌套调用**（PRD 3.2 图片补充功能）

### 5.3 M3 阶段引入
1. **触发器标签页 UI**：定时/间隔/随机/手动
2. **任务级"屏幕常亮"开关**

### 5.4 可选优化（PRD 未明示但提升质感）
1. **callout 提示框组件**：accent-light 背景 + 4px 左边框，用于"提示/警告"信息
2. **toggle-row 设置行组件**：当前设置页用 Dropdown/Switch 散列，可统一封装

---

## 六、总结

1. **当前 step_recorder UI 已与 HTML PRD 的"步骤卡片"风格基本对齐**（F8 完成后）。
2. **缺失的是大模块**（任务管理 M1 / 触发器 M3 / 统计 M4 / 日志 M5），按 tasks.md 顺序推进即可。
3. **小细节差距**（5.1 列表）可在本轮改动中一并修复。
4. **图片一二三在仓库中不存在**，需要向用户确认是否提供或是否仍需要参考。
5. **PRD 中的"图片识别"标签**仅表示这些步骤类型来自图片补充，并非缺失资源。

---

## 七、维护约定
- 每次新模块完成后，对照本文更新"已实现"清单
- 新发现的差距追加到第五节"改进建议"
- 与 `scope.md` 和 `unsupported_features.md` 互参
