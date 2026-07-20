"""User 模型测试"""
from datetime import datetime

from models.user import User


def test_user_creation() -> None:
    """创建用户"""
    user = User(user_id="u1", name="张三")
    assert user.user_id == "u1"
    assert user.name == "张三"
    assert isinstance(user.created_at, datetime)


def test_user_to_dict() -> None:
    """转字典"""
    user = User(user_id="u1", name="张三")
    d = user.to_dict()
    assert d["user_id"] == "u1"
    assert d["name"] == "张三"
    assert "created_at" in d


def test_user_from_dict() -> None:
    """从字典构造"""
    data = {
        "user_id": "u1",
        "name": "张三",
        "created_at": "2026-07-20T10:00:00",
    }
    user = User.from_dict(data)
    assert user.user_id == "u1"
    assert user.name == "张三"
    assert user.created_at.year == 2026


def test_user_roundtrip() -> None:
    """序列化往返"""
    user = User(user_id="u1", name="张三")
    d = user.to_dict()
    user2 = User.from_dict(d)
    assert user2.user_id == user.user_id
    assert user2.name == user.name
