import sys
from PyQt6.QtWidgets import QApplication

def get_application():
    """确保QApplication已经创建，并返回实例"""
    if not QApplication.instance():
        return QApplication(sys.argv)
    return QApplication.instance() 