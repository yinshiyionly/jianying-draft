import sys
from PyQt6.QtWidgets import QApplication

# 创建应用程序实例
app = QApplication(sys.argv)

# 应用 Material 风格
from qt_material import apply_stylesheet
apply_stylesheet(app, theme='light_blue.xml')

# 导入主窗口
from app.window import MainWindow

def main():
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    return app.exec()

if __name__ == '__main__':
    sys.exit(main()) 