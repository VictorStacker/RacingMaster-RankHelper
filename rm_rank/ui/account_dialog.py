"""账号管理对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QInputDialog, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal

from rm_rank.repositories import AccountRepository
from rm_rank.exceptions import BusinessLogicError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class AccountManagementDialog(QDialog):
    """账号管理对话框"""
    
    # 信号：账号切换时发出
    account_changed = pyqtSignal(int)  # 发送新的账号ID
    # 信号：账号列表变化时发出（创建、编辑、删除）
    accounts_updated = pyqtSignal()  # 通知刷新账号列表
    
    def __init__(self, account_repo: AccountRepository, parent=None):
        super().__init__(parent)
        self.account_repo = account_repo
        self.init_ui()
        self.load_accounts()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("账号管理")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明文字
        info_label = QLabel("管理多个游戏账号，每个账号有独立的车库数据")
        info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(info_label)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        create_button = QPushButton("创建账号")
        create_button.clicked.connect(self.create_account)
        button_layout.addWidget(create_button)
        
        edit_button = QPushButton("编辑账号")
        edit_button.clicked.connect(self.edit_account)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton("删除账号")
        delete_button.clicked.connect(self.delete_account)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        switch_button = QPushButton("切换到此账号")
        switch_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        switch_button.clicked.connect(self.switch_account)
        button_layout.addWidget(switch_button)
        
        layout.addLayout(button_layout)
        
        # 账号列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "账号名称", "描述", "状态"])
        
        # 设置表格属性
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 双击切换账号
        self.table.doubleClicked.connect(self.switch_account)
        
        layout.addWidget(self.table)
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        close_layout.addWidget(close_button)
        
        layout.addLayout(close_layout)
    
    def load_accounts(self):
        """加载账号列表"""
        try:
            accounts = self.account_repo.get_all_accounts()
            
            # 清空表格
            self.table.setRowCount(0)
            
            # 填充数据
            for account in accounts:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                self.table.setItem(row, 0, QTableWidgetItem(str(account.id)))
                self.table.setItem(row, 1, QTableWidgetItem(account.name))
                self.table.setItem(row, 2, QTableWidgetItem(account.description or ""))
                
                # 状态列
                status = "✓ 当前账号" if account.is_active else ""
                status_item = QTableWidgetItem(status)
                if account.is_active:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                self.table.setItem(row, 3, status_item)
                
        except Exception as e:
            logger.error(f"加载账号列表失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"加载账号列表失败：{str(e)}")
    
    def create_account(self):
        """创建新账号"""
        # 输入账号名称
        name, ok = QInputDialog.getText(
            self, 
            "创建账号", 
            "请输入账号名称:",
            text="新账号"
        )
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        # 输入账号描述
        description, ok = QInputDialog.getText(
            self, 
            "创建账号", 
            "请输入账号描述（可选）:",
            text=""
        )
        
        if not ok:
            return
        
        try:
            account = self.account_repo.create_account(name, description or None)
            QMessageBox.information(self, "成功", f"账号 '{account.name}' 创建成功！")
            self.load_accounts()
            # 发出信号通知账号列表已更新
            self.accounts_updated.emit()
            
        except BusinessLogicError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            logger.error(f"创建账号失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"创建账号失败：{str(e)}")
    
    def edit_account(self):
        """编辑选中的账号"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要编辑的账号")
            return
        
        row = selected_rows[0].row()
        account_id = int(self.table.item(row, 0).text())
        current_name = self.table.item(row, 1).text()
        current_desc = self.table.item(row, 2).text()
        
        # 输入新名称
        name, ok = QInputDialog.getText(
            self, 
            "编辑账号", 
            "请输入新的账号名称:",
            text=current_name
        )
        
        if not ok:
            return
        
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "警告", "账号名称不能为空")
            return
        
        # 输入新描述
        description, ok = QInputDialog.getText(
            self, 
            "编辑账号", 
            "请输入新的账号描述:",
            text=current_desc
        )
        
        if not ok:
            return
        
        try:
            self.account_repo.update_account(
                account_id, 
                name=name if name != current_name else None,
                description=description
            )
            QMessageBox.information(self, "成功", "账号信息已更新")
            self.load_accounts()
            # 发出信号通知账号列表已更新
            self.accounts_updated.emit()
            
        except BusinessLogicError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            logger.error(f"编辑账号失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"编辑账号失败：{str(e)}")
    
    def delete_account(self):
        """删除选中的账号"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的账号")
            return
        
        row = selected_rows[0].row()
        account_id = int(self.table.item(row, 0).text())
        account_name = self.table.item(row, 1).text()
        is_active = self.table.item(row, 3).text() == "✓ 当前账号"
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除账号 '{account_name}' 吗？\n\n"
            f"警告：该账号的所有车库数据将被永久删除！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 检查是否是最后一个账号
        if self.table.rowCount() == 1:
            QMessageBox.warning(self, "警告", "不能删除最后一个账号")
            return
        
        try:
            self.account_repo.delete_account(account_id)
            QMessageBox.information(self, "成功", f"账号 '{account_name}' 已删除")
            self.load_accounts()
            # 发出信号通知账号列表已更新
            self.accounts_updated.emit()
            
            # 如果删除的是激活账号，发出信号通知切换
            if is_active:
                active_account = self.account_repo.get_active_account()
                if active_account:
                    self.account_changed.emit(active_account.id)
            
        except BusinessLogicError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            logger.error(f"删除账号失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"删除账号失败：{str(e)}")
    
    def switch_account(self):
        """切换到选中的账号"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要切换的账号")
            return
        
        row = selected_rows[0].row()
        account_id = int(self.table.item(row, 0).text())
        account_name = self.table.item(row, 1).text()
        
        # 检查是否已经是当前账号
        if self.table.item(row, 3).text() == "✓ 当前账号":
            QMessageBox.information(self, "提示", f"'{account_name}' 已经是当前账号")
            return
        
        try:
            self.account_repo.set_active_account(account_id)
            QMessageBox.information(self, "成功", f"已切换到账号 '{account_name}'")
            self.load_accounts()
            
            # 发出信号通知主窗口
            self.account_changed.emit(account_id)
            
        except BusinessLogicError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            logger.error(f"切换账号失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"切换账号失败：{str(e)}")
