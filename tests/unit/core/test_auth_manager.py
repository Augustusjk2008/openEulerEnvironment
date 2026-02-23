"""
AuthManager单元测试
测试认证管理器的凭证管理、密码加密/解密、密钥文件管理等功能
"""

import sys
import tempfile
import base64
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 确保src在路径中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))

from core.auth_manager import AuthManager, INVITE_CODE, _derive_key, _xor_bytes


@pytest.fixture
def temp_auth_dir(tmp_path):
    """提供临时认证目录"""
    return tmp_path


@pytest.fixture
def isolated_auth_manager(temp_auth_dir, monkeypatch):
    """提供隔离的认证管理器实例"""
    from core import auth_manager

    # 模拟get_program_dir返回临时目录
    monkeypatch.setattr(auth_manager, "get_program_dir", lambda: str(temp_auth_dir))

    # 创建新的认证管理器实例
    manager = AuthManager()

    yield manager

    # 清理：删除测试文件
    if os.path.exists(manager.user_file):
        os.remove(manager.user_file)


class TestDeriveKey:
    """测试密钥派生函数"""

    def test_derive_key_returns_bytes(self):
        """测试密钥派生返回字节"""
        key = _derive_key()
        assert isinstance(key, bytes)
        assert len(key) == 32  # SHA256产生32字节

    def test_derive_key_deterministic(self):
        """测试密钥派生是确定性的"""
        key1 = _derive_key()
        key2 = _derive_key()
        assert key1 == key2


class TestXorBytes:
    """测试XOR加密函数"""

    def test_xor_bytes_basic(self):
        """测试基本XOR操作"""
        data = b"hello"
        key = b"key"
        result = _xor_bytes(data, key)
        assert isinstance(result, bytes)
        assert len(result) == len(data)

    def test_xor_bytes_reversible(self):
        """测试XOR是可逆的"""
        data = b"test data"
        key = b"secret key"
        encrypted = _xor_bytes(data, key)
        decrypted = _xor_bytes(encrypted, key)
        assert decrypted == data

    def test_xor_bytes_with_longer_key(self):
        """测试使用较长密钥的XOR"""
        data = b"short"
        key = b"this is a very long key"
        result = _xor_bytes(data, key)
        decrypted = _xor_bytes(result, key)
        assert decrypted == data

    def test_xor_bytes_empty_data(self):
        """测试空数据的XOR"""
        data = b""
        key = b"key"
        result = _xor_bytes(data, key)
        assert result == b""


class TestAuthManagerEncryptDecrypt:
    """测试认证管理器加密解密功能"""

    def test_encrypt_returns_string(self, isolated_auth_manager):
        """测试加密返回字符串"""
        manager = isolated_auth_manager
        raw = b"test data"
        encrypted = manager._encrypt(raw)
        assert isinstance(encrypted, str)

    def test_decrypt_reverses_encrypt(self, isolated_auth_manager):
        """测试解密逆转加密"""
        manager = isolated_auth_manager
        raw = b"test data"
        encrypted = manager._encrypt(raw)
        decrypted = manager._decrypt(encrypted)
        assert decrypted == raw

    def test_decrypt_invalid_base64(self, isolated_auth_manager):
        """测试解密无效base64"""
        manager = isolated_auth_manager
        result = manager._decrypt("not valid base64!!!")
        assert result is None

    def test_decrypt_wrong_magic(self, isolated_auth_manager):
        """测试解密错误的magic"""
        manager = isolated_auth_manager
        # 创建有效的base64但错误的magic
        data = b"WRONGMAGIC" + b"test data"
        encoded = base64.urlsafe_b64encode(data).decode("ascii")
        result = manager._decrypt(encoded)
        assert result is None

    def test_decrypt_empty_string(self, isolated_auth_manager):
        """测试解密空字符串"""
        manager = isolated_auth_manager
        result = manager._decrypt("")
        assert result is None


class TestAuthManagerLoadSave:
    """测试认证管理器加载保存功能"""

    def test_load_nonexistent_file(self, isolated_auth_manager):
        """测试加载不存在的文件"""
        manager = isolated_auth_manager
        # 确保文件不存在
        if os.path.exists(manager.user_file):
            os.remove(manager.user_file)
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_load_empty_file(self, isolated_auth_manager):
        """测试加载空文件"""
        manager = isolated_auth_manager
        # 创建空文件
        with open(manager.user_file, "w", encoding="utf-8") as f:
            f.write("")
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_load_whitespace_file(self, isolated_auth_manager):
        """测试加载只有空白字符的文件"""
        manager = isolated_auth_manager
        with open(manager.user_file, "w", encoding="utf-8") as f:
            f.write("   \n\t  ")
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_load_invalid_encrypted_data(self, isolated_auth_manager):
        """测试加载无效加密数据"""
        manager = isolated_auth_manager
        with open(manager.user_file, "w", encoding="utf-8") as f:
            f.write("invalid encrypted data")
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_load_corrupted_json(self, isolated_auth_manager):
        """测试加载损坏的JSON"""
        manager = isolated_auth_manager
        # 加密无效JSON
        raw = b"not valid json"
        encrypted = manager._encrypt(raw)
        with open(manager.user_file, "w", encoding="utf-8") as f:
            f.write(encrypted)
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_load_missing_users_key(self, isolated_auth_manager):
        """测试加载缺少users键的数据"""
        manager = isolated_auth_manager
        raw = json.dumps({"version": 1}).encode("utf-8")
        encrypted = manager._encrypt(raw)
        with open(manager.user_file, "w", encoding="utf-8") as f:
            f.write(encrypted)
        data = manager._load()
        assert data == {"version": 1, "users": {}}

    def test_save_and_load(self, isolated_auth_manager):
        """测试保存和加载"""
        manager = isolated_auth_manager
        data = {"version": 1, "users": {"testuser": {"salt": "abc", "hash": "def"}}}
        manager._save(data)
        loaded = manager._load()
        assert loaded == data

    def test_save_creates_file(self, isolated_auth_manager):
        """测试保存创建文件"""
        manager = isolated_auth_manager
        data = {"version": 1, "users": {}}
        manager._save(data)
        assert os.path.exists(manager.user_file)


class TestAuthManagerRegister:
    """测试用户注册功能"""

    def test_register_success(self, isolated_auth_manager):
        """测试成功注册"""
        manager = isolated_auth_manager
        success, msg = manager.register_user("testuser", "password123", INVITE_CODE)
        assert success is True
        assert "成功" in msg

    def test_register_invalid_invite_code(self, isolated_auth_manager):
        """测试无效邀请码"""
        manager = isolated_auth_manager
        success, msg = manager.register_user("testuser", "password123", "WRONGCODE")
        assert success is False
        assert "邀请码" in msg

    def test_register_empty_username(self, isolated_auth_manager):
        """测试空用户名"""
        manager = isolated_auth_manager
        success, msg = manager.register_user("", "password123", INVITE_CODE)
        assert success is False
        assert "不能为空" in msg

    def test_register_empty_password(self, isolated_auth_manager):
        """测试空密码"""
        manager = isolated_auth_manager
        success, msg = manager.register_user("testuser", "", INVITE_CODE)
        assert success is False
        assert "不能为空" in msg

    def test_register_duplicate_user(self, isolated_auth_manager):
        """测试重复用户"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        success, msg = manager.register_user("testuser", "password456", INVITE_CODE)
        assert success is False
        assert "已存在" in msg

    def test_register_stores_salt_and_hash(self, isolated_auth_manager):
        """测试注册存储salt和hash"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        data = manager._load()
        assert "testuser" in data["users"]
        user_data = data["users"]["testuser"]
        assert "salt" in user_data
        assert "hash" in user_data
        assert "created_at" in user_data

    def test_register_salt_is_base64(self, isolated_auth_manager):
        """测试salt是base64编码"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        data = manager._load()
        salt = data["users"]["testuser"]["salt"]
        # 验证是有效的base64
        decoded = base64.b64decode(salt)
        assert len(decoded) == 16  # 16字节salt


class TestAuthManagerAuthenticate:
    """测试用户认证功能"""

    def test_authenticate_success(self, isolated_auth_manager):
        """测试成功认证"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        success, msg = manager.authenticate("testuser", "password123")
        assert success is True
        assert "成功" in msg

    def test_authenticate_wrong_password(self, isolated_auth_manager):
        """测试错误密码"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        success, msg = manager.authenticate("testuser", "wrongpassword")
        assert success is False
        assert "密码错误" in msg

    def test_authenticate_nonexistent_user(self, isolated_auth_manager):
        """测试不存在的用户"""
        manager = isolated_auth_manager
        success, msg = manager.authenticate("nonexistent", "password123")
        assert success is False
        assert "不存在" in msg

    def test_authenticate_empty_username(self, isolated_auth_manager):
        """测试空用户名"""
        manager = isolated_auth_manager
        success, msg = manager.authenticate("", "password123")
        assert success is False
        assert "不能为空" in msg

    def test_authenticate_empty_password(self, isolated_auth_manager):
        """测试空密码"""
        manager = isolated_auth_manager
        success, msg = manager.authenticate("testuser", "")
        assert success is False
        assert "不能为空" in msg

    def test_authenticate_corrupted_user_data(self, isolated_auth_manager):
        """测试损坏的用户数据"""
        manager = isolated_auth_manager
        # 手动创建损坏的用户数据
        data = {
            "version": 1,
            "users": {
                "testuser": {
                    "salt": "invalid_base64",
                    "hash": "invalid_base64",
                }
            }
        }
        manager._save(data)
        success, msg = manager.authenticate("testuser", "password123")
        assert success is False
        assert "损坏" in msg


class TestAuthManagerHashPassword:
    """测试密码哈希功能"""

    def test_hash_password_deterministic_with_same_salt(self, isolated_auth_manager):
        """测试相同salt产生相同哈希"""
        manager = isolated_auth_manager
        salt = os.urandom(16)
        hash1 = manager._hash_password("password123", salt)
        hash2 = manager._hash_password("password123", salt)
        assert hash1 == hash2

    def test_hash_password_different_with_different_salt(self, isolated_auth_manager):
        """测试不同salt产生不同哈希"""
        manager = isolated_auth_manager
        salt1 = os.urandom(16)
        salt2 = os.urandom(16)
        hash1 = manager._hash_password("password123", salt1)
        hash2 = manager._hash_password("password123", salt2)
        assert hash1 != hash2

    def test_hash_password_returns_32_bytes(self, isolated_auth_manager):
        """测试哈希返回32字节"""
        manager = isolated_auth_manager
        salt = os.urandom(16)
        hash_result = manager._hash_password("password123", salt)
        assert len(hash_result) == 32


class TestInviteCode:
    """测试邀请码常量"""

    def test_invite_code_format(self):
        """测试邀请码格式"""
        assert isinstance(INVITE_CODE, str)
        assert len(INVITE_CODE) == 16
        assert INVITE_CODE == "OPENEULER-202601"


class TestEdgeCases:
    """测试边界情况"""

    def test_multiple_users(self, isolated_auth_manager):
        """测试多个用户"""
        manager = isolated_auth_manager
        manager.register_user("user1", "pass1", INVITE_CODE)
        manager.register_user("user2", "pass2", INVITE_CODE)

        assert manager.authenticate("user1", "pass1")[0] is True
        assert manager.authenticate("user2", "pass2")[0] is True
        assert manager.authenticate("user1", "pass2")[0] is False

    def test_special_characters_in_password(self, isolated_auth_manager):
        """测试密码中的特殊字符"""
        manager = isolated_auth_manager
        special_password = "p@$$w0rd!#$%^&*()"
        manager.register_user("testuser", special_password, INVITE_CODE)
        assert manager.authenticate("testuser", special_password)[0] is True

    def test_unicode_username(self, isolated_auth_manager):
        """测试Unicode用户名"""
        manager = isolated_auth_manager
        manager.register_user("用户", "password123", INVITE_CODE)
        assert manager.authenticate("用户", "password123")[0] is True

    def test_long_password(self, isolated_auth_manager):
        """测试长密码"""
        manager = isolated_auth_manager
        long_password = "a" * 1000
        manager.register_user("testuser", long_password, INVITE_CODE)
        assert manager.authenticate("testuser", long_password)[0] is True

    def test_file_permissions_preserved(self, isolated_auth_manager):
        """测试文件权限被保留"""
        manager = isolated_auth_manager
        manager.register_user("testuser", "password123", INVITE_CODE)
        # 验证文件存在且可读
        assert os.path.exists(manager.user_file)
        with open(manager.user_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0


class TestIntegration:
    """集成测试"""

    def test_full_user_lifecycle(self, isolated_auth_manager):
        """测试完整用户生命周期"""
        manager = isolated_auth_manager

        # 注册
        success, _ = manager.register_user("lifecycle_user", "mypassword", INVITE_CODE)
        assert success is True

        # 认证成功
        success, _ = manager.authenticate("lifecycle_user", "mypassword")
        assert success is True

        # 认证失败
        success, _ = manager.authenticate("lifecycle_user", "wrongpassword")
        assert success is False

        # 重新加载后认证仍然成功
        manager2 = AuthManager()
        manager2.user_file = manager.user_file
        success, _ = manager2.authenticate("lifecycle_user", "mypassword")
        assert success is True

    def test_data_persistence(self, isolated_auth_manager):
        """测试数据持久化"""
        manager = isolated_auth_manager

        # 注册用户
        manager.register_user("persistent_user", "password123", INVITE_CODE)

        # 创建新的管理器实例
        manager2 = AuthManager()
        manager2.user_file = manager.user_file

        # 验证数据持久化
        success, _ = manager2.authenticate("persistent_user", "password123")
        assert success is True
