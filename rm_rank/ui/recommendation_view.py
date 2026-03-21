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

# 周次规则配置：每个组别在不同周次下的计分车辆数
# 格式：(第1-2周, 第3-4周, 第5-7周)
WEEK_SCORING_RULES = {
    "极限组": (5, 7, 9),
    "性能组": (5, 7, 9),
    "运动组": (5, 7, 9),
}

# 背景色配置：对应三档计分车辆数
SCORING_COLORS = [
    QColor(200, 255, 200),  # 第1档：浅绿色 (1-2周)
    QColor(200, 230, 255),  # 第2档：浅蓝色 (3-4周)
    QColor(230, 230, 230),  # 第3档：浅灰色 (5-7周)
]

# 验证颜色配置
assert len(SCORING_COLORS) == 3, "SCORING_COLORS 必须包含3种颜色"


def build_display_rows(ranked_vehicles):
    """生成推荐页显示顺序。

    规则：
    - 推荐序保持原始结果中的 rank
    - 组内排名颜色按原始结果中的组内位置计算
    - 已标记休息的车辆仅在显示时稳定下沉到列表底部
    """
    category_counters = {
        "极限组": 0,
        "性能组": 0,
        "运动组": 0,
    }
    rows = []

    for ranked_vehicle in ranked_vehicles:
        category_name = ranked_vehicle.vehicle.category.value
        category_counters[category_name] += 1
        rows.append(
            {
                "ranked_vehicle": ranked_vehicle,
                "category_rank": category_counters[category_name],
                "is_resting": getattr(ranked_vehicle.vehicle, "is_resting", False),
            }
        )

    active_rows = [row for row in rows if not row["is_resting"]]
    resting_rows = [row for row in rows if row["is_resting"]]
    return active_rows + resting_rows


def get_scoring_color(category_name: str, category_rank: int) -> QColor:
    """根据组别和组别内排名获取背景色
    
    Args:
        category_name: 组别名称（"极限组"/"性能组"/"运动组"）
        category_rank: 车辆在该组别内的排名位置（从1开始）
    
    Returns:
        QColor对象，如果不在计分范围内则返回默认白色
    """
    if category_rank <= 0:
        logger.warning(f"无效的组别内排名: {category_rank}")
        return QColor(255, 255, 255)  # 白色
    
    if category_name not in WEEK_SCORING_RULES:
        logger.warning(f"未知组别: {category_name}")
        return QColor(255, 255, 255)  # 白色
    
    tier1, tier2, tier3 = WEEK_SCORING_RULES[category_name]
    
    if category_rank <= tier1:
        return SCORING_COLORS[0]  # 第1档
    elif category_rank <= tier2:
        return SCORING_COLORS[1]  # 第2档
    elif category_rank <= tier3:
        return SCORING_COLORS[2]  # 第3档
    else:
        return QColor(255, 255, 255)  # 白色


class RecommendationView(QWidget):
    """推荐视图组件"""
    
    def __init__(self, recommendation_engine: RecommendationEngine, garage_repo: GarageRepository, tuning_service=None):
        super().__init__()
        self.recommendation_engine = recommendation_engine
        self.garage_repo = garage_repo
        self.tuning_service = tuning_service  # 调教服务（可选）
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
        
        # 读取上次使用的联赛等级，默认精英联赛5
        from rm_rank.config import load_preferences
        prefs = load_preferences()
        saved_league = prefs.get("last_league", "精英联赛5")
        self.league_combo.setCurrentText(saved_league)
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
            "圈速总和 (数值越小越快) - 已跑够车辆会在推荐页置底显示，但保留原始推荐序"
        )
        note_label.setStyleSheet(
            "color: #666; font-size: 12px; padding: 5px 10px; "
            "background-color: #f0f0f0; border-radius: 3px;"
        )
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 全部推荐标签页（保持原有5列）
        self.all_table = self.create_table(include_category=True, include_tuning=False)
        self.tabs.addTab(self.all_table, "全部推荐")
        
        # 极限组标签页（4列+调教推荐）
        self.extreme_table = self.create_table(include_category=False, include_tuning=True)
        self.tabs.addTab(self.extreme_table, "极限组")
        
        # 性能组标签页（4列+调教推荐）
        self.performance_table = self.create_table(include_category=False, include_tuning=True)
        self.tabs.addTab(self.performance_table, "性能组")
        
        # 运动组标签页（4列+调教推荐）
        self.sports_table = self.create_table(include_category=False, include_tuning=True)
        self.tabs.addTab(self.sports_table, "运动组")
        
        layout.addWidget(self.tabs)
        
        # 联赛计分车辆数规则说明（放在表格下方）
        scoring_info_label = QLabel(
            "联赛计分车辆数规则：\n"
            "• 第1-2周：每组5辆（极限组5辆、性能组5辆、运动组5辆，总计15辆）\n"
            "• 第3-4周：每组7辆（极限组7辆、性能组7辆、运动组7辆，总计21辆）\n"
            "• 第5-7周：每组9辆（极限组9辆、性能组9辆、运动组9辆，总计27辆）\n"
            "表格背景色根据车辆在其所属组别内的排名位置设置"
        )
        scoring_info_label.setStyleSheet(
            "color: #333; font-size: 12px; padding: 8px 10px; "
            "background-color: #f5f5f5; border-radius: 3px; "
            "border: 1px solid #ddd;"
        )
        scoring_info_label.setWordWrap(True)
        layout.addWidget(scoring_info_label)
    
    def create_table(self, include_category=True, include_tuning=False):
        """创建表格
        
        Args:
            include_category: 是否包含"组别"列
            include_tuning: 是否包含"调教推荐"列
        """
        table = QTableWidget()
        
        # 根据参数设置列数和标题
        if include_category and not include_tuning:
            # 全部推荐：推荐序、车型、组别、阶数、圈速总和
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["推荐序", "车型", "组别", "阶数", "圈速总和(秒)"])
        elif not include_category and include_tuning:
            # 分组标签页：推荐序、车型、阶数、圈速、调教推荐
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["推荐序", "车型", "阶数", "圈速(秒)", "调教推荐"])
        else:
            # 默认：推荐序、车型、组别、阶数、圈速总和
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["推荐序", "车型", "组别", "阶数", "圈速总和(秒)"])
        
        # 设置表格属性
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 优化列宽分配
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 排名列固定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 车型列拉伸
        
        if include_category and not include_tuning:
            # 全部推荐表格
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 组别列固定
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 阶数列固定
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 圈速列固定
            
            table.setColumnWidth(0, 50)   # 排名列
            table.setColumnWidth(2, 80)   # 组别列
            table.setColumnWidth(3, 60)   # 阶数列
            table.setColumnWidth(4, 120)  # 圈速列
        elif not include_category and include_tuning:
            # 分组标签页表格
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 阶数列固定
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 圈速列固定
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 调教推荐列拉伸
            
            table.setColumnWidth(0, 50)   # 排名列
            table.setColumnWidth(2, 60)   # 阶数列
            table.setColumnWidth(3, 100)  # 圈速列
            
            # 设置调教列支持文本换行
            table.setWordWrap(True)
        
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
            
            # 保存用户选择
            from rm_rank.config import load_preferences, save_preferences
            prefs = load_preferences()
            prefs["last_league"] = league_name
            save_preferences(prefs)
        
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
            resting_selected_count = sum(
                1
                for ranked_vehicle in all_result.vehicles
                if getattr(ranked_vehicle.vehicle, "is_resting", False)
            )
            self.stats_label.setText(
                f"车库共有 {garage_count} 辆车 | "
                f"全部推荐: {all_result.count}辆 ({all_result.total_lap_time:.1f} s) | "
                f"运动组: {sports_result.count}辆 ({sports_result.total_lap_time:.1f} s) | "
                f"性能组: {performance_result.count}辆 ({performance_result.total_lap_time:.1f} s) | "
                f"极限组: {extreme_result.count}辆 ({extreme_result.total_lap_time:.1f} s) | "
                f"已标记休息: {resting_selected_count}辆"
            )
            
            # 更新各个表格
            self.update_table(self.all_table, all_result, include_category=True, include_tuning=False)
            self.update_table(self.sports_table, sports_result, include_category=False, include_tuning=True)
            self.update_table(self.performance_table, performance_result, include_category=False, include_tuning=True)
            self.update_table(self.extreme_table, extreme_result, include_category=False, include_tuning=True)
            
            # 更新标签页标题，显示数量
            self.tabs.setTabText(0, f"全部推荐 ({all_result.count})")
            self.tabs.setTabText(1, f"极限组 ({extreme_result.count})")
            self.tabs.setTabText(2, f"性能组 ({performance_result.count})")
            self.tabs.setTabText(3, f"运动组 ({sports_result.count})")
                
        except Exception as e:
            logger.error(f"生成推荐失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"生成推荐失败：{str(e)}")
    
    def update_table(self, table, result, include_category=True, include_tuning=False):
        """更新表格数据
        
        Args:
            table: 要更新的表格
            result: 推荐结果
            include_category: 是否包含"组别"列
            include_tuning: 是否包含"调教推荐"列
        """
        # 清空表格
        table.setRowCount(0)
        
        # 填充推荐数据
        for display_row in build_display_rows(result.vehicles):
            row = table.rowCount()
            table.insertRow(row)
            
            ranked_vehicle = display_row["ranked_vehicle"]
            v = ranked_vehicle.vehicle
            category_name = v.category.value
            is_resting = getattr(v, "is_resting", False)
            category_rank = display_row["category_rank"]
            
            # 根据组别内排名确定背景色
            color = get_scoring_color(category_name, category_rank)
            
            # 创建表格项
            col = 0
            
            # 排名列
            rank_item = QTableWidgetItem(str(ranked_vehicle.rank))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_item.setBackground(color)
            table.setItem(row, col, rank_item)
            col += 1
            
            # 车型列
            name_text = f"{v.name}（已跑够）" if is_resting else v.name
            name_item = QTableWidgetItem(name_text)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_item.setBackground(color)
            table.setItem(row, col, name_item)
            col += 1
            
            # 组别列（仅在include_category=True时）
            if include_category:
                category_item = QTableWidgetItem(category_name)
                category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                category_item.setBackground(color)
                table.setItem(row, col, category_item)
                col += 1
            
            # 阶数列
            tier_item = QTableWidgetItem(str(v.tier))
            tier_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tier_item.setBackground(color)
            table.setItem(row, col, tier_item)
            col += 1
            
            # 圈速列
            lap_time_item = QTableWidgetItem(f"{v.lap_time:.1f} s")
            lap_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            lap_time_item.setBackground(color)
            table.setItem(row, col, lap_time_item)
            col += 1
            
            # 调教推荐列（仅在include_tuning=True时）
            if include_tuning:
                tuning_text = self._get_tuning_recommendation(v.name, v.tier)
                tuning_item = QTableWidgetItem(tuning_text)
                tuning_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                tuning_item.setBackground(color)
                table.setItem(row, col, tuning_item)
                
                # 自动调整行高以适应调教数据
                if "\n" in tuning_text:
                    table.resizeRowToContents(row)

            if is_resting:
                self._apply_resting_row_style(table, row)
    
    def _get_tuning_recommendation(self, vehicle_name: str, vehicle_tier: int) -> str:
        """获取调教推荐
        
        Args:
            vehicle_name: 车辆名称
            vehicle_tier: 车辆阶位
            
        Returns:
            调教推荐文本
        """
        if not self.tuning_service:
            return "未启用"
        
        try:
            return self.tuning_service.get_tuning_recommendation(vehicle_name, vehicle_tier)
        except Exception as e:
            logger.error(f"获取调教推荐失败: {str(e)}", exc_info=True)
            return "加载失败"

    @staticmethod
    def _apply_resting_row_style(table, row: int):
        """弱化显示已跑够车辆"""
        resting_foreground = QColor(110, 110, 110)
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setForeground(resting_foreground)
