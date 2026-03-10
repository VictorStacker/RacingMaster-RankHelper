"""
数据更新进度对话框

显示数据更新进度和状态。
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import Optional, Callable

from rm_rank.logger import get_logger

logger = get_logger(__name__)


class CrawlerThread(QThread):
    """爬虫工作线程"""

    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度值, 状态消息
    finished_signal = pyqtSignal(bool, str)  # 成功/失败, 结果消息
    error_occurred = pyqtSignal(str)  # 错误消息

    def __init__(self, crawler_func: Callable):
        """
        初始化爬虫线程

        Args:
            crawler_func: 爬虫函数，应该返回 (success: bool, message: str, data: list)
        """
        super().__init__()
        self.crawler_func = crawler_func
        self._is_cancelled = False

    def run(self):
        """执行爬虫任务"""
        try:
            self.progress_updated.emit(10, "正在连接网站...")

            if self._is_cancelled:
                self.finished_signal.emit(False, "操作已取消")
                return

            self.progress_updated.emit(30, "正在加载页面...")

            if self._is_cancelled:
                self.finished_signal.emit(False, "操作已取消")
                return

            self.progress_updated.emit(50, "正在解析数据...")

            # 执行爬虫函数
            success, message, data = self.crawler_func()

            if self._is_cancelled:
                self.finished_signal.emit(False, "操作已取消")
                return

            if success:
                self.progress_updated.emit(80, "正在保存数据...")
                self.progress_updated.emit(100, "完成")
                self.finished_signal.emit(True, f"成功获取 {len(data)} 条数据")
            else:
                self.error_occurred.emit(message)
                self.finished_signal.emit(False, message)

        except Exception as e:
            error_msg = f"获取失败: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.finished_signal.emit(False, error_msg)

    def cancel(self):
        """取消爬虫任务"""
        self._is_cancelled = True


class ProgressDialog(QDialog):
    """数据更新进度对话框"""

    def __init__(self, parent=None, crawler_func: Optional[Callable] = None):
        """
        初始化进度对话框

        Args:
            parent: 父窗口
            crawler_func: 爬虫函数
        """
        super().__init__(parent)
        self.crawler_func = crawler_func
        self.crawler_thread: Optional[CrawlerThread] = None
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("数据更新进度")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()

        # 状态标签
        self.status_label = QLabel("准备开始...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 详细信息文本框
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        layout.addWidget(self.detail_text)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def start_crawling(self):
        """开始获取数据"""
        if not self.crawler_func:
            self._add_detail("错误：未设置爬虫函数")
            return

        self._add_detail("开始获取数据...")
        self.cancel_button.setEnabled(True)

        # 创建并启动爬虫线程
        self.crawler_thread = CrawlerThread(self.crawler_func)
        self.crawler_thread.progress_updated.connect(self._on_progress_updated)
        self.crawler_thread.finished_signal.connect(self._on_finished)
        self.crawler_thread.error_occurred.connect(self._on_error)
        self.crawler_thread.start()

    def _on_progress_updated(self, value: int, message: str):
        """
        处理进度更新

        Args:
            value: 进度值 (0-100)
            message: 状态消息
        """
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self._add_detail(f"[{value}%] {message}")

    def _on_finished(self, success: bool, message: str):
        """
        处理获取完成

        Args:
            success: 是否成功
            message: 结果消息
        """
        self.cancel_button.setText("关闭")
        self.cancel_button.setEnabled(True)

        if success:
            self.status_label.setText("✓ " + message)
            self._add_detail(f"成功: {message}")
        else:
            self.status_label.setText("✗ " + message)
            self._add_detail(f"失败: {message}")

    def _on_error(self, error_message: str):
        """
        处理错误

        Args:
            error_message: 错误消息
        """
        self._add_detail(f"错误: {error_message}")

    def _on_cancel(self):
        """处理取消按钮点击"""
        if self.crawler_thread and self.crawler_thread.isRunning():
            self._add_detail("正在取消...")
            self.cancel_button.setEnabled(False)
            self.crawler_thread.cancel()
            self.crawler_thread.wait()
            self._add_detail("已取消")
        self.accept()

    def _add_detail(self, message: str):
        """
        添加详细信息

        Args:
            message: 消息内容
        """
        self.detail_text.append(message)
        # 滚动到底部
        scrollbar = self.detail_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
