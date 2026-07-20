# 日常提交便捷脚本
# 用法：
#   .\scripts\commit.ps1 "提交信息"
#   .\scripts\commit.ps1 "feat(编程): 生成todo_app脚手架"
#
# 功能：
#   1. 显示当前改动
#   2. 暂存所有改动
#   3. 提交（带时间戳）
#   4. 显示最近5次提交

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Message
)

$ErrorActionPreference = "Stop"

$factoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $factoryRoot

Write-Host "=== 提交改动 ===" -ForegroundColor Cyan
Write-Host ""

# 显示改动概览
Write-Host "[1/3] 当前改动：" -ForegroundColor Yellow
git status --short
Write-Host ""

# 暂存所有改动
Write-Host "[2/3] 暂存改动..." -ForegroundColor Yellow
git add .
Write-Host "  ✓ 已暂存" -ForegroundColor Green
Write-Host ""

# 提交
Write-Host "[3/3] 提交..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$fullMessage = "$Message`n`n时间: $timestamp"
git commit -m $fullMessage
Write-Host ""
Write-Host "=== 提交完成 ===" -ForegroundColor Cyan
Write-Host ""

# 显示最近提交
Write-Host "最近5次提交：" -ForegroundColor Cyan
git log --oneline -5
