"""
User auth storage with simple encrypted payload.
"""

import base64
import hashlib
import json
import os
import time

from core.config_manager import get_program_dir

INVITE_CODE = "OPENEULER-202601"
_FILE_MAGIC = "OEUSER1"
_APP_SECRET = "RTopenEuler::AuthStore::v1"


def _derive_key():
    return hashlib.pbkdf2_hmac(
        "sha256",
        _APP_SECRET.encode("utf-8"),
        b"openEuler-user-store",
        100000,
        dklen=32,
    )


def _xor_bytes(data, key):
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


class AuthManager:
    def __init__(self):
        self.user_file = os.path.join(get_program_dir(), "users.dat")

    def _encrypt(self, raw_bytes):
        key = _derive_key()
        xored = _xor_bytes(raw_bytes, key)
        payload = _FILE_MAGIC.encode("ascii") + xored
        return base64.urlsafe_b64encode(payload).decode("ascii")

    def _decrypt(self, encoded_text):
        try:
            raw = base64.urlsafe_b64decode(encoded_text.encode("ascii"))
        except Exception:
            return None
        magic = _FILE_MAGIC.encode("ascii")
        if not raw.startswith(magic):
            return None
        key = _derive_key()
        return _xor_bytes(raw[len(magic):], key)

    def _load(self):
        if not os.path.exists(self.user_file):
            return {"version": 1, "users": {}}
        try:
            with open(self.user_file, "r", encoding="utf-8") as file_obj:
                content = file_obj.read().strip()
            if not content:
                return {"version": 1, "users": {}}
            decrypted = self._decrypt(content)
            if decrypted is None:
                return {"version": 1, "users": {}}
            data = json.loads(decrypted.decode("utf-8"))
            if not isinstance(data, dict) or "users" not in data:
                return {"version": 1, "users": {}}
            return data
        except Exception:
            return {"version": 1, "users": {}}

    def _save(self, data):
        payload = json.dumps(data, ensure_ascii=True, indent=2).encode("utf-8")
        encrypted = self._encrypt(payload)
        with open(self.user_file, "w", encoding="utf-8") as f:
            f.write(encrypted)

    def _hash_password(self, password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000,
            dklen=32,
        )

    def register_user(self, username, password, invite_code):
        if invite_code != INVITE_CODE:
            return False, "邀请码不正确"
        if len(invite_code) != 16:
            return False, "邀请码长度必须为16字符"
        if not username or not password:
            return False, "用户名或密码不能为空"
        data = self._load()
        users = data.get("users", {})
        if username in users:
            return False, "用户已存在"
        salt = os.urandom(16)
        pwd_hash = self._hash_password(password, salt)
        users[username] = {
            "salt": base64.b64encode(salt).decode("ascii"),
            "hash": base64.b64encode(pwd_hash).decode("ascii"),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["users"] = users
        self._save(data)
        return True, "注册成功"

    def authenticate(self, username, password):
        if not username or not password:
            return False, "用户名或密码不能为空"
        data = self._load()
        users = data.get("users", {})
        info = users.get(username)
        if not info:
            return False, "用户不存在"
        try:
            salt = base64.b64decode(info.get("salt", ""))
            expected = base64.b64decode(info.get("hash", ""))
        except Exception:
            return False, "用户数据损坏"
        pwd_hash = self._hash_password(password, salt)
        if pwd_hash != expected:
            return False, "密码错误"
        return True, "登录成功"
