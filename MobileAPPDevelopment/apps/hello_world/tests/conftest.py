"""pytest 配置"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
