from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QFrame, QFileDialog,
                           QMessageBox)
from PyQt6.QtGui import QFont
import os

class CreateDraftPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # 创建表单卡片
        form_card = QFrame()
        form_card.setObjectName("formCard")
        
        # 表单布局
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(30)

        # 标题
        title = QLabel("创建草稿箱")
        title.setObjectName("pageTitle")
        title.setFont(QFont("SF Pro Display", 24))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(title)

        # UUID输入区域
        uuid_layout = QVBoxLayout()
        uuid_layout.setSpacing(8)
        
        uuid_label = QLabel("UUID:")
        uuid_label.setObjectName("fieldLabel")
        uuid_label.setFont(QFont("SF Pro Text", 13))
        
        self.uuid_input = QLineEdit()
        self.uuid_input.setObjectName("uuidInput")
        self.uuid_input.setPlaceholderText("请输入UUID")
        self.uuid_input.setMinimumHeight(32)
        
        uuid_layout.addWidget(uuid_label)
        uuid_layout.addWidget(self.uuid_input)
        form_layout.addLayout(uuid_layout)

        # 文件夹选择区域
        folder_layout = QVBoxLayout()
        folder_layout.setSpacing(8)
        
        folder_label = QLabel("保存路径:")
        folder_label.setObjectName("fieldLabel")
        folder_label.setFont(QFont("SF Pro Text", 13))
        
        folder_input_layout = QHBoxLayout()
        folder_input_layout.setSpacing(10)
        
        self.folder_input = QLineEdit()
        self.folder_input.setObjectName("folderInput")
        self.folder_input.setPlaceholderText("请选择保存路径")
        self.folder_input.setReadOnly(True)
        self.folder_input.setMinimumHeight(32)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.setFont(QFont("SF Pro Text", 13))
        
        folder_input_layout.addWidget(self.folder_input)
        folder_input_layout.addWidget(self.browse_btn)
        
        folder_layout.addWidget(folder_label)
        folder_layout.addLayout(folder_input_layout)
        form_layout.addLayout(folder_layout)

        # 添加一些空间
        form_layout.addStretch()

        # 生成按钮
        self.generate_btn = QPushButton("生成草稿箱")
        self.generate_btn.setObjectName("generateButton")
        self.generate_btn.setMinimumWidth(200)
        self.generate_btn.setMinimumHeight(38)
        self.generate_btn.setFont(QFont("SF Pro Text", 14))
        form_layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 将表单卡片添加到主布局
        layout.addWidget(form_card)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            
            #formCard {
                background-color: white;
                border-radius: 10px;
            }
            
            #pageTitle {
                color: #1d1d1f;
                margin-bottom: 20px;
            }
            
            #fieldLabel {
                color: #1d1d1f;
                font-weight: 500;
            }
            
            QLineEdit {
                background-color: #f5f5f7;
                border: none;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 14px;
                color: #1d1d1f;
            }
            
            QLineEdit:focus {
                background-color: white;
                border: 2px solid #0066cc;
            }
            
            QLineEdit:disabled {
                background-color: #f5f5f7;
                color: #86868b;
            }
            
            QPushButton#browseButton {
                background-color: #f5f5f7;
                border: none;
                border-radius: 6px;
                color: #1d1d1f;
                padding: 0 15px;
            }
            
            QPushButton#browseButton:hover {
                background-color: #e5e5e5;
            }
            
            QPushButton#generateButton {
                background-color: #0066cc;
                border: none;
                border-radius: 6px;
                color: white;
                padding: 0 20px;
            }
            
            QPushButton#generateButton:hover {
                background-color: #0055b3;
            }
            
            QPushButton#generateButton:pressed {
                background-color: #004c99;
            }
        """)

    def setup_connections(self):
        self.browse_btn.clicked.connect(self.browse_folder)
        self.generate_btn.clicked.connect(self.generate_draft)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择保存路径",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)

    def generate_draft(self):
        # 获取输入
        uuid = self.uuid_input.text().strip()
        folder = self.folder_input.text().strip()

        # 验证输入
        if not uuid:
            self.show_message("错误", "请输入UUID", QMessageBox.Icon.Warning)
            return
        
        if not folder:
            self.show_message("错误", "请选择保存路径", QMessageBox.Icon.Warning)
            return

        try:
            # TODO: 这里添加实际的草稿箱生成逻辑
            # 示例：创建文件夹
            draft_path = os.path.join(folder, f"draft_{uuid}")
            os.makedirs(draft_path, exist_ok=True)
            
            # 成功提示
            self.show_message("成功", "草稿箱创建成功！", QMessageBox.Icon.Information)
            
            # 清空输入
            self.uuid_input.clear()
            self.folder_input.clear()
            
        except Exception as e:
            # 错误提示
            self.show_message("错误", f"创建草稿箱失败：{str(e)}", QMessageBox.Icon.Critical)

    def show_message(self, title, message, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 设置消息框样式
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #1d1d1f;
                font-size: 14px;
                font-family: 'SF Pro Text';
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'SF Pro Text';
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0055b3;
            }
        """)
        
        # 显示在窗口中央
        msg.exec() 