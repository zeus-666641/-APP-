"""脚手架生成器

从 templates/flet-app-template/ 复制并替换占位符，生成新 App 项目。

用法:
    python scripts/scaffold.py <app_name> <app_title> [app_description]

示例:
    python scripts/scaffold.py todo_app "待办事项" "一个简洁的待办清单App"
"""
import re
import shutil
import sys
from pathlib import Path

# 路径配置
FACTORY_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = FACTORY_ROOT / "templates" / "flet-app-template"
APPS_DIR = FACTORY_ROOT / "apps"

# 占位符映射
PLACEHOLDERS = {
    "{app_name}": "",        # snake_case 项目名
    "{app_title}": "",       # 中文应用名
    "{app_description}": "", # 应用描述
}


def validate_app_name(name: str) -> bool:
    """验证项目名合法（snake_case）

    Args:
        name: 待验证名称

    Returns:
        是否合法
    """
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


def copy_and_replace(src: Path, dst: Path, replacements: dict[str, str]) -> None:
    """递归复制目录并替换文件内容中的占位符

    Args:
        src: 模板源目录
        dst: 目标目录
        replacements: 占位符替换映射
    """
    for item in src.rglob("*"):
        if item.is_dir():
            continue

        # 计算目标路径
        rel = item.relative_to(src)
        target = dst / rel

        # 跳过 .gitignore 等特殊文件（按需调整）
        if item.name in {".DS_Store"}:
            continue

        # 创建目标父目录
        target.parent.mkdir(parents=True, exist_ok=True)

        # 二进制文件直接复制
        if item.suffix in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".keystore"}:
            shutil.copy2(item, target)
            continue

        # 文本文件替换占位符
        try:
            content = item.read_text(encoding="utf-8")
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, value)
            target.write_text(content, encoding="utf-8")
        except UnicodeDecodeError:
            # 非文本文件直接复制
            shutil.copy2(item, target)


def generate_app(app_name: str, app_title: str, app_description: str = "") -> Path:
    """生成新 App 项目

    Args:
        app_name: snake_case 项目名
        app_title: 应用中文名
        app_description: 应用描述

    Returns:
        生成的项目目录路径

    Raises:
        ValueError: 参数不合法
        FileExistsError: 项目已存在
    """
    if not validate_app_name(app_name):
        raise ValueError(
            f"app_name 必须是 snake_case（小写字母开头，仅含小写字母/数字/下划线）: {app_name}"
        )

    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(f"模板目录不存在: {TEMPLATE_DIR}")

    target_dir = APPS_DIR / app_name
    if target_dir.exists():
        raise FileExistsError(f"项目已存在: {target_dir}")

    # 准备替换映射
    replacements = {
        "{app_name}": app_name,
        "{app_title}": app_title,
        "{app_description}": app_description or f"{app_title} - 由移动App工厂生成",
    }

    # 复制并替换
    copy_and_replace(TEMPLATE_DIR, target_dir, replacements)

    return target_dir


def main() -> int:
    """命令行入口

    Returns:
        退出码 0=成功, 1=失败
    """
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    app_name = sys.argv[1]
    app_title = sys.argv[2]
    app_description = sys.argv[3] if len(sys.argv) > 3 else ""

    try:
        target = generate_app(app_name, app_title, app_description)
        print(f"✓ App 项目已生成: {target}")
        print()
        print("下一步:")
        print(f"  cd {target}")
        print("  uv sync       # 安装依赖")
        print("  python main.py  # 启动预览")
        return 0
    except (ValueError, FileNotFoundError, FileExistsError) as e:
        print(f"✗ 生成失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
