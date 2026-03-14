"""主窗口"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox, QFileDialog, QDialog
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

from rm_rank.ui.ranking_view import RankingView
from rm_rank.ui.garage_view import GarageView
from rm_rank.ui.recommendation_view import RecommendationView
from rm_rank.ui.dialogs import ErrorDialog
from rm_rank.ui.progress_dialog import ProgressDialog
from rm_rank.ui.account_dialog import AccountManagementDialog
from rm_rank.ui.account_selection_dialog import AccountSelectionDialog
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
        
        # 初始化调教服务
        from rm_rank.tuning import TuningService, DatabaseManager, TuningCache, TuningParser
        self.tuning_db_manager = DatabaseManager(str(config.TUNING_DATABASE_PATH))
        self.tuning_cache = TuningCache()
        self.tuning_parser = TuningParser()
        self.tuning_service = TuningService(self.tuning_db_manager, self.tuning_cache)
        
        self.validator = DataValidator()
        
        # 初始化导入导出
        self.exporter = DataExporter(
            self.vehicle_repo, self.garage_repo, self.combination_repo, self.account_repo
        )
        self.importer = DataImporter(
            self.vehicle_repo, self.garage_repo, self.combination_repo, self.validator, self.account_repo
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
        
        import_garage_action = QAction("导入车库数据(&G)", self)
        import_garage_action.triggered.connect(self.import_garage)
        import_menu.addAction(import_garage_action)
        
        # 导出子菜单
        export_menu = file_menu.addMenu("导出(&E)")
        
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
        
        data_menu.addSeparator()
        
        reset_tuning_action = QAction("重置车辆数据库(&R)", self)
        reset_tuning_action.triggered.connect(self.reset_tuning_database)
        data_menu.addAction(reset_tuning_action)
        
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
        self.garage_view = GarageView(self.garage_repo, self.vehicle_repo, self.account_repo, self.ranking_engine)
        self.garage_view.account_changed.connect(self.on_account_changed)
        self.tabs.addTab(self.garage_view, "我的车库")
        
        # 推荐视图
        self.recommendation_view = RecommendationView(
            self.recommendation_engine, 
            self.garage_repo,
            self.tuning_service
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
                # 使用简单爬虫一键获取所有数据（圈速+调教）
                vehicles, tuning_html = self.crawler.fetch_all_data()
                
                # 保存圈速数据
                self.vehicle_repo.save_vehicles(vehicles)
                
                # 处理调教数据
                tuning_count = 0
                if tuning_html:
                    try:
                        # 解析调教数据
                        tuning_data_list = self.tuning_parser.parse_tuning_data(tuning_html)
                        
                        # 保存到数据库
                        for tuning_data in tuning_data_list:
                            self.tuning_db_manager.save_tuning_data(tuning_data)
                            tuning_count += 1
                        
                        # 清空缓存
                        self.tuning_cache.clear()
                        
                        logger.info(f"成功保存 {tuning_count} 条调教数据")
                    except Exception as e:
                        logger.warning(f"调教数据处理失败: {str(e)}", exc_info=True)
                        # 调教数据失败不影响圈速数据的成功
                
                message = f"成功更新 {len(vehicles)} 条圈速数据"
                if tuning_count > 0:
                    message += f"，{tuning_count} 条调教数据"
                
                return True, message, vehicles
            except Exception as e:
                logger.error(f"更新数据库失败: {str(e)}", exc_info=True)
                return False, str(e), []
        
        # 显示进度对话框
        dialog = ProgressDialog(self, crawler_func)
        dialog.start_crawling()
        result = dialog.exec()
        
        # 刷新所有视图
        self.refresh_all()
        self.update_account_status()
    
    def reset_tuning_database(self):
        """重置车辆数据库"""
        # 获取当前数据统计
        try:
            tuning_count = self.tuning_db_manager.get_tuning_data_count()
            vehicle_count = self.vehicle_repo.get_vehicle_count()
        except Exception:
            tuning_count = 0
            vehicle_count = 0
        
        # 显示确认对话框
        reply = QMessageBox.warning(
            self,
            "确认重置",
            f"确定要重置车辆数据库吗？\n\n"
            f"当前数据库包含：\n"
            f"• {vehicle_count} 条车辆圈速数据\n"
            f"• {tuning_count} 条调教数据\n\n"
            f"此操作将清空所有车辆相关数据，但不会影响账号和车库数据。\n\n"
            f"重置后建议立即执行'更新数据库'以重新获取最新数据。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            # 重置车辆圈速数据
            cleared_vehicles = self.vehicle_repo.clear_all_vehicles()
            
            # 重置调教数据库
            self.tuning_db_manager.reset_tuning_data()
            
            # 清空缓存
            self.tuning_cache.clear()
            
            # 刷新视图
            self.refresh_all()
            
            # 显示成功消息
            QMessageBox.information(
                self,
                "重置成功",
                f"车辆数据库已成功重置！\n\n"
                f"已清空：\n"
                f"• {cleared_vehicles} 条车辆圈速数据\n"
                f"• {tuning_count} 条调教数据\n\n"
                f"建议现在执行'数据(D) - 更新数据库'以重新获取最新数据。"
            )
            
            self.statusBar().showMessage("车辆数据库已重置", 3000)
            
        except Exception as e:
            logger.error(f"重置车辆数据库失败: {str(e)}", exc_info=True)
            ErrorDialog.show_exception(self, e)
            
    def refresh_all(self):
        """刷新所有视图"""
        self.ranking_view.refresh()
        self.garage_view.load_accounts()
        self.garage_view.refresh()
        self.recommendation_view.refresh()
        self.update_account_status()
        
    def show_about(self):
        """显示关于对话框"""
        from rm_rank import __version__
        QMessageBox.about(
            self,
            "关于",
            f"<h3>巅峰极速车辆数据及排位计分车推荐</h3>"
            f"<p>版本：{__version__}</p>"
            f"<p>一个数据驱动的决策支持工具，帮助玩家在排位赛中选择最优车辆组合。</p>"
            f"<hr>"
            f"<p>数据来源：<a href='https://waylongrank.top/index.html'>阿龙WayLong</a></p>"
            f"<p>开源地址：<a href='https://github.com/VictorStacker/RacingMaster-RankHelper'>GitHub</a></p>"
            f"<p>By 隨緣</p>"
            f"<hr>"
            f"<p style='color: #888; font-size: 11px;'>本工具为非官方第三方工具，与《巅峰极速》官方无关。<br>仅供参考，实际表现与驾驶技术有直接关系。</p>"
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
            import json
            
            # 读取文件以检测格式
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否为多账号格式
            if 'accounts' in data and isinstance(data['accounts'], list):
                # 多账号格式，显示账号选择对话框
                accounts_data = data['accounts']
                
                if not accounts_data:
                    ErrorDialog.show_error(self, "文件中没有账号数据")
                    return
                
                # 显示账号选择对话框
                dialog = AccountSelectionDialog(accounts_data, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_accounts = dialog.get_selected_accounts()
                    
                    if not selected_accounts:
                        ErrorDialog.show_error(self, "未选择任何账号")
                        return
                    
                    # 导入选中的账号
                    count = self.importer.import_garage(Path(file_path), clear_existing=False, selected_accounts=selected_accounts)
                    ErrorDialog.show_success(self, f"成功导入 {count} 辆车辆到车库")
                    self.refresh_all()
            else:
                # 单账号格式，直接导入
                count = self.importer.import_garage(Path(file_path), clear_existing=False)
                ErrorDialog.show_success(self, f"成功导入 {count} 辆车辆到车库")
                self.refresh_all()
                
        except Exception as e:
            ErrorDialog.show_exception(self, e)
    
    def import_all(self):
        """导入所有数据（车库和组合）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入所有数据", "", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            import json
            
            # 读取文件以检测格式
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否为多账号格式
            if 'accounts' in data and isinstance(data['accounts'], list):
                # 多账号格式，显示账号选择对话框
                accounts_data = data['accounts']
                
                if not accounts_data:
                    ErrorDialog.show_error(self, "文件中没有账号数据")
                    return
                
                # 显示账号选择对话框
                dialog = AccountSelectionDialog(accounts_data, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_accounts = dialog.get_selected_accounts()
                    
                    if not selected_accounts:
                        ErrorDialog.show_error(self, "未选择任何账号")
                        return
                    
                    # 导入选中的账号
                    result = self.importer.import_all_accounts(Path(file_path), clear_existing=False, selected_accounts=selected_accounts)
                    
                    # 构建成功消息
                    message = "成功导入数据：\n"
                    for account_name, counts in result.items():
                        message += f"• {account_name}: {counts['garage']} 辆车库车辆, {counts['combination']} 个组合\n"
                    
                    ErrorDialog.show_success(self, message)
                    self.refresh_all()
            else:
                # 单账号格式，显示错误
                ErrorDialog.show_error(self, "此文件不是完整的多账号数据格式，请使用'导入车库数据'功能")
                
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
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出所有数据", "all_data.json", "JSON 文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            self.exporter.export_all(Path(file_path))
            ErrorDialog.show_success(self, f"成功导出所有数据到 {file_path}")
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
