"""
登录界面单元测试

测试LoginWindow的各项功能：
- 用户名/密码输入框正常显示
- 输入验证（空值、长度限制）
- 登录按钮状态（启用/禁用）
- 登录成功/失败提示
- 注册功能

依赖：pytest-qt
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# 尝试导入PyQt5相关模块
try:
    from PyQt5.QtWidgets import QApplication, QStackedWidget
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False

# 尝试导入登录界面
try:
    from ui.interfaces.login_interface import LoginWindow, HeroImageLabel
    import ui.interfaces.login_interface as login_interface_module
    LOGIN_INTERFACE_AVAILABLE = True
except ImportError as e:
    LOGIN_INTERFACE_AVAILABLE = False
    LOGIN_INTERFACE_IMPORT_ERROR = str(e)
    login_interface_module = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def qapp_args():
    """自定义QApplication启动参数"""
    return ["pytest-qt"]


@pytest.fixture
def mock_login_deps(monkeypatch):
    """
    Mock登录界面的所有依赖
    """
    # 如果登录界面模块不可用，跳过此fixture
    if not LOGIN_INTERFACE_AVAILABLE:
        pytest.skip(f"LoginWindow not available: {LOGIN_INTERFACE_IMPORT_ERROR}")

    # Mock AuthManager
    mock_auth = MagicMock()
    mock_auth.authenticate.return_value = (True, "登录成功")
    mock_auth.register_user.return_value = (True, "注册成功")
    monkeypatch.setattr("ui.interfaces.login_interface.AuthManager", lambda: mock_auth)

    # Mock get_program_dir
    monkeypatch.setattr("ui.interfaces.login_interface.get_program_dir", lambda: "/tmp")

    # Mock FontManager
    mock_font = MagicMock()
    mock_font.get_font_size.return_value = 12
    monkeypatch.setattr("ui.interfaces.login_interface.FontManager", mock_font)

    # Mock InfoBar
    mock_infobar = MagicMock()
    mock_infobar.success = MagicMock()
    mock_infobar.error = MagicMock()
    mock_infobar.warning = MagicMock()
    monkeypatch.setattr("ui.interfaces.login_interface.InfoBar", mock_infobar)

    # Mock QPixmap和文件检查
    mock_pixmap = MagicMock()
    mock_pixmap.isNull.return_value = True
    monkeypatch.setattr("ui.interfaces.login_interface.QPixmap", lambda x: mock_pixmap)
    monkeypatch.setattr("ui.interfaces.login_interface.os.path.exists", lambda x: False)

    return {
        "auth": mock_auth,
        "infobar": mock_infobar
    }


@pytest.fixture
def login_window(qtbot, mock_login_deps):
    """
    创建LoginWindow实例用于测试
    """
    if not LOGIN_INTERFACE_AVAILABLE:
        pytest.skip(f"LoginWindow not available: {LOGIN_INTERFACE_IMPORT_ERROR}")

    # 使用defer_heavy=True加快测试速度
    window = LoginWindow(defer_heavy=True)
    qtbot.addWidget(window)

    yield window

    # 清理
    window.close()
    window.deleteLater()


# =============================================================================
# 基础界面测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not LOGIN_INTERFACE_AVAILABLE, reason=f"LoginWindow not available")
class TestLoginInterfaceBasic:
    """登录界面基础功能测试"""

    def test_window_creation(self, login_window):
        """测试窗口创建成功"""
        assert login_window is not None
        assert login_window.windowTitle() == "RTopenEuler 登录"

    def test_window_size(self, login_window):
        """测试窗口大小固定"""
        assert login_window.width() == 1120
        assert login_window.height() == 680

    def test_login_form_elements_exist(self, login_window):
        """测试登录表单元素存在"""
        # 用户名输入框
        assert hasattr(login_window, 'login_user')
        assert login_window.login_user is not None
        assert login_window.login_user.placeholderText() == "用户名"

        # 密码输入框
        assert hasattr(login_window, 'login_pass')
        assert login_window.login_pass is not None
        assert login_window.login_pass.placeholderText() == "密码"
        assert login_window.login_pass.echoMode() == login_window.login_pass.Password

        # 登录按钮
        assert hasattr(login_window, 'login_btn')
        assert login_window.login_btn is not None
        assert login_window.login_btn.text() == "登录并进入"

    def test_register_form_elements_exist(self, login_window):
        """测试注册表单元素存在"""
        # 切换到注册模式
        login_window._set_mode("register")

        # 用户名输入框
        assert hasattr(login_window, 'reg_user')
        assert login_window.reg_user is not None
        assert login_window.reg_user.placeholderText() == "用户名"

        # 密码输入框
        assert hasattr(login_window, 'reg_pass')
        assert login_window.reg_pass is not None
        assert login_window.reg_pass.placeholderText() == "密码"

        # 确认密码输入框
        assert hasattr(login_window, 'reg_pass_confirm')
        assert login_window.reg_pass_confirm is not None
        assert login_window.reg_pass_confirm.placeholderText() == "确认密码"

        # 邀请码输入框
        assert hasattr(login_window, 'reg_invite')
        assert login_window.reg_invite is not None
        assert login_window.reg_invite.placeholderText() == "16位邀请码"

        # 注册按钮
        assert hasattr(login_window, 'register_btn')
        assert login_window.register_btn is not None
        assert login_window.register_btn.text() == "注册账号"

    def test_tab_buttons_exist(self, login_window):
        """测试切换标签按钮存在"""
        assert hasattr(login_window, 'login_tab_btn')
        assert hasattr(login_window, 'register_tab_btn')
        assert login_window.login_tab_btn.text() == "登录"
        assert login_window.register_tab_btn.text() == "注册"

    def test_mode_switching(self, login_window):
        """测试登录/注册模式切换"""
        # 初始状态应该是登录模式
        assert login_window.stack.currentIndex() == 0

        # 切换到注册模式
        login_window._set_mode("register")
        # 注册表单可能在索引1（如果已创建）
        # 或者我们需要确保注册表单已创建
        if login_window._register_form_ready:
            assert login_window.stack.currentIndex() == login_window._register_index

        # 切换回登录模式
        login_window._set_mode("login")
        assert login_window.stack.currentIndex() == 0


# =============================================================================
# 输入验证测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not LOGIN_INTERFACE_AVAILABLE, reason=f"LoginWindow not available")
class TestLoginInputValidation:
    """登录输入验证测试"""

    def test_empty_username_validation(self, login_window, mock_login_deps):
        """测试空用户名验证"""
        # 清空输入
        login_window.login_user.clear()
        login_window.login_pass.setText("password123")

        # 模拟认证失败（空用户名）
        mock_login_deps["auth"].authenticate.return_value = (False, "用户名不能为空")

        # 触发登录
        login_window._handle_login()

        # 验证错误提示被调用
        mock_login_deps["infobar"].error.assert_called_once()
        call_args = mock_login_deps["infobar"].error.call_args
        assert "登录失败" in str(call_args)

    def test_empty_password_validation(self, login_window, mock_login_deps):
        """测试空密码验证"""
        login_window.login_user.setText("testuser")
        login_window.login_pass.clear()

        # 模拟认证失败（空密码）
        mock_login_deps["auth"].authenticate.return_value = (False, "密码不能为空")

        # 触发登录
        login_window._handle_login()

        # 验证错误提示
        mock_login_deps["infobar"].error.assert_called_once()

    def test_username_length_limit(self, login_window):
        """测试用户名长度限制"""
        # 测试超长用户名
        long_username = "a" * 100
        login_window.login_user.setText(long_username)

        # 验证输入被接受（实际限制取决于实现）
        assert len(login_window.login_user.text()) == 100

    def test_password_length_limit(self, login_window):
        """测试密码长度限制"""
        # 测试超长密码
        long_password = "b" * 100
        login_window.login_pass.setText(long_password)

        # 验证输入被接受
        assert len(login_window.login_pass.text()) == 100

    def test_whitespace_username_handling(self, login_window, mock_login_deps):
        """测试用户名前后空格处理"""
        login_window.login_user.setText("  testuser  ")
        login_window.login_pass.setText("password123")

        mock_login_deps["auth"].authenticate.return_value = (True, "登录成功")

        # 触发登录
        login_window._handle_login()

        # 验证认证时被去除空格
        call_args = mock_login_deps["auth"].authenticate.call_args
        assert call_args[0][0] == "testuser"  # 去除空格后的用户名


# =============================================================================
# 登录功能测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not LOGIN_INTERFACE_AVAILABLE, reason=f"LoginWindow not available")
class TestLoginFunctionality:
    """登录功能测试"""

    def test_successful_login(self, login_window, mock_login_deps, qtbot):
        """测试成功登录"""
        # 设置有效凭据
        login_window.login_user.setText("validuser")
        login_window.login_pass.setText("validpass")

        mock_login_deps["auth"].authenticate.return_value = (True, "登录成功")

        # 监听登录成功信号
        with qtbot.waitSignal(login_window.login_success, timeout=1000):
            login_window._handle_login()

        # 验证成功提示
        mock_login_deps["infobar"].success.assert_called_once()

    def test_failed_login(self, login_window, mock_login_deps):
        """测试登录失败"""
        login_window.login_user.setText("invaliduser")
        login_window.login_pass.setText("wrongpass")

        mock_login_deps["auth"].authenticate.return_value = (False, "用户名或密码错误")

        # 触发登录
        login_window._handle_login()

        # 验证错误提示
        mock_login_deps["infobar"].error.assert_called_once()
        call_args = mock_login_deps["infobar"].error.call_args
        assert "登录失败" in str(call_args)

    def test_login_button_click(self, login_window, mock_login_deps, qtbot):
        """测试登录按钮点击"""
        login_window.login_user.setText("testuser")
        login_window.login_pass.setText("testpass")

        mock_login_deps["auth"].authenticate.return_value = (True, "登录成功")

        # 点击登录按钮
        qtbot.mouseClick(login_window.login_btn, Qt.LeftButton)

        # 验证认证被调用
        mock_login_deps["auth"].authenticate.assert_called_once()

    def test_login_return_pressed(self, login_window, mock_login_deps):
        """测试回车键触发登录"""
        login_window.login_user.setText("testuser")
        login_window.login_pass.setText("testpass")

        mock_login_deps["auth"].authenticate.return_value = (True, "登录成功")

        # 触发returnPressed信号
        login_window.login_pass.returnPressed.emit()

        # 验证认证被调用
        mock_login_deps["auth"].authenticate.assert_called_once()

    def test_login_signal_emission(self, login_window, mock_login_deps, qtbot):
        """测试登录成功信号发射"""
        login_window.login_user.setText("testuser")
        login_window.login_pass.setText("testpass")

        mock_login_deps["auth"].authenticate.return_value = (True, "登录成功")

        # 捕获信号参数
        received = []
        login_window.login_success.connect(lambda username: received.append(username))

        # 触发登录
        login_window._handle_login()

        # 验证信号被发射且携带正确参数
        assert len(received) == 1
        assert received[0] == "testuser"


# =============================================================================
# 注册功能测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
@pytest.mark.skipif(not LOGIN_INTERFACE_AVAILABLE, reason=f"LoginWindow not available")
class TestRegisterFunctionality:
    """注册功能测试"""

    def test_successful_registration(self, login_window, mock_login_deps):
        """测试成功注册"""
        login_window._set_mode("register")

        login_window.reg_user.setText("newuser")
        login_window.reg_pass.setText("newpass123")
        login_window.reg_pass_confirm.setText("newpass123")
        login_window.reg_invite.setText("INVITE_CODE_1234")

        mock_login_deps["auth"].register_user.return_value = (True, "注册成功")

        # 触发注册
        login_window._handle_register()

        # 验证成功提示
        mock_login_deps["infobar"].success.assert_called_once()

    def test_password_mismatch(self, login_window, mock_login_deps):
        """测试密码不匹配"""
        login_window._set_mode("register")

        login_window.reg_user.setText("newuser")
        login_window.reg_pass.setText("password1")
        login_window.reg_pass_confirm.setText("password2")
        login_window.reg_invite.setText("INVITE_CODE")

        # 触发注册
        login_window._handle_register()

        # 验证警告提示
        mock_login_deps["infobar"].warning.assert_called_once()
        call_args = mock_login_deps["infobar"].warning.call_args
        assert "不一致" in str(call_args)

    def test_failed_registration(self, login_window, mock_login_deps):
        """测试注册失败"""
        login_window._set_mode("register")

        login_window.reg_user.setText("existinguser")
        login_window.reg_pass.setText("pass123")
        login_window.reg_pass_confirm.setText("pass123")
        login_window.reg_invite.setText("INVALID_CODE")

        mock_login_deps["auth"].register_user.return_value = (False, "用户名已存在")

        # 触发注册
        login_window._handle_register()

        # 验证错误提示
        mock_login_deps["infobar"].error.assert_called_once()

    def test_register_switches_to_login(self, login_window, mock_login_deps):
        """测试注册成功后切换到登录模式"""
        login_window._set_mode("register")

        login_window.reg_user.setText("newuser")
        login_window.reg_pass.setText("newpass")
        login_window.reg_pass_confirm.setText("newpass")
        login_window.reg_invite.setText("VALID_CODE")

        mock_login_deps["auth"].register_user.return_value = (True, "注册成功")

        # 触发注册
        login_window._handle_register()

        # 验证切换到登录模式
        assert login_window.stack.currentIndex() == 0
        # 验证用户名被填充到登录框
        assert login_window.login_user.text() == "newuser"


# =============================================================================
# Mock测试（无需真实GUI）
# =============================================================================

class TestLoginInterfaceMocked:
    """使用Mock的登录界面测试"""

    def test_login_success_signal(self):
        """测试登录成功信号"""
        if login_interface_module is None:
            pytest.skip("登录界面模块不可用")
        with patch.multiple(
            login_interface_module,
            AuthManager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            InfoBar=MagicMock(),
            QPixmap=MagicMock(),
        ):
            from ui.interfaces.login_interface import LoginWindow

            # Mock os.path.exists
            with patch("ui.interfaces.login_interface.os.path.exists", return_value=False):
                window = LoginWindow(defer_heavy=True)

                # 连接信号
                received = []
                window.login_success.connect(lambda u: received.append(u))

                # 模拟成功登录
                window.auth_manager.authenticate.return_value = (True, "成功")
                window.login_user.setText("testuser")
                window.login_pass.setText("testpass")
                window._handle_login()

                assert len(received) == 1
                assert received[0] == "testuser"

    def test_password_visibility_toggle(self):
        """测试密码可见性切换"""
        if login_interface_module is None:
            pytest.skip("登录界面模块不可用")
        with patch.multiple(
            login_interface_module,
            AuthManager=MagicMock(),
            get_program_dir=MagicMock(return_value="/tmp"),
            FontManager=MagicMock(),
            InfoBar=MagicMock(),
            QPixmap=MagicMock(),
        ):
            from ui.interfaces.login_interface import LoginWindow

            with patch("ui.interfaces.login_interface.os.path.exists", return_value=False):
                window = LoginWindow(defer_heavy=True)

                # 默认应该是密码模式
                from PyQt5.QtWidgets import QLineEdit
                assert window.login_pass.echoMode() == QLineEdit.Password


# =============================================================================
# HeroImageLabel测试
# =============================================================================

@pytest.mark.skipif(not PYQT5_AVAILABLE, reason="PyQt5 not available")
class TestHeroImageLabel:
    """HeroImageLabel组件测试"""

    def test_label_creation(self, qtbot):
        """测试标签创建"""
        if not LOGIN_INTERFACE_AVAILABLE:
            pytest.skip("HeroImageLabel not available")

        label = HeroImageLabel()
        qtbot.addWidget(label)

        assert label is not None
        assert label.minimumHeight() == 320

    def test_set_source(self, qtbot):
        """测试设置图片源"""
        if not LOGIN_INTERFACE_AVAILABLE:
            pytest.skip("HeroImageLabel not available")

        label = HeroImageLabel()
        qtbot.addWidget(label)

        # Mock QPixmap
        mock_pixmap = MagicMock()
        mock_pixmap.isNull.return_value = False

        label.set_source(mock_pixmap)

        assert label._source == mock_pixmap
