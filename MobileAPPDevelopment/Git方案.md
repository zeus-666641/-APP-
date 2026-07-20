# Git版本控制方案

> 用于移动App工厂的版本控制。**不解决云端访问**（云端访问用方案A：打开工厂为项目根）。
> Git的作用：备份、回滚、分支管理、变更追踪。

## 一、安装Git（一次性）

### 方式1：官网下载（推荐）
1. 访问 https://git-scm.com/download/win
2. 下载 **64-bit Git for Windows Setup**
3. 双击安装，所有选项保持默认，一路"Next"
4. 安装完成后重启TRAE Work

### 方式2：用winget（如可用）
```powershell
winget install --id Git.Git -e
```

### 验证安装
打开新的PowerShell窗口，执行：
```powershell
git --version
```
应返回类似 `git version 2.45.0.windows.1`。

---

## 二、配置Git（一次性）

装完Git后首次使用需要配置用户信息：

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf input
```

说明：
- `user.name`/`user.email`：提交记录的作者标识（任意填，无需注册）
- `init.defaultBranch main`：默认分支名用main（现代约定）
- `core.autocrlf input`：Windows下处理换行符，避免跨平台问题

---

## 三、初始化工厂仓库（一次性）

### 方式A：一键脚本（推荐）
在工厂目录右键 → "Open PowerShell here"，执行：
```powershell
cd "f:\trae\CodingEnvironment\MobileAPPDevelopment"
.\scripts\init_git.ps1
```

脚本会自动完成：
- `git init`
- 检查.gitignore
- `git add .`
- 首次提交 `git commit -m "初始化移动App工厂"`
- 显示仓库状态

### 方式B：手动执行
```powershell
cd "f:\trae\CodingEnvironment\MobileAPPDevelopment"
git init
git add .
git commit -m "初始化移动App工厂"
git log --oneline
```

---

## 四、日常工作流

### 每次工作流阶段完成后提交
```powershell
# 在工厂目录下
git add .
git commit -m "feat(阶段X): 完成XXX流程"
```

提交信息规范（参考规则.md R17）：
- `feat`: 新功能（如新增App、新页面）
- `fix`: 修复bug
- `refactor`: 重构
- `docs`: 文档变更
- `chore`: 杂项（配置、依赖）

示例：
```
git commit -m "feat(选题): 完成健身App市场调研，生成3个候选方案"
git commit -m "feat(编程): 生成todo_app脚手架"
git commit -m "fix(封装): 修复APK签名失败问题"
```

### 实验性功能用分支
```powershell
# 创建分支
git checkout -b experiment/新功能

# 在分支上工作...完成后
git checkout main           # 切回主分支
git merge experiment/新功能  # 合并
git branch -d experiment/新功能  # 删除分支
```

### 回滚错误改动
```powershell
# 查看历史
git log --oneline

# 回到某个提交（保留改动在工作区）
git reset --soft <commit-id>

# 彻底丢弃某次提交（慎用）
git reset --hard <commit-id>

# 查看某次提交改了什么
git show <commit-id>
```

### 查看状态
```powershell
git status              # 当前改动
git diff                # 未暂存的改动
git diff --cached       # 已暂存的改动
git log --oneline -10   # 最近10次提交
```

---

## 五、与TRAE Work结合

### TRAE Work的Git面板
- 左侧活动栏 → 源代码管理图标（分支形状）
- 可视化查看改动、暂存、提交
- 不用敲命令

### 工作树（Worktree）—— 本地并行开发
**前提**：仓库已初始化

1. 对话输入框左下角 → 切换为"工作树"模式
2. 发起任务，AI自动创建工作树分支
3. 任务完成后点"AI合并"或"手动合并"

**适用场景**：
- 同时开发2个App（每个App一个工作树）
- 实验性重构（不影响主分支）
- 大改动前先在工作树试水

**不适用**：云端任务（工作树只对本地任务有效）

---

## 六、备份策略（不用GitHub）

### 本地备份
定期复制工厂目录到其他位置：
```powershell
# 复制到D盘备份
Copy-Item -Recurse "f:\trae\CodingEnvironment\MobileAPPDevelopment" "D:\backup\MobileAPPDevelopment_$(Get-Date -Format yyyyMMdd)"
```

### 用Git打tag标记里程碑
```powershell
# 每完成一个App打tag
git tag -a v0.1.0-todo-app -m "完成待办事项App v0.1.0"
git tag -l  # 查看所有tag
```

### 可选：推送到私有云盘
如果用坚果云/OneDrive等：
1. 把工厂目录放入云盘同步路径
2. 或定期推送副本到云盘

---

## 七、常见问题

### Q1: AI改坏了代码怎么回滚？
```powershell
git log --oneline -5     # 找到改坏前的commit
git reset --hard <commit-id>  # 回到那个状态
```

### Q2: 提交信息写错了？
```powershell
git commit --amend -m "新的提交信息"
```

### Q3: 误提交了大文件？
```powershell
# 从最近一次提交移除
git rm --cached <大文件路径>
git commit --amend
```
然后把这个文件路径加入 `.gitignore`。

### Q4: 想看某个文件的历史变更？
```powershell
git log --oneline -- <文件路径>
git diff <旧commit> <新commit> -- <文件路径>
```

### Q5: 云端任务能用Git吗？
能，但需要通过GitHub集成（你不想用）。所以云端任务还是依赖**方案A：打开工厂为项目根**让云端直接访问文件。Git只在你本地操作时起版本控制作用。

---

## 八、验证清单

装完Git后，依次执行以下命令验证：
```powershell
cd "f:\trae\CodingEnvironment\MobileAPPDevelopment"
git --version                    # 1. Git已安装
git status                       # 2. 仓库已初始化（显示分支名）
git log --oneline                # 3. 有首次提交
git branch                       # 4. 在main分支
```

全部通过即Git方案就绪。
