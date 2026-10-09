"""SQLite accounts and revisioned conversations; never store plaintext credentials."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class AccountError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


def password_hash(password: str, salt: str) -> str:
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384,
                          r=8, p=1, maxmem=67108864, dklen=32).hex()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Accounts:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                    salt TEXT NOT NULL, password TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tokens (
                    digest TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,
                    data TEXT, updated REAL NOT NULL, PRIMARY KEY(user_id,id));
            """)
        path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def authenticate(self, username: str, password: str, register: bool = False):
        with self.connect() as db:
            if register:
                salt, user_id = secrets.token_hex(16), secrets.token_hex(16)
                hashed = password_hash(password, salt)
                try:
                    db.execute("INSERT INTO users VALUES (?,?,?,?)",
                               (user_id, username, salt, hashed))
                except sqlite3.IntegrityError:
                    raise AccountError(409, "用户名已被使用") from None
            else:
                user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                salt = user["salt"] if user else "00" * 16
                candidate = password_hash(password, salt)
                if not user or not hmac.compare_digest(candidate, user["password"]):
                    raise AccountError(401, "用户名或密码不正确")
                user_id = user["id"]
            token = secrets.token_urlsafe(32)
            db.execute("DELETE FROM tokens WHERE expires <= ?", (time.time(),))
            # Bound concurrent devices to ten; older logins are revoked.
            db.execute("DELETE FROM tokens WHERE digest IN (SELECT digest FROM tokens "
                       "WHERE user_id=? ORDER BY expires DESC LIMIT -1 OFFSET 9)", (user_id,))
            db.execute("INSERT INTO tokens VALUES (?,?,?)",
                       (token_hash(token), user_id, time.time() + 30 * 86400))
            return {"token": token, "user": {"id": user_id, "username": username}}

    def user(self, token: str):
        with self.connect() as db:
            user = db.execute("SELECT u.id,u.username FROM users u JOIN tokens t "
                              "ON t.user_id=u.id WHERE t.digest=? AND t.expires>?",
                              (token_hash(token), time.time())).fetchone()
            if not user:
                raise AccountError(401, "登录已过期，请重新登录")
            return dict(user)

    def logout(self, token: str):
        with self.connect() as db:
            db.execute("DELETE FROM tokens WHERE digest=?", (token_hash(token),))

    def delete_account(self, user_id: str, password: str):
        with self.connect() as db:
            user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            if not user or not hmac.compare_digest(password_hash(password, user["salt"]),
                                                  user["password"]):
                raise AccountError(401, "密码不正确")
            db.execute("DELETE FROM tokens WHERE user_id=?", (user_id,))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            db.execute("DELETE FROM users WHERE id=?", (user_id,))

    def list_sessions(self, user_id: str):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY updated DESC",
                              (user_id,)).fetchall()
            return [{"id": row["id"], "revision": row["revision"],
                     "deleted": row["data"] is None,
                     "data": json.loads(row["data"]) if row["data"] else None} for row in rows]

    def save_session(self, user_id: str, session_id: str, revision: int, data: dict | None):
        serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":")) if data else None
        if serialized and len(serialized.encode()) > 200_000:
            raise AccountError(413, "单个对话最多200KB，请新建对话")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision,data FROM sessions WHERE user_id=? AND id=?",
                             (user_id, session_id)).fetchone()
            if (row["revision"] if row else 0) != revision or (row and row["data"] is None):
                raise AccountError(409, "对话已在其他设备变更，请同步后重试")
            if data and not row:
                count = db.execute("SELECT COUNT(*) FROM sessions WHERE user_id=? AND data IS NOT NULL",
                                   (user_id,)).fetchone()[0]
                if count >= 50:
                    raise AccountError(409, "云端最多保留50个对话，请先删除旧记录")
            if not data and not row:
                raise AccountError(404, "对话不存在")
            next_revision = revision + 1
            db.execute("INSERT INTO sessions VALUES (?,?,?,?,?) ON CONFLICT(user_id,id) "
                       "DO UPDATE SET revision=excluded.revision,data=excluded.data,updated=excluded.updated",
                       (user_id, session_id, next_revision, serialized, time.time()))
            return {"id": session_id, "revision": next_revision}
