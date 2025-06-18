from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                           QScrollArea, QHBoxLayout)
from PyQt6.QtGui import QFont, QPixmap

# 首先确保 QApplication 已创建
from app.util import get_application
_ = get_application()

class WelcomePage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('welcomePage')
        self.setWidgetResizable(True)
        
        # 创建内容窗口部件
        self.content = QWidget()
        self.setWidget(self.content)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主布局
        layout = QVBoxLayout(self.content)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # 创建指南卡片
        guide_card = QFrame()
        guide_card.setObjectName("guideCard")
        guide_card.setFrameShape(QFrame.Shape.StyledPanel)
        guide_card.setFrameShadow(QFrame.Shadow.Raised)
        guide_card.setMinimumWidth(800)
        
        card_layout = QVBoxLayout(guide_card)
        card_layout.setSpacing(30)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        # 添加标题
        title = QLabel('使用指南')
        title.setObjectName("guideTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        card_layout.addWidget(title)
        
        # 添加步骤说明
        steps = [
            {
                'number': '01',
                'title': '创建素材草稿',
                'desc': '点击左上角新建按钮，输入标题后创建素材草稿'
            },
            {
                'number': '02',
                'title': '导入视频和音频',
                'desc': '将需要使用的视频和音频素材拖拽到时间轴上'
            },
            {
                'number': '03',
                'title': '编辑效果',
                'desc': '调整视频片段、添加转场、设置字幕和特效'
            },
            {
                'number': '04',
                'title': '导出成品',
                'desc': '确认效果后，点击导出按钮生成最终视频'
            }
        ]
        
        for step in steps:
            step_widget = QWidget()
            step_layout = QHBoxLayout(step_widget)
            step_layout.setSpacing(20)
            
            # 步骤序号
            number = QLabel(step['number'])
            number.setObjectName("stepNumber")
            number.setFont(QFont("Arial", 32, QFont.Weight.Bold))
            number.setFixedWidth(80)
            step_layout.addWidget(number)
            
            # 步骤内容
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setSpacing(5)
            
            step_title = QLabel(step['title'])
            step_title.setObjectName("stepTitle")
            step_title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
            content_layout.addWidget(step_title)
            
            step_desc = QLabel(step['desc'])
            step_desc.setObjectName("stepDesc")
            step_desc.setFont(QFont("Microsoft YaHei", 12))
            content_layout.addWidget(step_desc)
            
            step_layout.addWidget(content)
            step_layout.addStretch()
            
            card_layout.addWidget(step_widget)
        
        # 将卡片添加到主布局
        layout.addWidget(guide_card)
        layout.addStretch()
        
        # 设置样式
        self.set_styles()
        
    def set_styles(self):
        # 设置卡片样式
        self.setStyleSheet("""
            #guideCard {
                background-color: white;
                border-radius: 12px;
                border: none;
            }
            
            #guideTitle {
                color: #333333;
            }
            
            #stepNumber {
                color: #1976D2;
            }
            
            #stepTitle {
                color: #333333;
            }
            
            #stepDesc {
                color: #666666;
            }
            
            QScrollArea {
                background: #F5F5F5;
                border: none;
            }
        """) 