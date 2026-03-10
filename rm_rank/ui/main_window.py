"""主窗口"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

from rm_rank.ui.ranking_view import RankingView
from rm_rank.ui.garage_view import GarageView
from rm_rank.ui.recommendation_view import RecommendationView
from rm_rank.ui.dialogs import ErrorDialog
from rm_rank.ui.progress_dialog import ProgressDialog
from rm_rank.ui.account_dialog import AccountManagementDialog
from rm_rank.repositories import VehicleRepository, GarageRepository, CombinationRepository, AccountRepository
from rm_rank.engines import RankingEngine, RecommendationEngine
from rm_rank.crawler import WebCrawler
from rm_rank.io import DataExporter, DataImporter
from rm_rank.validator import DataValidator
from rm_rank.models.db_models import init_database, get_session
from rm_rank import config
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据库
        init_database()
        
        # 获取数据库会话
        self.session = get_session()
        
        # 初始化仓库和引擎
        self.vehicle_repo = VehicleRepository(self.session)
        self.account_repo = AccountRepository(self.session)
        
        # 确保有默认账号
        self.account_repo.ensure_default_account()
        
        self.garage_repo = GarageRepository(self.session)
        self.combination_repo = CombinationRepository(self.session)
        self.ranking_engine = RankingEngine(self.vehicle_repo)
        self.recommendation_engine = RecommendationEngine(self.ranking_engine)
        
        # 优先使用简单爬虫（不需要浏览器），如果失败则尝试 Playwright
        from rm_rank.crawler import SimpleCrawler
        self.crawler = SimpleCrawler()
        self.use_simple_crawler = True
        
        self.validator = DataValidator()
        
        # 初始化导入导出
        self.exporter = DataExporter(
            self.vehicle_repo, self.garage_repo, self.combination_repo
        )
        self.importer = DataImporter(
            self.vehicle_repo, self.garage_repo, self.combination_repo, self.validator
        )
        
        self.init_ui()
        self.update_account_status()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("巅峰极速车辆数据及排位计分车推荐")
        self.setGeometry(100, 100, 800, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建中央部件
        self.create_central_widget()
        
        # 创建状态栏
        self.create_status_bar()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 导入子菜单
        import_menu = file_menu.addMenu("导入(&I)")
        
        import_vehicles_action = QAction("导入车辆数据(&V)", self)
        import_vehicles_action.triggered.connect(self.import_vehicles)
        import_menu.addAction(import_vehicles_action)
        
        import_garage_action = QAction("导入车库数据(&G)", self)
        import_garage_action.triggered.connect(self.import_garage)
        import_menu.addAction(import_garage_action)
        
        # 导出子菜单
        export_menu = file_menu.addMenu("导出(&E)")
        
        export_vehicles_action = QAction("导出车辆数据(&V)", self)
        export_vehicles_action.triggered.connect(self.export_vehicles)
        export_menu.addAction(export_vehicles_action)
        
        export_garage_action = QAction("导出车库数据(&G)", self)
        export_garage_action.triggered.connect(self.export_garage)
        export_menu.addAction(export_garage_action)
        
        export_all_action = QAction("导出所有数据(&A)", self)
        export_all_action.triggered.connect(self.export_all)
        export_menu.addAction(export_all_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 数据菜单
        data_menu = menubar.addMenu("数据(&D)")
        
        crawl_action = QAction("更新数据库(&U)", self)
        crawl_action.setShortcut("Ctrl+R")
        crawl_action.triggered.connect(self.crawl_data)
        data_menu.addAction(crawl_action)
        
        # 账号菜单
        account_menu = menubar.addMenu("账号(&A)")
        
        manage_accounts_action = QAction("管理账号(&M)", self)
        manage_accounts_action.setShortcut("Ctrl+M")
        manage_accounts_action.triggered.connect(self.manage_accounts)
        account_menu.addAction(manage_accounts_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        # 工具栏已移除所有按钮
        pass
        
    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 排行榜视图
        self.ranking_view = RankingView(self.ranking_engine)
        self.tabs.addTab(self.ranking_view, "车辆排行榜")
        
        # 车库视图
        self.garage_view = GarageView(self.garage_repo, self.vehicle_repo, self.account_repo)
        self.garage_view.account_changed.connect(self.on_account_changed)
        self.tabs.addTab(self.garage_view, "我的车库")
        
        # 推荐视图
        self.recommendation_view = RecommendationView(
            self.recommendation_engine, 
            self.garage_repo
        )
        self.tabs.addTab(self.recommendation_view, "排位车辆推荐")
        
        layout.addWidget(self.tabs)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = self.statusBar()
        status_bar.showMessage("就绪")
        
        # 在右侧添加数据来源标签
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        
        credit_label = QLabel()
        credit_label.setText('数据库支持：<a href="https://waylongrank.top/index.html" style="color: #2196F3; text-decoration: none;">阿龙WayLong</a>')
        credit_label.setOpenExternalLinks(True)  # 允许打开外部链接
        credit_label.setToolTip("点击访问阿龙WayLong的网站")
        credit_label.setStyleSheet("padding: 2px 10px;")
        
        # 添加到状态栏右侧（永久显示）
        status_bar.addPermanentWidget(credit_label)
        
    def crawl_data(self):
        """更新数据库"""
        # 先显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认更新",
            "确定要从网站更新车辆数据吗？\n\n这将从数据源获取最新的车辆信息并更新到本地数据库。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        def crawler_func():
            """爬虫函数，返回 (success, message, data)"""
            try:
                # 使用简单爬虫（不需要浏览器）
                vehicles = self.crawler.fetch_all_vehicles()
                self.vehicle_repo.save_vehicles(vehicles)
                return True, f"成功更新 {len(vehicles)} 条数据", vehicles
            except Exception as e:
                logger.error(f"更新数据库失败: {str(e)}", exc_info=True)
                return False, str(e), []
        
        # 显示进度对话框
        dialog = ProgressDialog(self, crawler_func)
        dialog.start_crawling()
        result = dialog.exec()
        
        # 刷新所有视图
        self.refresh_all()
        self.statusBar().showMessage("数据更新完成", 3000)
            
    def refresh_all(self):
        """刷新所有视图"""
        self.ranking_view.refresh()
        self.garage_view.refresh()
        self.recommendation_view.refresh()
        self.statusBar().showMessage("已刷新", 3000)
        
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h3>巅峰极速车辆数据及排位计分车推荐</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>一个数据驱动的决策支持工具，帮助玩家优化排位赛车辆选择。</p>"
        )
    
    def import_vehicles(self):
        """导入车辆数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入车辆数据", "", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            count = self.importer.import_vehicles(Path(file_path), replace=True)
            ErrorDialog.show_success(self, f"成功导入 {count} 辆车辆数据")
            self.refresh_all()
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def import_garage(self):
        """导入车库数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入车库数据", "", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            count = self.importer.import_garage(Path(file_path), clear_existing=False)
            ErrorDialog.show_success(self, f"成功导入 {count} 辆车辆到车库")
            self.refresh_all()
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def export_vehicles(self):
        """导出车辆数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出车辆数据", "vehicles.json", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            self.exporter.export_vehicles(Path(file_path))
            ErrorDialog.show_success(self, f"成功导出车辆数据到 {file_path}")
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def export_garage(self):
        """导出车库数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出车库数据", "garage.json", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            self.exporter.export_garage(Path(file_path))
            ErrorDialog.show_success(self, f"成功导出车库数据到 {file_path}")
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def export_all(self):
        """导出所有数据"""
        directory = QFileDialog.getExistingDirectory(self, "选择导出目录")
        
        if not directory:
            return
        
        try:
            files = self.exporter.export_all(Path(directory))
            message = "成功导出所有数据：\n"
            for key, path in files.items():
                message += f"• {key}: {path.name}\n"
            ErrorDialog.show_success(self, message)
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def manage_accounts(self):
        """打开账号管理对话框"""
        dialog = AccountManagementDialog(self.account_repo, self)
        dialog.account_changed.connect(self.on_account_changed)
        # 连接账号列表更新信号，刷新车库视图的账号下拉框
        dialog.accounts_updated.connect(self.garage_view.load_accounts)
        dialog.exec()
    
    def on_account_changed(self, account_id: int):
        """账号切换时的处理"""
        # 更新状态栏
        self.update_account_status()
        
        # 刷新所有视图
        self.refresh_all()
    
    def update_account_status(self):
        """更新状态栏显示当前账号"""
        try:
            active_account = self.account_repo.get_active_account()
            if active_account:
                self.statusBar().showMessage(f"当前账号: {active_account.name}")
            else:
                self.statusBar().showMessage("未选择账号")
        except Exception as e:
            logger.error(f"更新账号状态失败: {str(e)}")
            self.statusBar().showMessage("就绪")


def run_gui():
    """运行图形界面"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
