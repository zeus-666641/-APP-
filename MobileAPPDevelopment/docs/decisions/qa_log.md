# 问答决策日志

> 移动App工厂 · 所有 AskUserQuestion 提问归档（含未选中选项）
> 用途：方便日后修改决策时回溯当时所有可选项
> 格式：时间 → 问题 → 全部选项（含未选中）→ 用户选择

---

## 2026-07-20

### Q1. App 方向（项目1.1 调研焦点）
- **问题**：第一个 App 期望在哪个方向？
- **选项**：
  1. 效率/工具类（待办/清单/习惯打卡/番茄钟）
  2. 学习/阅读类（单词/古诗/抽认卡/错题本）
  3. 生活/健康类（记账/节水节电/运动打卡/冥想）
  4. 娱乐/小游戏类（2048/翻牌配对/井字棋）
- **用户选择**：跳过（不预设方向，1.3 立项时由用户拍板）
- **结果**：1.1 调研覆盖 4 大方向，1.3 选方案 A 习惯追踪

### Q2. habit_zh 首App 选型
- **问题**：首个 App 选哪个方案？
- **选项**：
  1. A 优化型：中文版 Loop + 修 6 项痛点
  2. B 细分型：晨晚仪式习惯追踪
  3. C 创新型：锚点-行为习惯链
- **用户选择**：A 优化型·习惯追踪
- **状态**：项目1+2 完成（docs/prd/habit_zh_prd.md），后因用户切换到 step_recorder 暂停

### Q3. GitHub PAT 处理
- **问题**：你新建的「移动APP开发」仓库现在在哪？
- **选项**：
  1. 改为公开仓库
  2. 提供 PAT 鉴权 URL
  3. 告诉我准确仓库名
  4. 还没推到 GitHub
- **用户选择**：跳过（用户在 Trae Work 上传了 step-recorder 分支代替回答）
- **状态**：自动发现 step-recorder 分支

### Q4. 步骤记录器方向（关键决策）
- **问题**：步骤记录器 PRD 与 Flet 栈不兼容。怎么走？
- **选项**：
  1. 仅实现 Flet 能做的子集
  2. 改栈为 Kotlin+Android Studio
  3. 暂停 步骤记录器，继续 habit_zh
  4. 减范围到最小 MVP
- **用户选择**：选 1，但要给出不能实现的内容
- **补充**：「不贪快可以一步步来。可以分模块，一块块实现。最重要的是质量。不要少了提问。尽最大的可能还原功能。」

### Q5. 不可做项处理方式
- **问题**：「不可做项」（如系统控制 14 项、跨应用模拟点击、悬浮窗、屏幕 OCR 等）怎么处理？
- **选项**：
  1. 预留接口 + 置灰显示
  2. 完全删除
  3. 可建可存执行跳过
  4. 逐项变通实现
- **用户选择**：选 1
- **补充**：用户点击的话就显示「尚未完成」

### Q6. 分模块起始
- **问题**：分模块实现从哪里开始？
- **选项**：
  1. 任务管理 (M1)
  2. 数据模型+存储 (M0)
  3. 步骤编辑器 (M2)
- **用户选择**：顺序为「第三个第一个第二个」即 M2→M1→M0

### Q7. 后台触发处理
- **问题**：PRD 第 6 章触发器中定时/间隔/随机模式必须后台运行，Flet 做不到。怎么处理？
- **选项**：
  1. 仅前台定时
  2. 前台可用 + 后台尽量
  3. MVP 不做后台触发
- **用户选择**：选 2
- **补充**：启动的时候提示用户打开后台运行白名单和电池优化不限制

### Q8. 分模块顺序确认
- **问题**：分模块顺序确认一下？
- **选项**：
  1. M2→M1→M0 (UI-first)
  2. M0→M1→M2 (Data-first)
  3. M1 为主 (合并起步)
- **用户选择**：M2→M1→M0 (UI-first)

### Q9. 父子任务存储设计
- **问题**：父子任务的数据存储怎么设计？
- **选项**：
  1. 单表 parent_id 自关联
  2. 独立关系表
  3. JSON 数组嵌套
- **用户选择**：独立关系表

### Q10. App 项目名
- **问题**：App 项目名？
- **选项**：
  1. step_recorder (英文蛇形)
  2. sr (缩写)
  3. step_record
  4. bufuzou (中文拼音)
- **用户选择**：step_recorder (英文蛇形)

### Q11. step_card 卡片设计
- **问题**：step_card (步骤卡片) 怎么设计？
- **选项**：
  1. PRD 原样样式（序号圆圈 + 步骤名/参数 + 状态开关/删除）
  2. 图标+状态点+下拉菜单
  3. 可展开折叠卡片
- **用户选择**：PRD 原样样式

### Q12. step_type_picker 设计
- **问题**：step_type_picker (步骤类型选择面板) 怎么设计？
- **选项**：
  1. 5 分类标签页 + 网格
  2. 单页滚动列表
  3. 搜索 + accordion
- **用户选择**：选 1，但也要包括搜索框

### Q13. 占位步骤 UI 表现
- **问题**：用户选「保存为占位」后该步骤的 UI 表现？
- **选项**：
  1. 徽章标记不可用
  2. 可修改参数不可执行
  3. 完全不区分
- **用户选择**：可修改参数不可执行

---

## 后续待记录

### Q14. 不可做项在 picker 中的点击行为
- **选项**：
  1. 完全禁用不可点
  2. 可点弹提示对话框
  3. 点击展开提示文字
- **用户选择**：第三种 + 自动保存占位（点击展开"尚未完成"提示，同时直接创建占位步骤，无需二次确认）
- **影响**：T2.5 not_implemented_dialog 简化为 SnackBar 通知，节省 0.5h

### Q15. 网格密度
- **选项**：4 列 / 3 列 / 2 列
- **用户选择**：4 列

### Q16. 搜索范围
- **选项**：
  1. 仅搜当前分类
  2. 全局搜 + 分类分段
  3. 全局搜 + 隐藏标签页
- **用户选择**：全局搜 + 分类分段（搜索结果按分类分段展示，每段一个分类标题 + 该分类匹配项网格）

---

## 2026-07-20 续（M2-T2.6 param_editor 设计）

### Q17. params_schema 升级方案
- **问题**：`params_schema: dict[str,str]` 只有字段名+类型描述，不能直接生成表单。怎么升级到结构化字段？
- **选项**：
  1. 新增 fields 字段（StepTypeMeta 加 `fields: list[ParamField]`，向后兼容，旧 params_schema 保留为提示文本）
  2. 原地升级 params_schema（dict → list，重写 41 个类型的元数据，所有已有测试需更新）
  3. 新建独立 param_schema 模块（不动 StepTypeMeta）
- **用户选择**：选 1 新增 fields 字段
- **影响**：StepTypeMeta 加 `fields` 字段默认空列表，旧 `params_schema` 不删；新组件 `param_editor` 优先读 `fields`

### Q18. NOT_IMPLEMENTED 类型参数表单
- **问题**：占位步骤的参数表单怎么处理？Q14 已定「自动保存占位」。
- **选项**：
  1. 允许填参数+保存为占位（用户可预先规划）
  2. 显示但只读禁用
  3. 不显示参数表单
- **用户选择**：选 1 允许填参数+保存为占位
- **影响**：param_editor 对所有 StepType（含 NOT_IMPLEMENTED）都渲染表单，占位标记在 StepCard 层面体现

### Q19. 字段控件类型策略
- **问题**：每个参数字段渲染成什么输入控件？
- **选项**：
  1. 按字段类型自动选控件（bool→Switch、enum→Dropdown、int_range→Slider、其他→TextField）
  2. 统一 TextField（所有字段都输字符串）
  3. 混合策略（默认 TextField，bool→Switch，有限选项→Dropdown）
- **用户选择**：选 1 按字段类型自动选控件
- **影响**：FieldType 枚举：BOOL / INT / INT_RANGE / STRING / TEXTAREA / ENUM / COORDINATE；ParamEditor 按类型分发渲染

### Q20. 未保存离开策略
- **问题**：用户改了参数但没点保存就返回，怎么处理？
- **选项**：
  1. 提示保存对话框（保存并退出/不保存退出/继续编辑）
  2. 自动保存草稿（无打扰）
  3. 直接丢弃
- **用户选择**：选 1 提示保存对话框
- **影响**：T2.7 step_editor_view 返回时检测 dirty 状态，弹 AlertDialog 让用户三选一；param_editor 暴露 `is_dirty()` + `get_values()` 方法供 view 层调用

---

## 2026-07-20 续2（M2-T2.7 step_editor_view 设计）

### Q21. 步骤编辑模式展开方式
- **问题**：点击 StepCard 或 + 按钮编辑步骤时，以什么方式展开编辑界面？
- **选项**：
  1. 抽屉式侧滑（从右滑出宽度 80%，含 StepTypePicker + ParamEditor）
  2. 全屏对话框
  3. 独立全屏页
  4. BottomSheet
- **用户选择**：选 1 抽屉式侧滑
- **影响**：用 ft.PageOverlay 或自定义 ft.Container + transform animation 实现抽屉；编辑时不遮挡步骤列表（用户能看到上下文）

### Q22. 添加步骤入口
- **问题**：添加步骤的入口位置？
- **选项**：
  1. 右下角 FAB（FloatingActionButton，符合手机习惯）
  2. 顶部按钮（PRD HTML 原始设计）
  3. 双入口（FAB 默认 + 顶部按钮，都启动添加流程）
- **用户选择**：选 3 双入口（默认 FAB，但顶部按钮也要实现）
- **影响**：step_editor_view 同时渲染 FAB 和顶部"添加步骤"按钮，二者调用同一个 add_step_handler；未来可在设置中切换默认

### Q23. T2.7 首跑数据源
- **问题**：M0 数据模型未实现，T2.7 首跑时数据从哪里来？
- **选项**：
  1. mock 3-5 条示例步骤（hardcode 在 view 内部，覆盖 AVAILABLE/LIMITED/NOT_IMPLEMENTED 三种状态）
  2. 空状态 + 引导文案
  3. 直接调用 services/storage.py（未实现，会报错）
- **用户选择**：选 1 mock 3-5 条示例步骤
- **影响**：step_editor_view 内置 `_default_mock_steps()` 返回 list[StepCardData]，覆盖 OPEN_URL/DELAY/DARK_MODE/BLUETOOTH(VISIBLE_NOT_IMPL)/CLICK 等代表性类型

---

## 2026-07-20 续3（M2-T2.8 draggable_list 设计）

### Q24. 拖拽实现方式
- **问题**：T2.8 draggable_list 的拖拽实现选哪个？
- **选项**：
  1. 仅 ↑/↓ 按钮（无拖拽，最稳，但与 PRD「拖拽」语义有偏差）
  2. 仅 Draggable+DragTarget 真拖拽（无按钮，符合 PRD，但触屏体验不一定好）
  3. 拖拽 + ↑/↓ 按钮双保险（按钮可通过设置开关显示/隐藏）
  4. LongPressDraggable（长按拖动，更接近原生 ReorderableListView）
- **用户选择**：选 3 拖拽 + ↑/↓ 按钮，按钮开关可设置
- **影响**：DraggableList 组件同时实现 Draggable+DragTarget 与 ↑/↓ 按钮；构造参数 `show_reorder_buttons: bool = True`；未来在设置中切换

### Q25. 子任务嵌套拖拽
- **问题**：T2.8 是否含子任务嵌套拖拽？（RUN_SUBTASK 类型可能展开子步骤）
- **选项**：
  1. 支持嵌套（子步骤可拖入父步骤，可视化层级）
  2. 仅同级排序，不主动提示嵌套（但内部保留嵌套能力）
  3. 完全禁止嵌套（删除子任务概念）
- **用户选择**：选 2 仅同级排序，不主动提示嵌套
- **影响**：DraggableList 的 `on_reorder(old_index, new_index)` 仅处理同级；不暴露嵌套 UI；数据层为未来嵌套留接口（step.parent_id 字段保留但不渲染）

### Q26-Q29. 拖拽视觉/交互细节（用户正式答复）
- **Q26 拖拽触发区**：选「专属拖拽手柄」，但**默认在右侧**（不是左侧），并支持设置切换左/右
  - 影响：构造参数 `drag_handle_side: Literal["left", "right"] = "right"`，未来在 settings 中可切换
- **Q27 拖动时原位置反馈**：选「半透明灰色占位」
  - 影响：`content_when_dragging` 用 opacity=0.3 + bgcolor="#f1f5f9" 的同形占位
- **Q28 ↑/↓ 按钮的开关默认值与位置**：用户提出全新设计
  - "上下箭头集成了一个按钮"：合并为单个"换位"按钮（图标 `SWAP_VERT`）
  - "点击按钮的时候显示输入框"：点击后弹 AlertDialog 含 TextField
  - "输入要调换的行数"：用户输入目标行号（1-based）
  - "并可一键调换"：对话框内有"一键调换"按钮
  - "上下箭头按钮和拖拽按钮可以同时出现"：换位按钮 + 拖拽手柄 可并存
  - "设置里面可以调整开关任意一个按钮"：两个按钮可独立开关
  - 影响：
    - 构造参数 `show_drag_handle: bool = True` + `show_swap_button: bool = True`（两者独立）
    - 点击换位按钮 → 弹 AlertDialog(TextField + 一键调换按钮)
    - 输入目标行号 → 移动到该位置（移动语义，非交换）
- **Q29 拖到边界（输入行号超范围）**：
  - "先按上一问的回答来做"：先用 Q28 的换位对话框处理
  - "当输入行数超出范围，例如超出最后一行就提示是否移动到最后一行"：target > total → 二级确认"是否移动到最后一行？"
  - "小于一行就提示是否移动到第 1 行"：target < 1 → 二级确认"是否移动到第 1 行？"
  - 影响：`_show_boundary_confirm(current_index, boundary_index, reason, label)` 弹二级 AlertDialog
- **综合影响**：
  - DraggableList 每行结构 = `DragTarget(content=Container(Row[handle?, Draggable(content=item), handle?, swap_btn?]))`
  - `max_simultaneous_drags=1`（避免多指拖拽混乱）
  - `on_accept` 通过 `e.src.data`（key）反查 src_index，调用 `_reorder(old, new)`
  - 换位按钮点击 → `_handle_swap_click(current_index)` → 弹输入对话框 → 校验 → 移动 or 二级确认

---

## 2026-07-20 续4（D1 后续 4 项小改动 F9a-d）

### Q30. 添加步骤按钮样式（F9a）
- **问题**：当前 AppBar 添加步骤按钮是 IconButton，PRD `.add-btn` 是胶囊状 accent 背景 + 白字。怎么改？
- **选项**：
  1. 改为 `ft.Button` + accent 背景 + 白字（与 PRD 一致）
  2. 保持 IconButton（图标按钮）
  3. FAB 改胶囊状
- **用户选择**：选 1 改为 `ft.Button` + accent 背景 + 白字
- **影响**：step_editor_view.py `_build_main_content` 中 AppBar actions 改用 `ft.Button("添加步骤", icon=ft.Icons.ADD, bgcolor="#2563eb", color="white")`

### Q31. StepCard 删除按钮二次确认（F9b）
- **问题**：当前 StepCard 删除按钮直接删除，PRD 第 4 章明确要求"删除需二次确认"。怎么实现？
- **选项**：
  1. modal AlertDialog（标题 + 步骤名 + 取消/确认删除两个按钮，确认按钮红色）
  2. SnackBar 倒计时撤销
  3. 长按删除（短按不触发）
- **用户选择**：选 1 modal AlertDialog
- **影响**：step_card.py `_handle_delete` 改为：先弹 `ft.AlertDialog(modal=True, content=Text("确定要删除步骤「X」吗？此操作不可撤销。"), actions=[取消, 确认删除(红色)])`，确认后才调用 `self._on_delete(step_id)`

### Q32. 步骤列表上方 section-title（F9c）
- **问题**：PRD `.section-title` 在列表上方有分组标题（左标题右统计）。怎么加？
- **选项**：
  1. 加 `ft.Row([Text("执行步骤", 14px W_600), Text("共 N 项", 12px 灰)], SPACE_BETWEEN)
  2. 仅加标题 "执行步骤"
  3. 加分类筛选 dropdown
- **用户选择**：选 1 加 Row 标题 + 计数
- **影响**：step_editor_view.py `_build_main_content` 在步骤列表上方加 `self._section_title`；`_refresh_step_list` 同步更新计数 `f"共 {len(self._steps)} 项"`

### Q33. step-actions 图标尺寸（F9d）
- **问题**：PRD `.step-actions` 图标 14px，当前 StepCard 操作图标 18px（delete/expand/add_child）和 22px（execute）。怎么统一？
- **选项**：
  1. 仅调 18→14，execute 保留 22 作为主 CTA
  2. 全部调到 14（包括 execute），视觉一致但 execute 视觉权重降低
  3. 全部调到 18（中等档）
- **用户选择（初次）**：选 1 仅调 18→14
- **用户选择（追问后改）**：改为选 2 全部 14px
- **影响**：step_card.py 中 `delete_btn`、`expand_btn`、`add_child_btn`、`execute_btn` 的 `icon_size` 全部统一为 14

### Q34. 文件超限处理（CHK10）
- **问题**：step_card.py（565 行）和 step_editor_view.py（748 行）都超 500 行（ORG2）。pre-existing 状态，非 F9 引入。如何处理？
- **选项**：
  1. 延后到 M1 后统一拆分
  2. 现在就拆
  3. 保持现状
- **用户选择**：选 3 保持现状
- **影响**：记录到 项目记忆.md 的"M2.5 待重构候选"，不立即拆分

### Q35. M2.5 延后设置项排期（需求4）
- **问题**：息屏执行 / 语言切换 / 权限管理入口 何时实现？
- **选项**：
  1. M1 完成后
  2. M0 完成后（M6 设置模块）
  3. M7 执行引擎后
- **用户选择**：选 3 M7 执行引擎后
- **影响**：项目记忆.md 标记 M2.5 延后项归 M7 后处理；息屏执行依赖执行引擎，权限入口需要 U1+U2 落地后再开 UI

---

## 2026-07-20 续5（M1 模块设计 4 个关键决策）

### Q37. M1 默认路由（覆盖需求6）
- **问题**：M1 加入底部导航后，默认路由怎么调？当前是 /step_editor。注意需求6 要求"一进入就是步骤界面"。
- **选项**：
  1. /tasks 任务列表（默认路由改为任务列表，点任务进步骤编辑器）
  2. 保持 /step_editor
  3. /tasks + push 到 step_editor
- **用户选择**：选 1 /tasks 任务列表
- **影响**：
  - **需求6 部分作废**：原"一进入就是步骤界面"调整为"一进入就是任务列表"
  - routes.py 默认路由从 `/step_editor` 改为 `/tasks`
  - 理由：M1 引入底部导航后，任务列表是更高层级的入口（PRD 主次顺序）

### Q38. task_card 设计
- **问题**：task_card（任务卡片）怎么设计？
- **选项**：
  1. PRD 原样：任务名 + 图标 + 状态点 + 启用开关 + 执行按钮，可展开子任务
  2. 参考 StepCard 设计语言（序号圆圈 + 图标块 + 参数摘要 + actions）
  3. 简化卡片：仅任务名 + 启用开关 + 执行按钮，点击进详情
- **用户选择**：选 1 PRD 原样
- **影响**：task_card.py 实现 PRD 原样样式，不参考 StepCard

### Q39. 父子嵌套交互（覆盖 Q25）
- **问题**：父子任务的嵌套交互怎么设计？Q25 已定"仅同级排序，不主动提示嵌套"。
- **选项**：
  1. 树形展开 + 缩进
  2. 面包屑导航
  3. 仅同级 + 编辑选择
- **用户选择**：前两个都实现，设置可以切换，默认为第一个
- **影响**：
  - task_tree 组件同时实现"树形展开"和"面包屑"两种模式
  - 构造参数 `nest_mode: Literal["tree", "breadcrumb"] = "tree"`
  - 设置中加切换项 `task_nest_mode`（默认 "tree"）
  - Q25 的"仅同级排序"仍生效（拖拽排序仅同级）

### Q40. 未完成 tab 处理
- **问题**：PRD 要求 4 tab（任务/步骤/统计/设置），但 M4 统计和 M5 日志未做。怎么处理？
- **选项**：
  1. 现在仅 2 tab
  2. 4 tab + 占位
  3. 4 tab + 隐藏不可点
- **用户选择**：先完成 2 和 4，再完成 4 和 5，本次对话内完成
- **解读**：
  - M1 阶段先做 4 tab 框架，统计/日志 tab 先占位
  - M1 完成后立刻进入 M4 统计 + M5 日志模块
  - 本次对话内完成 M1 + M4 + M5
- **影响**：
  - M1 工作量增加：home_view 需要 4 tab 框架 + 2 个占位页
  - M4 + M5 在本次对话内完成（挑战性目标）

### Q41. 本次对话范围确认
- **问题**：本次对话目标范围？
- **用户选择**：M1（任务管理）+ M4（统计）+ M5（日志）
- **影响**：本次对话工时约 15.5h（M1=7.5h + M4=4.5h + M5=3.5h），需分模块逐项推进

### Q42. M5 日志详情展示方式
- **问题**：M5 执行日志的详情展示方式选哪种？
- **选项**：
  1. 侧滑抽屉（与 TaskEditDrawer 一致风格）
  2. 独立路由页 /logs/{id}，全屏展示详情
  3. 卡片原地展开（accordion 风格）
- **用户选择**：独立路由页

### Q43. M5 日志详情步骤列表展示
- **问题**：日志详情中如何展示该次执行的步骤列表？
- **选项**：
  1. 时间轴列表（每步：序号+图标+名称+状态点+耗时，简洁紧凑）
  2. 卡片列表（类似 StepCard 样式）
  3. 树形结构（Tree 控件，支持折叠/展开）
- **用户选择**：时间轴列表

### Q44. M5 日志列表过滤维度
- **问题**：日志列表需要支持哪些过滤维度？
- **选项**（多选）：
  1. 按状态过滤（成功/失败/中止）
  2. 按任务过滤
  3. 按触发源过滤
  4. 按时间范围（最近 1/7/30 天）
- **用户选择**：全部 4 项

### Q45. M5 日志数据保留和清理策略
- **问题**：日志数据保留和清理策略怎么处理？
- **选项**：
  1. 本次不实现清理（M5 阶段先用 mock，M7 接入后再加自动清理）
  2. 设置项清理（在设置页加"保留最近 N 条"开关）
  3. 自动清理（M5 阶段就实现自动清理，如保留 30 天）
- **用户选择**：设置项清理，更新待办和任务清单，清理可开关自动清理

### Q46. M5 日志列表项展示字段
- **问题**：日志列表中每个卡片项展示哪些字段？
- **选项**（多选）：
  1. 任务名+状态（必选）
  2. 触发源
  3. 开始时间（相对）
  4. 耗时
- **用户选择**：全部 4 项

### Q47. M5 日志列表分组方式
- **问题**：日志列表是否按日期分组展示？
- **选项**：
  1. 按日期分组（同一天内合并为一组）
  2. 平铺列表（按时间倒序，不分组）
  3. 两种均可切换
- **用户选择**：两种均可切换（默认按日期分组）

### Q48. M5 日志自动清理设置项位置
- **问题**：日志自动清理设置项放哪里，默认状态和保留策略？
- **选项**：
  1. 设置页独立"日志管理"区域，默认关闭，开关打开后默认保留最近 500 条
  2. 设置页独立"日志管理"区域，默认开启，默认保留 30 天
  3. 合入"执行设置"区域，默认关闭，保留条数可选（100/500/1000）
- **用户选择**：选项 1（独立"日志管理"区域 + 默认关闭），但保留条数改为用户输入（1-9999）

### Q49. M5 额外功能
- **问题**：M5 需要哪些额外功能？
- **选项**（多选）：
  1. 搜索（按任务名/日志ID）
  2. 单条删除（卡片右上角按钮）
  3. 分页加载（每页 20 条）
  4. 都不要
- **用户选择**：搜索 + 单条删除（删除按钮放在卡片左下角）；列表页不分页

---

## 2026-07-20 续6（M5 完成后 Bug 修复 + 需求调整）

### Q50. tab 结构调整（覆盖 Q40）
- **问题**：M5 完成后用户预览反馈 15 个问题，其中需求 9+12+13 要求去掉步骤 tab、设置常驻 AppBar、日志 tab 与任务/统计同级。怎么调？
- **选项**：
  1. 3 tab（任务/统计/日志）+ AppBar 设置（步骤 tab 去掉，设置常驻 AppBar leading）
  2. 4 tab（任务/统计/日志/设置）保持原结构
  3. 2 tab（任务/日志）+ 设置 AppBar（去掉统计 tab，统计通过任务卡片入口）
- **用户选择**：选 1 3 tab + AppBar 设置
- **影响**：
  - home_view 重写：3 tab（任务/统计/日志），AppBar leading=设置按钮，actions=添加任务
  - 步骤 tab 去掉（步骤编辑器从任务卡片进入，原有路由 /step_editor 保留）
  - 统计/日志 tab 点击直接 `page.go("/stats")` / `page.go("/logs")` 跳路由
  - routes.py 调整：所有路由栈底保留 HomeView（点返回回任务列表）
  - Q40 的 4 tab 决策作废

### Q51. UI 设计文件形式（需求 15）
- **问题**：需求 15 要求"分析软件 UI 生成 UI 设计文件"，采用哪种形式？
- **选项**：
  1. 仅 Markdown 设计规范（颜色/字号/间距/组件清单 + 文字描述）
  2. 仅 HTML 原型（可在浏览器查看的高保真原型，含配色和布局）
  3. 两者结合：Markdown 规范（开发者读）+ HTML 原型（设计审阅）
- **用户选择**：第二再加上第一（HTML 原型 + Markdown 规范）
- **影响**：
  - 产出 `docs/ui_design/step_recorder_ui.html`（HTML 原型，含所有页面/状态）
  - 产出 `docs/ui_design/ui_design_spec.md`（设计规范文档）
  - HTML 原型复用 PRD HTML 的 :root CSS 变量，保证视觉一致性

### Q52. 抽屉关闭交互（Bug 2 修复方案）
- **问题**：Bug 2 抽屉关闭后黑屏，怎么修？
- **选项**：
  1. 仅点击遮罩关闭（取消按钮改为不可点，只支持点遮罩）
  2. 点击遮罩 + 取消按钮双关闭（两种方式都支持，更友好）
  3. 仅取消按钮关闭（保持原样，修黑屏根因）
- **用户选择**：选 2 点击遮罩 + 取消按钮双关闭
- **影响**：
  - `_handle_overlay_click`：判断 `e.control == self._overlay` 才关闭（避免点到抽屉内部也关）
  - `_handle_close_drawer`：清除 `self._overlay.content = None` 引用，避免下次 update 时引用失效的控件导致黑屏
  - `e.stop_propagation = True` 阻止抽屉内部按钮事件冒泡到遮罩

### Q53. UI 设计集成到工作流（需求 15）
- **问题**：需求 15 要求"把 UI 设计这一步集成到工作流中（记忆/规则/骨架之类的所有）"，集成到哪些文件？
- **选项**：
  1. 仅骨架.md（在 7 大项目中新增"UI 设计"流程）
  2. 骨架.md + 编码习惯.md（增加 UI 一致性检查项）
  3. 骨架.md + 编码习惯.md + 规则.md（三者全部补充，硬性要求）
- **用户选择**：选 3 三者全部补充
- **影响**：
  - 骨架.md：在项目 4 核心编码前新增"项目 3.5：UI 设计"，产出 HTML 原型 + Markdown 规范
  - 编码习惯.md：新增 CHK24（UI 一致性自检）和 F6（设计文件复用）
  - 规则.md：新增 R19（UI 设计文件为开发前置）和 R20（视觉一致性硬约束）

### Bug 修复批次（Q50 决策后执行）

| Bug # | 描述 | 根因 | 修复 |
|---|---|---|---|
| 1 | 点击统计报 `Dropdown.__init__() got an unexpected keyword argument 'on_change'` | Flet 0.86.1 把 `Dropdown.on_change` 改为 `on_select` | `settings_view.py` 4 处 Dropdown 改 `on_select` |
| 2 | 添加任务后白屏 + 返回黑屏 | 抽屉关闭后 `_overlay.content` 仍引用旧控件，`page.update()` 时引用失效 | 关闭时清 `_overlay.content = None` + 加遮罩点击关闭 |
| 3 | `ERR_BLOCKED_BY_RESPONSE.NotSameOriginAfterDefaultedToSameOriginByCoep` | Flet 默认 `COEP: require-corp` 阻塞 TRAE 预览器外部脚本 | `main.py` 用 `export_asgi_app=True` + 外层中间件覆盖 COEP 为 `credentialless` |
| 4 | 折叠子任务 `'NoneType' object has no attribute 'task_id'` | `TaskCard.data` 与 `ft.Control.data` 默认值 None 冲突 | `self.data` → `self._card_data` + `card_data` property，在 `super().__init__()` 之后赋值 |
| 5 | 任务卡片左右边距不等 | `TaskCard` 固定 `width=360` + 缩进 padding 仅在 left | 移除 `width`，缩进容器 `padding=ft.Padding(left=depth*step, right=depth*step, ...)` |
| 6 | 点击任务卡片报 `'NoneType' object has no attribute 'task_id'` | 同 Bug 4 | 同 Bug 4 修复 |
| 7 | 开关任务报 `'NoneType' object has no attribute 'enabled'` | 同 Bug 4 | 同 Bug 4 修复 |
| 8 | 点击执行报 `'NoneType' object has no attribute 'task_id'` | 同 Bug 4 | 同 Bug 4 修复 |
| 10 | 点击设置报 Dropdown on_change 错误 | 同 Bug 1 | 同 Bug 1 修复 |
| 11 | 任务卡片缺删除按钮 | 原设计未要求 | `TaskCard` 加左下角删除按钮 + 二次确认 AlertDialog（与 LogCard 一致） |

需求 9（去掉步骤 tab）、需求 12（设置常驻 AppBar）、需求 13（日志 tab 与任务/统计同级）由 Q50 决策一并实现。

---
