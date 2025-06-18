from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSlot
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QStackedWidget, QListWidget, QListWidgetItem, QLabel,
                           QPushButton, QFrame, QSizePolicy, QDialog, QLineEdit,
                           QGridLayout, QMessageBox)
from PyQt6.QtGui import QIcon, QFont, QPixmap
import asyncio
from functools import partial
import traceback

# 首先确保 QApplication 已创建
from app.util import get_application
_ = get_application()

# 导入页面
from app.welcome import WelcomePage
from app.draft_box import DraftBoxPage
from app.create_draft import CreateDraftPage

# 导入服务
from app.services.auth_service import auth_service


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.resize(480, 520)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 添加标题和副标题
        title = QLabel("登录对话框")
        title.setObjectName("loginTitle")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #0066ff;")
        main_layout.addWidget(title)
        
        subtitle = QLabel("简洁的登录界面，支持手机号验证码登录")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setFont(QFont("Microsoft YaHei", 12))
        subtitle.setStyleSheet("color: #666666; margin-bottom: 30px;")
        main_layout.addWidget(subtitle)
        
        # 创建登录卡片
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setStyleSheet("""
            #loginCard {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        
        # 用户登录标题
        user_login_label = QLabel("用户登录")
        user_login_label.setObjectName("userLoginLabel")
        user_login_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        card_layout.addWidget(user_login_label)
        
        # 提示文本
        hint_label = QLabel("请输入您的手机号码以获取验证码")
        hint_label.setObjectName("hintLabel")
        hint_label.setFont(QFont("Microsoft YaHei", 12))
        hint_label.setStyleSheet("color: #666666; margin-bottom: 10px;")
        card_layout.addWidget(hint_label)
        
        # 手机号码输入
        phone_label = QLabel("手机号码")
        phone_label.setObjectName("phoneLabel")
        phone_label.setFont(QFont("Microsoft YaHei", 12))
        card_layout.addWidget(phone_label)
        
        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("phoneInput")
        self.phone_input.setPlaceholderText("请输入手机号码")
        self.phone_input.setFont(QFont("Microsoft YaHei", 12))
        self.phone_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        card_layout.addWidget(self.phone_input)
        
        # 验证码输入区域
        verify_label = QLabel("验证码")
        verify_label.setObjectName("verifyLabel")
        verify_label.setFont(QFont("Microsoft YaHei", 12))
        card_layout.addWidget(verify_label)
        
        verify_layout = QHBoxLayout()
        verify_layout.setSpacing(10)
        
        self.verify_input = QLineEdit()
        self.verify_input.setObjectName("verifyInput")
        self.verify_input.setPlaceholderText("请输入验证码")
        self.verify_input.setFont(QFont("Microsoft YaHei", 12))
        self.verify_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        verify_layout.addWidget(self.verify_input)
        
        self.get_code_btn = QPushButton("获取验证码")
        self.get_code_btn.setObjectName("getCodeBtn")
        self.get_code_btn.setFont(QFont("Microsoft YaHei", 11))
        self.get_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        verify_layout.addWidget(self.get_code_btn)
        
        card_layout.addLayout(verify_layout)
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFont(QFont("Microsoft YaHei", 12))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                padding: 10px 30px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        button_layout.addWidget(self.cancel_btn)
        
        self.login_btn = QPushButton("登录")
        self.login_btn.setObjectName("confirmLoginBtn")
        self.login_btn.setFont(QFont("Microsoft YaHei", 12))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066ff;
                border: none;
                border-radius: 4px;
                padding: 10px 30px;
                color: white;
            }
            QPushButton:hover {
                background-color: #0052cc;
            }
            QPushButton:disabled {
                background-color: #99ccff;
            }
        """)
        button_layout.addWidget(self.login_btn)
        
        card_layout.addLayout(button_layout)
        
        # 添加登录卡片到主布局
        main_layout.addWidget(login_card)
        
        # 倒计时相关
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)  # 1秒
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_seconds = 0
        
        # 连接信号
        self.cancel_btn.clicked.connect(self.reject)
        self.login_btn.clicked.connect(self.on_login_clicked)
        self.get_code_btn.clicked.connect(self.on_get_code_clicked)
    
    def on_get_code_clicked(self):
        """获取验证码按钮点击处理"""
        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "提示", "请输入手机号码")
            return
        
        # 禁用按钮，防止重复点击
        self.get_code_btn.setEnabled(False)
        
        # 使用异步方式请求验证码
        asyncio.ensure_future(self.request_verification_code(phone))
    
    async def request_verification_code(self, phone):
        """请求验证码的异步方法"""
        try:
            # 调用服务层获取验证码
            success, message = await auth_service.request_verification_code(phone)
            
            # 在UI线程中更新界面
            self.handle_verification_result(success, message)
            
        except Exception as e:
            traceback.print_exc()
            # 在UI线程中显示错误
            self.handle_verification_result(False, f"获取验证码失败: {str(e)}")
    
    def handle_verification_result(self, success, message):
        """处理验证码请求结果"""
        if success:
            # 开始倒计时
            self.countdown_seconds = 60
            self.get_code_btn.setText(f"已发送 ({self.countdown_seconds}s)")
            self.countdown_timer.start()
        else:
            # 重新启用按钮
            self.get_code_btn.setEnabled(True)
            QMessageBox.warning(self, "提示", message)
    
    def update_countdown(self):
        """更新倒计时"""
        self.countdown_seconds -= 1
        if self.countdown_seconds <= 0:
            self.countdown_timer.stop()
            self.get_code_btn.setEnabled(True)
            self.get_code_btn.setText("获取验证码")
        else:
            self.get_code_btn.setText(f"已发送 ({self.countdown_seconds}s)")
    
    def on_login_clicked(self):
        """登录按钮点击处理"""
        phone = self.phone_input.text().strip()
        code = self.verify_input.text().strip()
        
        if not phone:
            QMessageBox.warning(self, "提示", "请输入手机号码")
            return
            
        if not code:
            QMessageBox.warning(self, "提示", "请输入验证码")
            return
        
        # 禁用登录按钮，防止重复点击
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        
        # 使用异步方式登录
        asyncio.ensure_future(self.perform_login(phone, code))
    
    async def perform_login(self, phone, code):
        """执行登录的异步方法"""
        try:
            # 调用服务层登录
            success, user_info, message = await auth_service.login(phone, code)
            
            # 在UI线程中更新界面
            self.handle_login_result(success, user_info, message)
            
        except Exception as e:
            traceback.print_exc()
            # 在UI线程中显示错误
            self.handle_login_result(False, {}, f"登录失败: {str(e)}")
    
    def handle_login_result(self, success, user_info, message):
        """处理登录结果"""
        if success:
            self.accept()  # 关闭对话框，返回接受结果
        else:
            # 重新启用登录按钮
            self.login_btn.setEnabled(True)
            self.login_btn.setText("登录")
            QMessageBox.warning(self, "提示", message)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口基本属性
        self.setWindowTitle("素材草稿助手")
        self.resize(1200, 800)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 先创建内容区域，再创建导航面板
        self.setup_content_area()
        self.setup_nav_panel()
        
        # 添加组件到主布局
        main_layout.addWidget(self.nav_panel)
        main_layout.addWidget(self.stack_widget)
        
        # 设置初始选中项
        self.nav_list.setCurrentRow(0)
        
        # 设置样式
        self.set_styles()
        
        # 初始化用户状态
        self.init_user_state()
        
        # 注册服务回调
        self.register_service_callbacks()
    
    def init_user_state(self):
        """初始化用户状态"""
        # 从数据库加载最后登录的用户
        auth_service.load_last_logged_in_user()
        
        # 检查是否已登录
        if auth_service.is_logged_in():
            # 获取用户信息
            user_info = auth_service.get_user_info()
            # 更新UI
            self.update_user_ui(user_info)
            # 验证token是否有效
            asyncio.ensure_future(self.validate_token())
    
    async def validate_token(self):
        """异步验证令牌有效性"""
        is_valid = await auth_service.validate_current_token()
        if not is_valid:
            # Token无效，登出用户
            auth_service.logout()
    
    def register_service_callbacks(self):
        """注册服务回调"""
        # 登录回调
        auth_service.register_login_callback(self.on_login_status_changed)
        # 登出回调
        auth_service.register_logout_callback(self.on_logout)
    
    @pyqtSlot(bool, dict, str)
    def on_login_status_changed(self, success, user_info, message):
        """登录状态变更回调"""
        if success:
            self.update_user_ui(user_info)
    
    @pyqtSlot()
    def on_logout(self):
        """登出回调"""
        self.username_label.setText("未登录")
        self.status_label.setText("点击登录")
        self.login_button.setText("登录")
        # 断开之前的连接
        try:
            self.login_button.clicked.disconnect()
        except:
            pass
        # 重新连接到登录功能
        self.login_button.clicked.connect(self.show_login_dialog)
    
    def update_user_ui(self, user_info):
        """更新用户界面"""
        if user_info:
            # 提取用户信息
            username = user_info.get("nickname") or user_info.get("username") or "用户"
            phone = user_info.get("phone", "")
            
            # 处理手机号显示
            if phone and len(phone) == 11:
                phone_display = f"{phone[:3]}****{phone[7:]}"
            else:
                phone_display = phone
            
            # 更新UI
            self.username_label.setText(username)
            self.status_label.setText(phone_display if phone_display else "已登录")
            self.login_button.setText("退出")
            
            # 断开之前的连接
            try:
                self.login_button.clicked.disconnect()
            except:
                pass
            # 重新连接到登出功能
            self.login_button.clicked.connect(self.logout_user)
    
    def setup_nav_panel(self):
        """设置左侧导航面板"""
        self.nav_panel = QWidget()
        self.nav_panel.setObjectName("navPanel")
        self.nav_panel.setFixedWidth(220)
        
        # 创建导航面板的垂直布局
        nav_layout = QVBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # 添加标题区域
        title_container = QWidget()
        title_container.setObjectName("titleContainer")
        title_container.setFixedHeight(60)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(20, 0, 10, 0)
        
        # 应用标题
        title_label = QLabel("素材草稿助手")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        nav_layout.addWidget(title_container)
        
        # 创建导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFrameShape(QListWidget.Shape.NoFrame)
        self.nav_list.setSpacing(4)
        
        # 添加导航项
        self.add_nav_item("首页", "home", 0)
        self.add_nav_item("草稿箱", "drafts", 1)
        self.add_nav_item("创建草稿", "create", 2)
        
        # 连接导航项的点击事件
        self.nav_list.currentRowChanged.connect(self.stack_widget.setCurrentIndex)
        
        # 添加导航列表到布局，并设置它可以伸展
        nav_layout.addWidget(self.nav_list, 1)  # 使用 stretch factor = 1
        
        # 创建用户信息区域
        self.user_info_widget = self.create_user_info_widget()
        nav_layout.addWidget(self.user_info_widget)
    
    def create_user_info_widget(self):
        """创建用户信息区域"""
        user_widget = QFrame()
        user_widget.setObjectName("userInfoWidget")
        user_widget.setFrameShape(QFrame.Shape.StyledPanel)
        user_widget.setFixedHeight(80)
        
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(15, 10, 15, 10)
        
        # 用户头像
        avatar_label = QLabel()
        avatar_label.setObjectName("userAvatar")
        # 使用默认头像
        default_avatar = QPixmap(40, 40)
        default_avatar.fill(Qt.GlobalColor.lightGray)
        avatar_label.setPixmap(default_avatar)
        avatar_label.setFixedSize(40, 40)
        avatar_label.setScaledContents(True)
        user_layout.addWidget(avatar_label)
        
        # 用户信息
        user_info = QVBoxLayout()
        user_info.setSpacing(2)
        
        # 用户名
        self.username_label = QLabel("未登录")
        self.username_label.setObjectName("usernameLabel")
        self.username_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        user_info.addWidget(self.username_label)
        
        # 登录状态
        self.status_label = QLabel("点击登录")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFont(QFont("Microsoft YaHei", 8))
        user_info.addWidget(self.status_label)
        
        user_layout.addLayout(user_info)
        
        # 登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedSize(60, 30)
        self.login_button.clicked.connect(self.show_login_dialog)
        user_layout.addWidget(self.login_button)
        
        return user_widget
    
    def show_login_dialog(self):
        """显示登录对话框"""
        dialog = LoginDialog(self)
        result = dialog.exec()
    
    def logout_user(self):
        """登出用户"""
        auth_service.logout()
    
    def setup_content_area(self):
        """设置右侧内容区域"""
        # 创建堆叠窗口部件用于切换页面
        self.stack_widget = QStackedWidget()
        self.stack_widget.setObjectName("stackWidget")
        
        # 添加欢迎页面
        self.welcome_page = WelcomePage()
        self.stack_widget.addWidget(self.welcome_page)
        
        # 添加草稿箱页面
        self.draft_box_page = DraftBoxPage()
        self.stack_widget.addWidget(self.draft_box_page)
        
        # 添加创建草稿页面
        self.create_draft_page = CreateDraftPage()
        self.stack_widget.addWidget(self.create_draft_page)
    
    def add_nav_item(self, title, icon_name=None, index=None):
        """添加导航项"""
        item = QListWidgetItem(title)
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # 可以在这里设置图标
        # if icon_name:
        #     item.setIcon(QIcon(f"path/to/icons/{icon_name}.png"))
        
        self.nav_list.addItem(item)
    
    def add_page(self, page_widget, nav_title, icon_name=None):
        """添加新页面和对应的导航项"""
        # 添加页面到堆叠窗口
        index = self.stack_widget.addWidget(page_widget)
        
        # 添加导航项
        self.add_nav_item(nav_title, icon_name, index)
        
        return index
        
    def set_styles(self):
        """设置应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            
            #navPanel {
                background-color: #f5f5f7;
                border-right: 1px solid #e0e0e0;
            }
            
            #titleContainer {
                border-bottom: 1px solid #e0e0e0;
            }
            
            #titleLabel {
                color: #1976D2;
                font-weight: bold;
            }
            
            #navList {
                background-color: #f5f5f7;
                border: none;
                color: #333333;
                padding: 15px 10px;
            }
            
            #navList::item {
                height: 36px;
                padding-left: 15px;
                border-radius: 6px;
                margin: 2px 0px;
                font-size: 14px;
            }
            
            #navList::item:selected {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
            }
            
            #navList::item:hover:!selected {
                background-color: #e5e5e5;
            }
            
            #stackWidget {
                background-color: white;
            }
            
            #userInfoWidget {
                background-color: #f0f0f0;
                border-top: 1px solid #e0e0e0;
                border-radius: 0;
                margin: 0;
            }
            
            #userAvatar {
                border-radius: 20px;
                background-color: #ddd;
            }
            
            #usernameLabel {
                color: #333333;
            }
            
            #statusLabel {
                color: #666666;
            }
            
            #loginButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
            }
            
            #loginButton:hover {
                background-color: #1565C0;
            }
        """) 