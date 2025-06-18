from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QTableWidget, QTableWidgetItem, 
                           QPushButton, QFrame, QDateTimeEdit, QHeaderView)
from PyQt6.QtGui import QFont
from datetime import datetime

class SearchFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchFrame")
        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 第一行搜索条件
        row1_layout = QHBoxLayout()
        # UUID搜索
        uuid_label = QLabel("UUID:")
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("请输入UUID")
        row1_layout.addWidget(uuid_label)
        row1_layout.addWidget(self.uuid_input)
        # 小说名称搜索
        novel_label = QLabel("小说名称:")
        self.novel_input = QLineEdit()
        self.novel_input.setPlaceholderText("请输入小说名称")
        row1_layout.addWidget(novel_label)
        row1_layout.addWidget(self.novel_input)
        layout.addLayout(row1_layout)

        # 第二行搜索条件
        row2_layout = QHBoxLayout()
        # 版本名称搜索
        version_label = QLabel("版本名称:")
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("请输入版本名称")
        row2_layout.addWidget(version_label)
        row2_layout.addWidget(self.version_input)
        # 创建人搜索
        creator_label = QLabel("创建人:")
        self.creator_input = QLineEdit()
        self.creator_input.setPlaceholderText("请输入创建人")
        row2_layout.addWidget(creator_label)
        row2_layout.addWidget(self.creator_input)
        layout.addLayout(row2_layout)

        # 第三行搜索条件
        row3_layout = QHBoxLayout()
        # 创建时间搜索
        time_label = QLabel("创建时间:")
        self.start_time = QDateTimeEdit()
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_time.setCalendarPopup(True)
        row3_layout.addWidget(time_label)
        row3_layout.addWidget(self.start_time)
        
        time_to_label = QLabel("至")
        self.end_time = QDateTimeEdit()
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_time.setCalendarPopup(True)
        row3_layout.addWidget(time_to_label)
        row3_layout.addWidget(self.end_time)
        
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("searchButton")
        row3_layout.addWidget(self.search_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("resetButton")
        row3_layout.addWidget(self.reset_btn)
        
        layout.addLayout(row3_layout)

        # 设置样式
        self.setStyleSheet("""
            QFrame#searchFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QLabel {
                min-width: 60px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-right: 10px;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 4px;
                color: white;
            }
            QPushButton#searchButton {
                background-color: #1976D2;
            }
            QPushButton#resetButton {
                background-color: #757575;
            }
        """)

class DraftBoxPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 添加搜索区域
        self.search_frame = SearchFrame()
        layout.addWidget(self.search_frame, stretch=2)

        # 添加表格区域
        self.table = QTableWidget()
        self.table.setObjectName("draftTable")
        
        # 设置列
        headers = ["序号", "UUID", "小说名称", "版本名称", "创建人", "创建时间", "操作"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # 添加一些示例数据
        self.add_sample_data()
        
        layout.addWidget(self.table, stretch=8)

        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

    def add_sample_data(self):
        # 添加一些示例数据
        sample_data = [
            ["1", "uuid-001", "小说1", "v1.0", "用户A", "2024-01-20 10:00:00"],
            ["2", "uuid-002", "小说2", "v2.0", "用户B", "2024-01-21 11:00:00"],
            ["3", "uuid-003", "小说3", "v1.5", "用户C", "2024-01-22 12:00:00"],
        ]

        self.table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, text in enumerate(data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            
            # 添加操作按钮
            operations_widget = QWidget()
            operations_layout = QHBoxLayout(operations_widget)
            operations_layout.setContentsMargins(5, 0, 5, 0)
            
            edit_btn = QPushButton("编辑")
            edit_btn.setObjectName("editButton")
            delete_btn = QPushButton("删除")
            delete_btn.setObjectName("deleteButton")
            
            operations_layout.addWidget(edit_btn)
            operations_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, operations_widget)

        # 设置操作列按钮样式
        self.setStyleSheet(self.styleSheet() + """
            QPushButton#editButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 3px 8px;
            }
            QPushButton#deleteButton {
                background-color: #F44336;
                color: white;
                border-radius: 4px;
                padding: 3px 8px;
            }
        """) 