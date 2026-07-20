# Git仓库一键初始化脚本
# 用法：在工厂目录下执行 .\scripts\init_git.ps1
#
# 功能：
#   1. 检查Git是否已安装
#   2. 初始化Git仓库
#   3. 检查.gitignore是否存在
#   4. 首次提交所有文件
#   5. 显示仓库状态

$ErrorActionPreference = "Stop"

# 切换到工厂根目录（脚本的上级目录）
$factoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $factoryRoot

Write-Host "=== 移动App工厂 Git初始化 ===" -ForegroundColor Cyan
Write-Host "工厂目录: $factoryRoot"
Write-Host ""

# 步骤1：检查Git
Write-Host "[1/5] 检查Git安装..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  ✓ $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Git未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装Git：" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://git-scm.com/download/win"
    Write-Host "  2. 下载64-bit Git for Windows Setup"
    Write-Host "  3. 双击安装，所有选项保持默认"
    Write-Host "  4. 安装完成后重启PowerShell，重新执行此脚本"
    exit 1
}

# 步骤2：检查是否已初始化
Write-Host ""
Write-Host "[2/5] 检查仓库状态..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "  ! 仓库已存在，跳过初始化" -ForegroundColor Yellow
    $alreadyInit = $true
} else {
    git init | Out-Null
    Write-Host "  ✓ Git仓库已初始化" -ForegroundColor Green
    $alreadyInit = $false
}

# 步骤3：检查.gitignore
Write-Host ""
Write-Host "[3/5] 检查.gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host "  ✓ .gitignore 已存在" -ForegroundColor Green
} else {
    # 创建针对工厂的.gitignore
    $gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/
*.egg

# 虚拟环境
.venv/
venv/
env/

# 测试
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# IDE
.vscode/
.idea/
*.swp

# 系统
.DS_Store
Thumbs.db

# 应用数据
data/
*.db
*.sqlite

# 敏感信息
.env
.env.local
*.keystore
credentials/

# 构建产物
build/
releases/
*.apk
*.aab

# Flet构建缓存
.flet/
"@
    Set-Content -Path ".gitignore" -Value $gitignoreContent -Encoding UTF8
    Write-Host "  ✓ .gitignore 已创建" -ForegroundColor Green
}

# 步骤4：配置用户（如未配置）
Write-Host ""
Write-Host "[4/5] 检查Git用户配置..." -ForegroundColor Yellow
$userName = git config user.name
$userEmail = git config user.email
if (-not $userName -or -not $userEmail) {
    Write-Host "  ! 需要配置Git用户信息" -ForegroundColor Yellow
    if (-not $userName) {
        $inputName = Read-Host "  请输入你的名字（任意，如：移动App工厂主）"
        git config user.name $inputName
    }
    if (-not $userEmail) {
        $inputEmail = Read-Host "  请输入邮箱（任意，如：factory@local.dev）"
        git config user.email $inputEmail
    }
    git config init.defaultBranch main
    git config core.autocrlf input
    Write-Host "  ✓ Git用户已配置" -ForegroundColor Green
} else {
    Write-Host "  ✓ 用户: $userName <$userEmail>" -ForegroundColor Green
}

# 步骤5：首次提交（仅新仓库）
if (-not $alreadyInit) {
    Write-Host ""
    Write-Host "[5/5] 首次提交..." -ForegroundColor Yellow
    git add .
    git commit -m "初始化移动App工厂

包含：
- 7大项目/27流程/94步骤骨架
- 3个核心Skill（app-ideation、flet-scaffold、flet-cloud-builder）
- Flet项目模板（14文件）
- 脚手架脚本scaffold.py
- 完整规则、编码习惯、工作流程文档
- 项目索引.md（AI导航）
- 记忆系统（决策/经验/项目记忆/骨架）

详见 项目索引.md"

    Write-Host "  ✓ 首次提交完成" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[5/5] 跳过提交（仓库已存在）" -ForegroundColor Yellow
}

# 显示最终状态
Write-Host ""
Write-Host "=== 初始化完成 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "仓库状态：" -ForegroundColor Cyan
git status
Write-Host ""
Write-Host "最近提交：" -ForegroundColor Cyan
git log --oneline -5 2>&1
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  - 日常提交：git add . ; git commit -m '描述'"
Write-Host "  - 查看状态：git status"
Write-Host "  - 查看历史：git log --oneline"
Write-Host "  - 详见 Git方案.md"
