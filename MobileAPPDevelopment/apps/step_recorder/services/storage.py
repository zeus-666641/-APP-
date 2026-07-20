"""本地存储服务

支持 JSON 文件和 SQLite 两种模式
"""
import json
from pathlib import Path
from typing import Any


class Storage:
    """本地存储

    Args:
        base_dir: 存储根目录
        storage_type: "json" 或 "sqlite"
    """

    def __init__(self, base_dir: Path, storage_type: str = "json") -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.storage_type = storage_type

    def read_json(self, key: str) -> dict[str, Any] | None:
        """读取 JSON 数据

        Args:
            key: 存储键名（作为文件名）

        Returns:
            数据字典，不存在返回 None
        """
        path = self.base_dir / f"{key}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, key: str, data: dict[str, Any]) -> None:
        """写入 JSON 数据

        Args:
            key: 存储键名
            data: 数据字典
        """
        path = self.base_dir / f"{key}.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def delete(self, key: str) -> bool:
        """删除存储项

        Args:
            key: 存储键名

        Returns:
            是否删除成功
        """
        path = self.base_dir / f"{key}.json"
        if path.exists():
            path.unlink()
            return True
        return False
