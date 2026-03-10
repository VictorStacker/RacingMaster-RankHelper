"""
通用对话框模块

提供统一的错误、警告、信息和确认对话框。
"""

from PyQt6.QtWidgets import QMessageBox, QWidget, QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt6.QtCore import Qt
from typing import Optional

from rm_rank.exceptions import (
    NetworkError,
    CrawlerError,
    ValidationError,
    DatabaseError,
    BusinessLogicError,
    PeakSpeedError,
)
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class ErrorDialog:
    """错误对话框工具类"""

    @staticmethod
    def show_error(
        parent: Optional[QWidget], title: str, message: str, details: Optional[str] = None
    ):
        """
        显示错误对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 错误消息
            details: 详细错误信息（可选）
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if details:
            msg_box.setDetailedText(details)

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        logger.error(f"{title}: {message}")

    @staticmethod
    def show_exception(parent: Optional[QWidget], exception: Exception):
        """
        根据异常类型显示相应的错误对话框

        Args:
            parent: 父窗口
            exception: 异常对象
        """
        if isinstance(exception, NetworkError):
            ErrorDialog.show_error(
                parent,
                "网络错误",
                "无法连接到数据源网站",
                f"详细信息：{str(exception)}\n\n请检查：\n1. 网络连接是否正常\n2. 网站是否可访问\n3. 防火墙设置",
            )
        elif isinstance(exception, CrawlerError):
            ErrorDialog.show_error(
                parent,
                "数据更新错误",
                "更新数据时发生错误",
                f"详细信息：{str(exception)}\n\n可能的原因：\n1. 网站结构已变化\n2. 数据格式不符合预期\n3. 网站访问限制",
            )
        elif isinstance(exception, ValidationError):
            errors = exception.errors if hasattr(exception, "errors") else [str(exception)]
            error_list = "\n".join(f"• {err}" for err in errors)
            ErrorDialog.show_error(
                parent,
                "数据验证错误",
                "数据验证失败",
                f"以下数据不符合要求：\n\n{error_list}",
            )
        elif isinstance(exception, DatabaseError):
            ErrorDialog.show_error(
                parent,
                "数据库错误",
                "数据库操作失败",
                f"详细信息：{str(exception)}\n\n请检查：\n1. 数据库文件是否可写\n2. 磁盘空间是否充足\n3. 数据库是否损坏",
            )
        elif isinstance(exception, BusinessLogicError):
            ErrorDialog.show_error(
                parent, "操作错误", str(exception), "请检查输入数据是否正确"
            )
        elif isinstance(exception, PeakSpeedError):
            ErrorDialog.show_error(parent, "错误", str(exception))
        else:
            ErrorDialog.show_error(
                parent,
                "未知错误",
                "发生了未预期的错误",
                f"详细信息：{type(exception).__name__}: {str(exception)}",
            )

    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, message: str):
        """
        显示警告对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 警告消息
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        logger.warning(f"{title}: {message}")

    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, message: str):
        """
        显示信息对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 信息内容
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        logger.info(f"{title}: {message}")

    @staticmethod
    def show_success(parent: Optional[QWidget], message: str):
        """
        显示成功消息对话框

        Args:
            parent: 父窗口
            message: 成功消息
        """
        ErrorDialog.show_info(parent, "成功", message)

    @staticmethod
    def ask_confirmation(
        parent: Optional[QWidget], title: str, message: str, details: Optional[str] = None
    ) -> bool:
        """
        显示确认对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 确认消息
            details: 详细信息（可选）

        Returns:
            用户是否确认（True/False）
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if details:
            msg_box.setInformativeText(details)

        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes


class LogViewerDialog(QDialog):
    """日志查看器对话框"""

    def __init__(self, parent: Optional[QWidget] = None, log_file_path: Optional[str] = None):
        """
        初始化日志查看器

        Args:
            parent: 父窗口
            log_file_path: 日志文件路径
        """
        super().__init__(parent)
        self.log_file_path = log_file_path
        self._init_ui()
        self._load_logs()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("日志查看器")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        layout = QVBoxLayout()

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_text)

        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self._load_logs)
        layout.addWidget(refresh_button)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def _load_logs(self):
        """加载日志内容"""
        if not self.log_file_path:
            self.log_text.setPlainText("未指定日志文件路径")
            return

        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.log_text.setPlainText(content)

            # 滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except FileNotFoundError:
            self.log_text.setPlainText("日志文件不存在")
        except Exception as e:
            self.log_text.setPlainText(f"读取日志文件失败: {str(e)}")
