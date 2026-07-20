"""用户数据模型"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """用户模型

    Attributes:
        user_id: 用户唯一ID
        name: 用户名
        created_at: 创建时间
    """

    user_id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """转字典"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """从字典构造"""
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
