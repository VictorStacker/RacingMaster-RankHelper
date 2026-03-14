"""账号选择对话框"""
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QScrollArea, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt


class AccountSelectionDialog(QDialog):
    """账号选择对话框，用于导入时选择要导入的账号"""
    
    def __init__(self, accounts_data: List[Dict[str, Any]], parent=None):
        """
        初始化账号选择对话框
        
        Args:
            accounts_data: 账号数据列表，每个元素包含 'name' 和 'description' 字段
            parent: 父窗口
        """
        super().__init__(parent)
        self.accounts_data = accounts_data
        self.checkboxes = []
        self.selected_accounts = []
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("选择要导入的账号")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("请选择要导入的账号：")
        layout.addWidget(info_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 创建账号复选框
        for account_data in self.accounts_data:
            account_name = account_data.get('name', '未命名账号')
            account_desc = account_data.get('description', '')
            
            checkbox = QCheckBox(account_name)
            checkbox.setChecked(True)  # 默认全选
            
            if account_desc:
                checkbox.setToolTip(account_desc)
            
            self.checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 全选/取消全选按钮
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 确定/取消按钮
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        action_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)
        
        layout.addLayout(action_layout)
        
    def select_all(self):
        """全选所有账号"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)
    
    def deselect_all(self):
        """取消全选所有账号"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)
    
    def get_selected_accounts(self) -> List[str]:
        """
        获取用户选择的账号名称列表
        
        Returns:
            选中的账号名称列表
        """
        selected = []
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.isChecked():
                account_name = self.accounts_data[i].get('name', '')
                if account_name:
                    selected.append(account_name)
        return selected
