"""会话管理（应用层）。

维护匿名会话的上下文与材料勾选状态。会话标识使用不可逆哈希，不采集任何身份信息。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Session:
    session_hash: str
    history: list[dict] = field(default_factory=list)  # 多轮上下文 [{role, content}]
    checked_items: dict[str, set[int]] = field(default_factory=dict)  # 卡片 -> 已勾选材料下标


class SessionStore:
    """内存会话存储（生产可替换为 Redis）。"""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    @staticmethod
    def hash_of(openid: str) -> str:
        """会话标识不可逆哈希，无法回溯到个人。"""
        return hashlib.sha256(openid.encode("utf-8")).hexdigest()[:16]

    def get(self, session_hash: str) -> Session:
        return self._sessions.setdefault(session_hash, Session(session_hash))

    def append(self, session_hash: str, role: str, content: str) -> None:
        self.get(session_hash).history.append({"role": role, "content": content})

    def mark_checked(self, session_hash: str, card_id: str, index: int) -> None:
        """材料清单勾选状态在会话中保留。"""
        self.get(session_hash).checked_items.setdefault(card_id, set()).add(index)


session_store = SessionStore()
