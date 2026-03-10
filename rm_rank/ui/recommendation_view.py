"""推荐视图"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QGroupBox, QHeaderView, QMessageBox, QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from rm_rank.engines import RecommendationEngine
from rm_rank.repositories import GarageRepository
from rm_rank.logger import logger


# 联赛等级配置：(极限组数量, 性能组数量, 运动组数量)
LEAGUE_CONFIGS = {
    "新秀联赛1": (2, 2, 2),
    "新秀联赛2": (3, 3, 3),
    "新秀联赛3": (4, 4, 4),
    "新秀联赛4": (5, 5, 5),
    "精英联赛1": (6, 6, 6),
    "精英联赛2": (7, 6, 6),  # 极限组+1
    "精英联赛3": (7, 7, 6),  # 性能组+1
    "精英联赛4": (7, 7, 7),  # 运动组+1
    "精英联赛5": (8, 7, 7),  # 极限组+1
    "精英联赛6": (8, 8, 7),  # 性能组+1
    "精英联赛7": (8, 8, 8),  # 运动组+1
    "精英联赛8": (9, 8, 8),  # 极限组+1
    "精英联赛9": (9, 9, 8),  # 性能组+1
    "巅峰联赛": (9, 9, 9),
}


class RecommendationView(QWidget):
    """推荐视图组件"""
    
    def __init__(self, recommendation_engine: RecommendationEngine, garage_repo: GarageRepository):
        super().__init__()
        self.recommendation_engine = recommendation_engine
        self.garage_repo = garage_repo
        self._updating_from_league = False  # 防止循环更新
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_group = QGroupBox("推荐设置")
        control_layout = QHBoxLayout()
        
        # 联赛等级选择
        control_layout.addWidget(QLabel("最高联赛等级:"))
        self.league_combo = QComboBox()
        for league_name in LEAGUE_CONFIGS.keys():
            self.league_combo.addItem(league_name, league_name)
        self.league_combo.setCurrentText("精英联赛5")  # 默认精英联赛5
        self.league_combo.currentIndexChanged.connect(self.on_league_changed)
        control_layout.addWidget(self.league_combo)
        
        control_layout.addSpacing(20)
        
        # 计分车辆选择
        control_layout.addWidget(QLabel("计分车辆:"))
        self.vehicle_count_combo = QComboBox()
        # 添加所有可能的计分车辆配置
        for league_name, (extreme, performance, sports) in LEAGUE_CONFIGS.items():
            total = extreme + performance + sports
            display_text = f"{total}台 (极限{extreme}+性能{performance}+运动{sports})"
            # 使用元组作为data，方便后续使用
            self.vehicle_count_combo.addItem(display_text, (extreme, performance, sports))
        
        # 设置默认值为精英联赛5的配置
        default_config = LEAGUE_CONFIGS["精英联赛5"]
        for i in range(self.vehicle_count_combo.count()):
            if self.vehicle_count_combo.itemData(i) == default_config:
                self.vehicle_count_combo.setCurrentIndex(i)
                break
        
        control_layout.addWidget(self.vehicle_count_combo)
        
        control_layout.addSpacing(20)
        
        self.recommend_button = QPushButton("生成推荐")
        self.recommend_button.clicked.connect(self.generate_all_recommendations)
        control_layout.addWidget(self.recommend_button)
        
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 统计信息
        self.stats_label = QLabel("请点击'生成推荐'按钮")
        self.stats_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.stats_label)
        
        # 说明文字
        note_label = QLabel(
            "圈速总和 (数值越小越快) - 此表仅作大致参考，具体情况与技术有直接关系"
        )
        note_label.setStyleSheet(
            "color: #666; font-size: 12px; padding: 5px 10px; "
            "background-color: #f0f0f0; border-radius: 3px;"
        )
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 全部推荐标签页
        self.all_table = self.create_table()
        self.tabs.addTab(self.all_table, "全部推荐")
        
        # 极限组标签页
        self.extreme_table = self.create_table()
        self.tabs.addTab(self.extreme_table, "极限组")
        
        # 性能组标签页
        self.performance_table = self.create_table()
        self.tabs.addTab(self.performance_table, "性能组")
        
        # 运动组标签页
        self.sports_table = self.create_table()
        self.tabs.addTab(self.sports_table, "运动组")
        
        layout.addWidget(self.tabs)
    
    def create_table(self):
        """创建表格"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["排名", "车型", "组别", "阶数", "圈速总和(秒)"])
        
        # 设置表格属性
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 优化列宽分配
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 排名列固定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 车型列拉伸
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 组别列固定
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 阶数列固定
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 圈速列固定
        
        table.setColumnWidth(0, 50)   # 排名列
        table.setColumnWidth(2, 80)   # 组别列
        table.setColumnWidth(3, 60)   # 阶数列
        table.setColumnWidth(4, 120)  # 圈速列
        
        return table
        
    def on_league_changed(self, index):
        """联赛等级改变时自动更新计分车辆"""
        if self._updating_from_league:
            return
        
        self._updating_from_league = True
        
        league_name = self.league_combo.currentData()
        if league_name in LEAGUE_CONFIGS:
            config = LEAGUE_CONFIGS[league_name]
            # 在计分车辆下拉框中找到对应的配置
            for i in range(self.vehicle_count_combo.count()):
                if self.vehicle_count_combo.itemData(i) == config:
                    self.vehicle_count_combo.setCurrentIndex(i)
                    break
        
        self._updating_from_league = False
    
    def refresh(self):
        """刷新视图"""
        # 推荐视图不需要自动刷新，由用户手动触发
        pass
    
    def generate_all_recommendations(self):
        """生成所有组别的推荐"""
        try:
            # 获取车库车辆
            garage_vehicles = self.garage_repo.get_all_garage_vehicles()
            
            if not garage_vehicles:
                QMessageBox.warning(self, "警告", "车库为空，请先添加车辆")
                return
            
            # 获取用户选择的计分车辆配置
            vehicle_config = self.vehicle_count_combo.currentData()
            if not vehicle_config:
                QMessageBox.warning(self, "警告", "无效的计分车辆配置")
                return
            
            extreme_count, performance_count, sports_count = vehicle_config
            
            # 生成全部推荐（使用自定义数量）
            all_result = self.recommendation_engine.recommend_all_categories_custom(
                garage_vehicles,
                extreme_count=extreme_count,
                performance_count=performance_count,
                sports_count=sports_count
            )
            
            # 生成运动组推荐
            sports_result = self.recommendation_engine.recommend_optimal_combination(
                garage_vehicles, 
                "运动组",
                limit=sports_count
            )
            
            # 生成性能组推荐
            performance_result = self.recommendation_engine.recommend_optimal_combination(
                garage_vehicles,
                "性能组",
                limit=performance_count
            )
            
            # 生成极限组推荐
            extreme_result = self.recommendation_engine.recommend_optimal_combination(
                garage_vehicles,
                "极限组",
                limit=extreme_count
            )
            
            # 更新统计信息
            garage_count = len(garage_vehicles)
            self.stats_label.setText(
                f"车库共有 {garage_count} 辆车 | "
                f"全部推荐: {all_result.count}辆 ({all_result.total_lap_time:.1f} s) | "
                f"运动组: {sports_result.count}辆 ({sports_result.total_lap_time:.1f} s) | "
                f"性能组: {performance_result.count}辆 ({performance_result.total_lap_time:.1f} s) | "
                f"极限组: {extreme_result.count}辆 ({extreme_result.total_lap_time:.1f} s)"
            )
            
            # 更新各个表格（全部推荐不高亮前3名）
            self.update_table(self.all_table, all_result, highlight_top3=False)
            self.update_table(self.sports_table, sports_result)
            self.update_table(self.performance_table, performance_result)
            self.update_table(self.extreme_table, extreme_result)
            
            # 更新标签页标题，显示数量
            self.tabs.setTabText(0, f"全部推荐 ({all_result.count})")
            self.tabs.setTabText(1, f"极限组 ({extreme_result.count})")
            self.tabs.setTabText(2, f"性能组 ({performance_result.count})")
            self.tabs.setTabText(3, f"运动组 ({sports_result.count})")
                
        except Exception as e:
            logger.error(f"生成推荐失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"生成推荐失败：{str(e)}")
    
    def update_table(self, table, result, highlight_top3=True):
        """更新表格数据
        
        Args:
            table: 要更新的表格
            result: 推荐结果
            highlight_top3: 是否高亮显示前3名，默认True
        """
        # 清空表格
        table.setRowCount(0)
        
        # 填充推荐数据
        for ranked_vehicle in result.vehicles:
            row = table.rowCount()
            table.insertRow(row)
            
            v = ranked_vehicle.vehicle
            
            # 创建表格项并设置居中对齐
            rank_item = QTableWidgetItem(str(ranked_vehicle.rank))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_item = QTableWidgetItem(v.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            category_item = QTableWidgetItem(v.category.value)
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            tier_item = QTableWidgetItem(str(v.tier))
            tier_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lap_time_item = QTableWidgetItem(f"{v.lap_time:.1f} s")
            lap_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 高亮显示前3名（如果启用）
            if highlight_top3 and ranked_vehicle.rank <= 3:
                color = QColor(255, 255, 200)  # 浅黄色
                rank_item.setBackground(color)
                name_item.setBackground(color)
                category_item.setBackground(color)
                tier_item.setBackground(color)
                lap_time_item.setBackground(color)
            
            table.setItem(row, 0, rank_item)
            table.setItem(row, 1, name_item)
            table.setItem(row, 2, category_item)
            table.setItem(row, 3, tier_item)
            table.setItem(row, 4, lap_time_item)
