# 步骤记录器 · 无法实现清单

> 集中记录所有在 Flet 框架内无法实现的需求项，每项含：来源需求、原因、变通方案。
> 用户原则：以上要求有无法实现的添加到无法实现清单里（需求17）。
> 应用质量是第一优先级，无法实现不等于"假装实现"，必须明确告知用户。

---

## U1. 绑定无障碍服务（AccessibilityService）

### 来源需求
- 需求16：软件应该可以绑定无障碍服务并且有显示在其他应用上层的权限
- 需求17：以上要求有无法实现的添加到无法实现清单里

### 详细说明
用户希望 step_recorder App 能够：
- 在系统设置中开启"无障碍服务"权限，授权后 App 可监听其他应用界面
- 通过 AccessibilityService 模拟跨应用点击/滑动/手势操作
- 监听系统级事件（如通知到达、窗口变化）

### 为什么无法实现（在 Flet 框架内）

1. **框架限制**：Flet 是基于 Flutter 引擎的 Python UI 框架，不提供 Android 原生 AccessibilityService API。
   - Flet 应用编译为 APK 后，Dart/Python 层无法注册 AccessibilityService 子类
   - 需要编写 Java/Kotlin 类继承 `AccessibilityService` 并实现 `onAccessibilityEvent`，Flet 无法承载这种原生代码

2. **权限声明可用但实际无效**：
   - 可以修改 `AndroidManifest.xml` 添加 `<service android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">` 声明
   - 但由于缺少 Java/Kotlin 实现，权限声明后服务无法启动，属于"声明空壳"
   - 用户在系统设置中也找不到可开启的"步骤记录器"无障碍服务

3. **Flet 0.86.1 API 缺失**：
   - 无 `ft.accessibility_service` 或类似 API
   - 无跨应用模拟输入 API
   - 无 `dispatchGesture` 等无障碍手势 API

### 变通方案（如适用）
- **App 内点击/滑动**：Flet 可以模拟 App 内部控件的点击（通过 `control.click()` 或事件触发），但不能跨应用
- **替代品**：Tasker/MacroDroid 等专门工具仍是 Android 自动化的最佳方案，step_recorder 不与之竞争
- **未来扩展方向**（记录，暂不实现）：
  - 写一个独立的 Java/Kotlin 原生模块（如 FFI 插件），编译为 AAR 包，让 Flet 通过 platform channel 调用
  - 但这超出 Flet 标准开发流程，且 Flet 暂不提供稳定的 platform channel API

### UI 处理方式（按用户决策）
- 在"系统设置 → 权限管理"页中，"无障碍服务"项显示为置灰状态
- 点击弹提示："此功能需要 Android 原生支持，Flet 框架无法实现"
- 不删除该 UI 项，让用户感知功能存在但未实现

### 状态
- 永久无法实现（除非 Flet 框架原生支持，或编写 FFI 插件，不在本期范围内）

---

## U2. 显示在其他应用上层权限（悬浮窗 WindowManager）

### 来源需求
- 需求16：软件应该可以绑定无障碍服务并且有显示在其他应用上层的权限
- 需求17：以上要求有无法实现的添加到无法实现清单里
- PRD 第 10 章：悬浮窗快捷操作

### 详细说明
用户希望 step_recorder App 能够：
- 申请 `SYSTEM_ALERT_WINDOW` 权限
- 通过 `WindowManager.addView()` 在其他应用上层显示悬浮按钮/工具栏
- 用户在其他应用中操作时，悬浮窗提供快捷触发步骤的能力

### 为什么无法实现（在 Flet 框架内）

1. **框架限制**：Flet 不提供 `WindowManager` API。
   - Flet 的 UI 控件只能在当前 Page 内显示
   - 无法将 Flet 控件"浮"到其他应用上层
   - 即使声明了 `SYSTEM_ALERT_WINDOW` 权限，也无 API 调用

2. **Flet 0.86.1 API 缺失**：
   - 无 `ft.overlay_window` 或类似 API
   - 无 `WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY` 等价物
   - 无 `addView` 等价 API

3. **替代 API 不等效**：
   - Flet 有 `page.window_always_on_top`，但这只是把当前窗口置顶（桌面端语义），不能在 Android 上跨应用悬浮
   - Flet 有 `ft.SnackBar` / `ft.AlertDialog`，但这些只能在自己 App 内显示
   - Android 通知可以"悬浮"显示（heads-up notification），但不是用户期望的"任意位置的可拖动悬浮按钮"

### 变通方案（如适用）
- **本地通知**：可作为简化版的"快捷入口"，用户点击通知可启动 App（但不是真正的悬浮窗）
- **小部件（Widget）**：理论上可以写原生 AppWidget，但 Flet 不支持 AppWidget API
- **未来扩展方向**（记录，暂不实现）：
  - 与 U1 一样，需写原生 Kotlin/Java 模块，超出 Flet 标准开发流程

### UI 处理方式（按用户决策）
- 在"系统设置 → 权限管理"页中，"显示在其他应用上层"项显示为置灰状态
- 点击弹提示："此功能需要 Android 原生 WindowManager，Flet 框架无法实现"
- "悬浮窗快捷操作"模块（PRD 第 10 章）在导航中标记为"未实现"

### 状态
- 永久无法实现（除非 Flet 框架原生支持，或编写 FFI 插件，不在本期范围内）

---

## 汇总表

| 编号 | 需求 | 限制类型 | 原因 | 变通 |
|---|---|---|---|---|
| U1 | 绑定无障碍服务 | 永久 | Flet 无 AccessibilityService API | 无 |
| U2 | 显示在其他应用上层 | 永久 | Flet 无 WindowManager API | 本地通知（不等效） |

## 维护约定
- 每次新增需求中如发现无法实现项，追加到本文件对应章节
- 状态变更（如 Flet 未来版本支持）需更新本文件
- 本文件需与 `docs/prd/scope.md` 互相参照，避免重复维护
