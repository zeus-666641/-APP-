"""存储服务测试"""
import json
from pathlib import Path

import pytest

from services.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage:
    """临时存储实例"""
    return Storage(base_dir=tmp_path, storage_type="json")


def test_write_and_read_json(storage: Storage) -> None:
    """写入并读取 JSON"""
    data = {"name": "test", "value": 123}
    storage.write_json("test_key", data)

    result = storage.read_json("test_key")
    assert result == data


def test_read_nonexistent(storage: Storage) -> None:
    """读取不存在的键返回 None"""
    result = storage.read_json("nonexistent")
    assert result is None


def test_delete_existing(storage: Storage) -> None:
    """删除已存在的键"""
    storage.write_json("to_delete", {"a": 1})
    assert storage.delete("to_delete") is True
    assert storage.read_json("to_delete") is None


def test_delete_nonexistent(storage: Storage) -> None:
    """删除不存在的键返回 False"""
    assert storage.delete("nonexistent") is False


def test_unicode_content(storage: Storage) -> None:
    """中文内容读写"""
    data = {"name": "张三", "desc": "测试用户"}
    storage.write_json("unicode", data)

    result = storage.read_json("unicode")
    assert result == data
    assert result["name"] == "张三"
