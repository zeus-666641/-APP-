# 任务清单 · step_recorder 0.1.0

> 移动App工厂 · 项目2 / 流程2.3 · 输出
> 顺序：UI-first（M2 → M1 → M0 → M3-M6）
> 每个任务 <4h，拓扑排序

## 模块划分

| 模块 | 内容 | 顺序 |
|---|---|---|
| **M2** | 步骤编辑器 UI（mock 数据） | 1 |
| **M1** | 任务管理 UI（含父子嵌套） | 2 |
| **M0** | 数据模型 + 存储（重构 mock 为真实存储） | 3 |
| **M3** | 触发器系统 | 4 |
| **M4** | 统计模块 | 5 |
| **M5** | 执行日志模块 | 6 |
| **M6** | 系统设置 + 启动引导 | 7 |
| **M7** | 执行引擎 + 集成测试 | 8 |
| **M8** | 打包 APK | 9 |

## 任务表

### M2 步骤编辑器 UI（先做，mock 数据）

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T2.1 | 项目骨架生成 | scaffold | 0.5h | — | apps/step_recorder/ 创建 + uv sync |
| T2.2 | StepType 枚举定义 | models | 0.5h | T2.1 | 30+ 类型 + 状态标记（✅/⚠️/❌） |
| T2.3 | step_card 组件（卡片+图标+名称+角标+开关+删除） | views/components | 1.5h | T2.2 | 卡片样式正确，状态角标显示 |
| T2.4 | step_type_picker 组件（5分类网格+置灰+点击提示） | views/components | 2h | T2.2 | 30+ 类型网格展示，未实现项置灰 |
| T2.5 | not_implemented_dialog 组件 | views/components | 0.5h | T2.4 | 弹窗 + 保存占位/取消按钮 |
| T2.6 | param_editor 组件（按 type 动态表单） | views/components | 2.5h | T2.2 | 至少 5 种典型 type 表单正确 |
| T2.7 | step_editor_view 主视图（列表+添加+拖拽排序） | views | 3h | T2.3, T2.4, T2.6 | 列表展示 + 添加弹窗 + 拖拽生效 |
| T2.8 | draggable_list 通用组件 | views/components | 1.5h | — | 长按拖拽 + 上下箭头双模式 |
| T2.9 | M2 mock 数据与单元测试 | tests | 1h | T2.7 | mock 数据 5+ 步骤，UI 渲染正确 |

**M2 合计：13h**

### M1 任务管理 UI

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T1.1 | task_tree 组件（树形列表+缩进+折叠） | views/components | 2h | T2.8 | 至少 3 层嵌套展示 |
| T1.2 | home_view 主视图（任务列表+分组+底部导航） | views | 2.5h | T1.1 | 4 tab 导航 + 任务列表 |
| T1.3 | task_edit_view（编辑表单+父子选择+图标选择） | views | 2h | T1.2 | 表单提交正确 |
| T1.4 | M1 mock 数据与单元测试 | tests | 1h | T1.3 | mock 数据 5+ 任务含嵌套 |

**M1 合计：7.5h**

### M0 数据模型 + 存储（重构）

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T0.1 | 6 个 pydantic 模型实现 | models | 2h | T2.2 | 全部字段+验证+单测 |
| T0.2 | storage_service（JSON 读写+锁） | services | 1.5h | T0.1 | 并发读写安全 + 单测 |
| T0.3 | task_service（CRUD+父子关系） | services | 2.5h | T0.2 | 增删改查 + 关系操作 + 单测 |
| T0.4 | step_service（CRUD+排序） | services | 2h | T0.2 | 增删改查 + 拖拽重排 + 单测 |
| T0.5 | relation_service（关系表操作） | services | 1.5h | T0.2 | parent/child 操作 + 单测 |
| T0.6 | M0 集成 M2/M1，移除 mock | 全栈 | 2h | T0.3, T0.4, T0.5 | UI 接真实数据 |

**M0 合计：11.5h**

### M3 触发器系统

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T3.1 | trigger 模型 + trigger_service | services | 2h | T0.5 | 4 种触发器 + 单测 |
| T3.2 | 启动引导组件 | views/components | 1h | — | 首次启动弹引导 |
| T3.3 | trigger_editor_view | views | 2h | T3.1 | 4 种触发器配置 UI |
| T3.4 | 前台定时执行（asyncio） | services | 2h | T3.1 | 前台定时触发 + 单测 |

**M3 合计：7h**

### M4 统计模块

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T4.1 | stats_service（按任务/天/触发源） | services | 2h | T0.2 | 3 维统计 + 单测 |
| T4.2 | stats_view（图表+排行） | views | 2.5h | T4.1 | ECharts 风格图表 |

**M4 合计：4.5h**

### M5 执行日志

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T5.1 | log 模型 + log_service | services | 1.5h | T0.2 | 日志读写 + 单测 |
| T5.2 | logs_view（列表+详情+步骤展开） | views | 2h | T5.1 | 日志列表 + 步骤展开 |

**M5 合计：3.5h**

### M6 系统设置

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T6.1 | settings_view（深色/字号/执行参数/关于） | views | 2h | — | 设置项生效 |

**M6 合计：2h**

### M7 执行引擎 + 集成测试

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T7.1 | executor_service（步骤调度+失败处理+占位跳过） | services | 3h | T0.4, T3.1 | 6 种可执行 type 正确执行 |
| T7.2 | 集成测试 E2E | tests | 2h | T7.1 | 主流程跑通 |
| T7.3 | 性能优化 | 全栈 | 1.5h | T7.2 | 启动 <3s |

**M7 合计：6.5h**

### M8 打包

| ID | 任务 | 模块 | 预估 | 前置 | 验收 |
|---|---|---|---|---|---|
| T8.1 | flet build apk | flet | 1h | T7.3 | releases/step_recorder_0.1.0.apk |

**M8 合计：1h**

## 工时汇总

- M2 步骤编辑器：13h
- M1 任务管理：7.5h
- M0 数据模型：11.5h
- M3 触发器：7h
- M4 统计：4.5h
- M5 日志：3.5h
- M6 设置：2h
- M7 执行引擎：6.5h
- M8 打包：1h
- **合计：56h**（约 14 个工作日）

## 里程碑

| 里程碑 | 任务集 | 验证 |
|---|---|---|
| **Milestone 1**：M2 完成 | T2.1-T2.9 | 步骤编辑器 UI 可用 |
| **Milestone 2**：M2+M1 完成 | + T1.1-T1.4 | 任务+步骤 UI 联通 |
| **Milestone 3**：M0 完成 | + T0.1-T0.6 | UI 接真实数据 |
| **Milestone 4**：M3-M6 完成 | + T3-T6 | 全功能可用 |
| **Milestone 5**：M7+M8 完成 | + T7-T8 | APK 发布 |
