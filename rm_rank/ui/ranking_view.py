"""排行榜视图"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QLabel, QLineEdit, QPushButton, QHeaderView, QTabWidget
)
from PyQt6.QtCore import Qt

from rm_rank.engines import RankingEngine
from rm_rank.logger import logger


class RankingView(QWidget):
    """排行榜视图组件"""
    
    def __init__(self, ranking_engine: RankingEngine):
        super().__init__()
        self.ranking_engine = ranking_engine
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入车型名称...")
        self.search_input.textChanged.connect(self.apply_search)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 总榜标签页
        self.all_table = self.create_table()
        self.tabs.addTab(self.all_table, "总榜")
        
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
        
        # 说明文字（标签页下方）
        note_label = QLabel("💡 圈速总和 (数值越小越快) - 此表仅作大致参考，具体情况与技术有直接关系")
        note_label.setStyleSheet(
            "color: #555; font-size: 12px; padding: 8px 15px; "
            "background-color: #fffbea; border-left: 3px solid #f59e0b; "
            "border-radius: 3px; margin: 5px 0px;"
        )
        layout.addWidget(note_label)
        
        # 初始加载数据
        self.refresh()
    
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
        
    def refresh(self):
        """刷新排行榜数据"""
        try:
            # 获取各个排行榜数据
            all_ranking = self.ranking_engine.generate_ranking(None)
            sports_ranking = self.ranking_engine.generate_ranking("运动组")
            performance_ranking = self.ranking_engine.generate_ranking("性能组")
            extreme_ranking = self.ranking_engine.generate_ranking("极限组")
            
            # 更新各个表格
            self.update_table(self.all_table, all_ranking)
            self.update_table(self.sports_table, sports_ranking)
            self.update_table(self.performance_table, performance_ranking)
            self.update_table(self.extreme_table, extreme_ranking)
            
            # 更新标签页标题，显示数量
            self.tabs.setTabText(0, f"总榜 ({len(all_ranking)})")
            self.tabs.setTabText(1, f"极限组 ({len(extreme_ranking)})")
            self.tabs.setTabText(2, f"性能组 ({len(performance_ranking)})")
            self.tabs.setTabText(3, f"运动组 ({len(sports_ranking)})")
            
            # 应用搜索过滤
            self.apply_search()
            
        except Exception as e:
            logger.error(f"刷新排行榜失败: {str(e)}", exc_info=True)
    
    def update_table(self, table, ranking):
        """更新表格数据"""
        # 清空表格
        table.setRowCount(0)
        
        # 填充数据
        for ranked_vehicle in ranking:
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
            
            table.setItem(row, 0, rank_item)
            table.setItem(row, 1, name_item)
            table.setItem(row, 2, category_item)
            table.setItem(row, 3, tier_item)
            table.setItem(row, 4, lap_time_item)
            
    def apply_search(self):
        """应用搜索过滤"""
        search_text = self.search_input.text().lower()
        
        # 对所有标签页的表格应用搜索
        for table in [self.all_table, self.sports_table, self.performance_table, self.extreme_table]:
            for row in range(table.rowCount()):
                name_item = table.item(row, 1)
                if name_item:
                    should_show = search_text in name_item.text().lower()
                    table.setRowHidden(row, not should_show)
