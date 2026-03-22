"""车库视图"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, QComboBox,
    QDialogButtonBox, QMessageBox, QHeaderView, QTabWidget, QLabel, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from rm_rank.repositories import GarageRepository, VehicleRepository, AccountRepository
from rm_rank.exceptions import BusinessLogicError
from rm_rank.logger import logger


class GarageView(QWidget):
    """车库视图组件"""
    
    # 信号：账号切换时发出
    account_changed = pyqtSignal(int)
    
    def __init__(self, garage_repo: GarageRepository, vehicle_repo: VehicleRepository, account_repo: AccountRepository = None, ranking_engine=None):
        super().__init__()
        self.garage_repo = garage_repo
        self.vehicle_repo = vehicle_repo
        self.account_repo = account_repo
        self.ranking_engine = ranking_engine
        self._updating_account = False  # 防止递归更新
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 账号选择栏（如果提供了account_repo）
        if self.account_repo:
            account_layout = QHBoxLayout()
            
            account_label = QLabel("当前账号:")
            account_label.setStyleSheet("font-weight: bold;")
            account_layout.addWidget(account_label)
            
            self.account_combo = QComboBox()
            self.account_combo.setMinimumWidth(200)
            self.account_combo.currentIndexChanged.connect(self.on_account_changed)
            account_layout.addWidget(self.account_combo)
            
            account_layout.addStretch()
            
            layout.addLayout(account_layout)
            
            # 加载账号列表
            self.load_accounts()
        
        # 工具栏（合并按钮和场次操作为一行）
        toolbar_layout = QHBoxLayout()

        add_button = QPushButton("添加车辆")
        add_button.clicked.connect(self.add_vehicle)
        toolbar_layout.addWidget(add_button)

        self.delete_button = QPushButton("移出车库")
        self.delete_button.clicked.connect(self.toggle_delete_mode)
        toolbar_layout.addWidget(self.delete_button)

        toolbar_layout.addSpacing(15)

        toolbar_layout.addWidget(QLabel("休息场次:"))
        self.global_races_spin = QSpinBox()
        self.global_races_spin.setMinimum(1)
        self.global_races_spin.setMaximum(99)
        self.global_races_spin.setValue(5)
        self.global_races_spin.setSuffix("场")
        toolbar_layout.addWidget(self.global_races_spin)

        apply_global_button = QPushButton("应用")
        apply_global_button.setToolTip("将此场次数应用到当前账号所有车辆")
        apply_global_button.clicked.connect(self.apply_global_races)
        toolbar_layout.addWidget(apply_global_button)

        batch_reset_button = QPushButton("重置")
        batch_reset_button.setToolTip("重置所有车辆的场次计数（新赛季用）")
        batch_reset_button.clicked.connect(self.batch_reset_all_races)
        toolbar_layout.addWidget(batch_reset_button)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # 删除模式标志
        self.delete_mode = False
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 全部车辆标签页
        self.all_table = self.create_table()
        self.tabs.addTab(self.all_table, "全部")
        
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
        note_label = QLabel(
            "💡 圈速总和 (数值越小越快) - 已停用或已跑够场次的车辆会置后并以灰色弱化显示"
        )
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
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["", "总榜", "车型", "组别", "阶数", "圈速(秒)", "状态", "操作"])
        
        # 设置表格属性
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # 优化列宽分配
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 勾选框列固定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # ID列固定
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 车型列拉伸
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 组别列固定
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # 阶数列固定
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 圈速列固定
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 状态列固定
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # 操作列固定

        table.setColumnWidth(0, 28)   # 勾选框列
        table.setColumnWidth(1, 45)   # 总榜列
        table.setColumnWidth(3, 60)   # 组别列
        table.setColumnWidth(4, 40)   # 阶数列
        table.setColumnWidth(5, 80)   # 圈速列
        table.setColumnWidth(6, 90)   # 状态列
        table.setColumnWidth(7, 220)  # 操作列

        # 默认隐藏勾选框列（删除模式才显示）
        table.setColumnHidden(0, True)

        # 双击行触发调整阶数
        table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        return table
        
    def refresh(self):
        """刷新车库数据"""
        try:
            vehicles = self.garage_repo.get_all_garage_vehicles()
            
            # 按圈速排序（从小到大）
            vehicles.sort(key=lambda v: (v.is_effectively_resting, v.lap_time))
            
            # 建立总榜排名映射 {vehicle_id: rank}
            rank_map = {}
            if self.ranking_engine:
                all_ranked = self.ranking_engine.generate_ranking()
                rank_map = {rv.vehicle.id: rv.rank for rv in all_ranked}
            
            # 按组别分类
            from rm_rank.models.data_models import Category
            all_vehicles = vehicles
            sports_vehicles = [v for v in vehicles if v.category == Category.SPORTS]
            performance_vehicles = [v for v in vehicles if v.category == Category.PERFORMANCE]
            extreme_vehicles = [v for v in vehicles if v.category == Category.EXTREME]
            
            # 更新各个表格
            self.update_table(self.all_table, all_vehicles, rank_map)
            self.update_table(self.extreme_table, extreme_vehicles, rank_map)
            self.update_table(self.performance_table, performance_vehicles, rank_map)
            self.update_table(self.sports_table, sports_vehicles, rank_map)
            
            # 更新标签页标题，显示数量
            self.tabs.setTabText(0, f"全部 ({len(all_vehicles)})")
            self.tabs.setTabText(1, f"极限组 ({len(extreme_vehicles)})")
            self.tabs.setTabText(2, f"性能组 ({len(performance_vehicles)})")
            self.tabs.setTabText(3, f"运动组 ({len(sports_vehicles)})")
                
        except Exception as e:
            logger.error(f"刷新车库失败: {str(e)}", exc_info=True)
    
    def update_table(self, table, vehicles, rank_map=None):
        """更新表格数据"""
        # 清空表格
        table.setRowCount(0)
        
        # 填充数据
        for v in vehicles:
            row = table.rowCount()
            table.insertRow(row)
            
            # 勾选框列
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Unchecked)
            checkbox.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, checkbox)
            
            # 总榜排名
            rank = rank_map.get(v.id, "-") if rank_map else "-"
            rank_item = QTableWidgetItem(str(rank))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            name_item = QTableWidgetItem(v.name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            category_item = QTableWidgetItem(v.category.value)
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            tier_item = QTableWidgetItem(str(v.tier))
            tier_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lap_time_item = QTableWidgetItem(f"{v.lap_time:.1f} s")
            lap_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 状态列：显示停用状态和场次进度
            parts = []
            if v.is_resting:
                parts.append("已停用")
            if v.rest_after_races is not None:
                progress = f"{v.races_completed}/{v.rest_after_races}"
                if v.races_completed >= v.rest_after_races:
                    progress += "\u2713"
                parts.append(progress)
            elif v.races_completed > 0:
                parts.append(f"已跑{v.races_completed}场")
            status_text = " ".join(parts) if parts else "正常"
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            table.setItem(row, 1, rank_item)
            table.setItem(row, 2, name_item)
            table.setItem(row, 3, category_item)
            table.setItem(row, 4, tier_item)
            table.setItem(row, 5, lap_time_item)
            table.setItem(row, 6, status_item)

            if v.is_effectively_resting:
                self._apply_resting_row_style(
                    checkbox,
                    rank_item,
                    name_item,
                    category_item,
                    tier_item,
                    lap_time_item,
                    status_item,
                )

            # 添加操作按钮（居中）
            upgrade_button = QPushButton("升阶")
            upgrade_button.setFixedWidth(42)
            upgrade_button.clicked.connect(lambda checked, name=v.name, tier=v.tier: self.adjust_tier(name, tier))

            resting_button = QPushButton("启用" if v.is_resting else "停用")
            resting_button.setFixedWidth(42)
            resting_button.clicked.connect(
                lambda checked, name=v.name, tier=v.tier, resting=not v.is_resting: self.set_vehicle_resting_status(
                    name,
                    tier,
                    resting,
                )
            )

            minus_one_button = QPushButton("-1场")
            minus_one_button.setFixedWidth(45)
            minus_one_button.setToolTip("已跑场次-1")
            minus_one_button.clicked.connect(
                lambda checked, name=v.name, tier=v.tier: self.decrement_single_race(name, tier)
            )

            plus_one_button = QPushButton("+1场")
            plus_one_button.setFixedWidth(45)
            plus_one_button.setToolTip("已跑场次+1")
            plus_one_button.clicked.connect(
                lambda checked, name=v.name, tier=v.tier: self.increment_single_race(name, tier)
            )

            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.addWidget(upgrade_button)
            container_layout.addWidget(resting_button)
            container_layout.addWidget(minus_one_button)
            container_layout.addWidget(plus_one_button)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)
            table.setCellWidget(row, 7, container)
            
    def add_vehicle(self):
        """添加车辆对话框（支持连续添加）"""
        while True:
            dialog = AddVehicleDialog(self.vehicle_repo, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                vehicle_info = dialog.get_vehicle_info()
                if vehicle_info:
                    name, tier = vehicle_info
                    try:
                        self.garage_repo.add_vehicle(name, tier)
                        self.refresh()
                        
                        # 询问是否继续添加
                        reply = QMessageBox.question(
                            self,
                            "添加成功",
                            f"车辆 '{name} {tier}阶' 已添加到车库\n\n是否继续添加车辆？",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        
                        if reply == QMessageBox.StandardButton.No:
                            break  # 用户选择不继续，退出循环
                        # 否则继续循环，显示新的添加对话框
                        
                    except BusinessLogicError as e:
                        QMessageBox.warning(self, "警告", str(e))
                        # 出错后也询问是否继续
                        reply = QMessageBox.question(
                            self,
                            "添加失败",
                            f"{str(e)}\n\n是否继续添加其他车辆？",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        if reply == QMessageBox.StandardButton.No:
                            break
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"添加失败：{str(e)}")
                        break  # 严重错误，退出
            else:
                # 用户取消对话框，退出循环
                break
    
    def adjust_tier(self, name: str, current_tier: int):
        """调整车辆阶数"""
        dialog = UpgradeTierDialog(name, current_tier, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_tier = dialog.get_new_tier()
            if new_tier is not None and new_tier != current_tier:
                try:
                    self.garage_repo.update_vehicle_tier(name, current_tier, new_tier)
                    QMessageBox.information(
                        self, 
                        "成功", 
                        f"车辆 '{name}' 已从 {current_tier}阶 调整到 {new_tier}阶"
                    )
                    self.refresh()
                except BusinessLogicError as e:
                    QMessageBox.warning(self, "警告", str(e))
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"调整阶数失败：{str(e)}")

    def set_vehicle_resting_status(self, name: str, tier: int, is_resting: bool):
        """设置车辆休息状态"""
        try:
            self.garage_repo.set_vehicle_resting_status(name, tier, is_resting)
            self.refresh()
        except BusinessLogicError as e:
            QMessageBox.warning(self, "警告", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新车辆状态失败：{str(e)}")
    

    def toggle_delete_mode(self):
        """切换删除模式"""
        self.delete_mode = not self.delete_mode

        # 获取所有表格
        tables = [self.all_table, self.sports_table, self.performance_table, self.extreme_table]

        if self.delete_mode:
            # 进入删除模式：显示勾选框
            for table in tables:
                table.setColumnHidden(0, False)
            self.delete_button.setText("确认移出")
            self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        else:
            # 退出删除模式 - 先执行删除，再清理UI
            self.remove_checked_vehicles()

            # 恢复UI状态
            self.delete_button.setText("移出车库")
            self.delete_button.setStyleSheet("")

            # 隐藏勾选框并取消所有勾选
            for table in tables:
                table.setColumnHidden(0, True)
                for row in range(table.rowCount()):
                    checkbox = table.item(row, 0)
                    if checkbox:
                        checkbox.setCheckState(Qt.CheckState.Unchecked)
    
    def remove_checked_vehicles(self):
        """删除所有勾选的车辆"""
        # 获取所有表格
        tables = [self.all_table, self.sports_table, self.performance_table, self.extreme_table]
        
        # 收集所有勾选的车辆
        vehicles_to_delete = []
        
        for table in tables:
            for row in range(table.rowCount()):
                checkbox = table.item(row, 0)
                if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                    name_item = table.item(row, 2)
                    tier_item = table.item(row, 4)
                    if name_item and tier_item:
                        name = name_item.text()
                        tier = int(tier_item.text())
                        # 避免重复添加
                        if (name, tier) not in vehicles_to_delete:
                            vehicles_to_delete.append((name, tier))
        
        if not vehicles_to_delete:
            return  # 没有勾选任何车辆，直接返回
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认移出",
            f"确定要将选中的 {len(vehicles_to_delete)} 辆车移出车库吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 执行删除
            for name, tier in vehicles_to_delete:
                try:
                    self.garage_repo.remove_vehicle(name, tier)
                except Exception as e:
                    logger.error(f"删除车辆失败: {str(e)}", exc_info=True)
            
            self.refresh()
            QMessageBox.information(self, "成功", f"已将 {len(vehicles_to_delete)} 辆车移出车库")
                    
    def remove_vehicle(self):
        """删除选中的车辆"""
        # 获取当前激活的标签页的表格
        current_tab_index = self.tabs.currentIndex()
        tables = [self.all_table, self.sports_table, self.performance_table, self.extreme_table]
        current_table = tables[current_tab_index]
        
        selected_rows = current_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的车辆")
            return
            
        reply = QMessageBox.question(
            self, 
            "确认", 
            f"确定要删除选中的 {len(selected_rows)} 辆车吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for index in selected_rows:
                row = index.row()
                name_item = current_table.item(row, 2)
                tier_item = current_table.item(row, 4)
                if name_item and tier_item:
                    name = name_item.text()
                    tier = int(tier_item.text())
                    try:
                        self.garage_repo.remove_vehicle(name, tier)
                    except Exception as e:
                        logger.error(f"删除车辆失败: {str(e)}", exc_info=True)
                        
            self.refresh()
            QMessageBox.information(self, "成功", "已删除选中的车辆")

    def increment_single_race(self, name: str, tier: int):
        """单车场次+1"""
        try:
            self.garage_repo.increment_races(name, tier)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"记录场次失败：{str(e)}")

    def decrement_single_race(self, name: str, tier: int):
        """单车场次-1"""
        try:
            self.garage_repo.decrement_races(name, tier)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"减少场次失败：{str(e)}")

    def _on_cell_double_clicked(self, row, column):
        """双击行触发调整阶数"""
        # 找到发送信号的表格
        table = self.sender()
        if not table:
            return
        name_item = table.item(row, 2)
        tier_item = table.item(row, 4)
        if name_item and tier_item:
            name = name_item.text()
            tier = int(tier_item.text())
            self.adjust_tier(name, tier)

    def apply_global_races(self):
        """应用全局默认场次到所有车辆"""
        races = self.global_races_spin.value()
        try:
            count = self.garage_repo.batch_set_rest_after_races(races)
            QMessageBox.information(self, "成功", f"已为 {count} 辆车设置自动休息场次为 {races} 场")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"设置失败：{str(e)}")

    def batch_reset_all_races(self):
        """全部重置场次计数"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置当前账号所有车辆的场次计数吗？\n（通常在新赛季开始时使用，不影响手动停用状态）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                count = self.garage_repo.batch_reset_races()
                QMessageBox.information(self, "成功", f"已重置 {count} 辆车的场次计数")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置失败：{str(e)}")

    def _get_checked_vehicles(self):
        """获取当前标签页中勾选的车辆列表"""
        current_tab_index = self.tabs.currentIndex()
        tables = [self.all_table, self.extreme_table, self.performance_table, self.sports_table]
        table = tables[current_tab_index]
        checked = []
        for row in range(table.rowCount()):
            checkbox = table.item(row, 0)
            if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                name_item = table.item(row, 2)
                tier_item = table.item(row, 4)
                if name_item and tier_item:
                    name = name_item.text()
                    tier = int(tier_item.text())
                    if (name, tier) not in checked:
                        checked.append((name, tier))
        return checked

    @staticmethod
    def _apply_resting_row_style(*items):
        """弱化显示已跑够车辆"""
        foreground = QColor(120, 120, 120)
        background = QColor(242, 242, 242)
        for item in items:
            item.setForeground(foreground)
            item.setBackground(background)
    
    def load_accounts(self):
        """加载账号列表到下拉框"""
        if not self.account_repo:
            return
        
        try:
            self._updating_account = True
            
            # 清空下拉框
            self.account_combo.clear()
            
            # 获取所有账号和当前激活账号
            accounts = self.account_repo.get_all_accounts()
            active_account = self.account_repo.get_active_account()
            
            # 添加到下拉框
            for account in accounts:
                display_text = account.name
                if active_account and account.id == active_account.id:
                    display_text += " ✓"
                self.account_combo.addItem(display_text, account.id)
            
            # 始终选中激活账号
            if active_account:
                index = self.account_combo.findData(active_account.id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
                    
        except Exception as e:
            logger.error(f"加载账号列表失败: {str(e)}", exc_info=True)
        finally:
            self._updating_account = False
    
    def on_account_changed(self, index):
        """账号下拉框改变时"""
        if index < 0 or not self.account_repo or self._updating_account:
            return
        
        account_id = self.account_combo.itemData(index)
        if not account_id:
            return
        
        try:
            # 切换激活账号
            self.account_repo.set_active_account(account_id)
            
            # 发出信号通知主窗口（会触发 refresh_all，包含 load_accounts 和 refresh）
            self.account_changed.emit(account_id)
            
        except Exception as e:
            logger.error(f"切换账号失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"切换账号失败：{str(e)}")


class AddVehicleDialog(QDialog):
    """添加车辆对话框"""
    
    def __init__(self, vehicle_repo: VehicleRepository, parent=None):
        super().__init__(parent)
        self.vehicle_repo = vehicle_repo
        self.selected_name = None
        self.selected_tier = None
        self.vehicles_map = {}  # 存储车辆名称到车辆列表的映射
        self._updating_combo = False  # 防止递归更新
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("添加车辆")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QFormLayout(self)
        
        # 组别筛选下拉框
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部组别", None)
        self.category_combo.addItem("运动组", "运动组")
        self.category_combo.addItem("性能组", "性能组")
        self.category_combo.addItem("极限组", "极限组")
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        layout.addRow("组别:", self.category_combo)
        
        # 车型名称下拉框（带搜索功能）
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)  # 允许输入
        self.name_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # 不插入新项
        
        # 设置自动完成器
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # 不区分大小写
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)  # 包含匹配
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)  # 弹出式完成
        self.name_combo.setCompleter(self.completer)
        
        # 连接信号
        self.name_combo.currentTextChanged.connect(self.on_name_changed)
        
        layout.addRow("车型名称:", self.name_combo)
        
        # 阶数下拉框
        self.tier_combo = QComboBox()
        self.tier_combo.currentIndexChanged.connect(self.update_lap_time)
        layout.addRow("阶数:", self.tier_combo)
        
        # 显示圈速信息
        self.lap_time_label = QLineEdit()
        self.lap_time_label.setReadOnly(True)
        self.lap_time_label.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("圈速:", self.lap_time_label)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        # 加载车辆数据
        self.load_vehicles()
        
    def load_vehicles(self):
        """加载所有车辆数据"""
        try:
            all_vehicles = self.vehicle_repo.get_all_vehicles()
            
            # 按车型名称分组
            self.vehicles_map.clear()
            for vehicle in all_vehicles:
                if vehicle.name not in self.vehicles_map:
                    self.vehicles_map[vehicle.name] = []
                self.vehicles_map[vehicle.name].append(vehicle)
            
            # 初始加载车型列表
            self.update_name_combo()
            
        except Exception as e:
            logger.error(f"加载车辆数据失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"加载车辆数据失败：{str(e)}")
    
    def on_category_changed(self):
        """组别改变时更新车型列表"""
        self.update_name_combo()
    
    def update_name_combo(self):
        """更新车型下拉框"""
        if self._updating_combo:
            return
        
        self._updating_combo = True
        
        try:
            # 保存当前输入的文本
            current_text = self.name_combo.currentText()
            
            # 暂时断开信号
            self.name_combo.blockSignals(True)
            self.name_combo.clear()
            
            selected_category = self.category_combo.currentData()
            
            # 获取符合组别筛选的车型名称
            vehicle_names = set()
            for name, vehicles in self.vehicles_map.items():
                if selected_category is None:
                    # 全部组别
                    vehicle_names.add(name)
                else:
                    # 检查是否有该组别的车辆
                    if any(v.category.value == selected_category for v in vehicles):
                        vehicle_names.add(name)
            
            # 排序并添加到下拉框
            sorted_names = sorted(vehicle_names)
            for name in sorted_names:
                self.name_combo.addItem(name)
            
            # 更新自动完成器
            self.completer.setModel(self.name_combo.model())
            
            # 恢复文本
            if current_text:
                self.name_combo.setEditText(current_text)
            
            # 恢复信号
            self.name_combo.blockSignals(False)
            
        finally:
            self._updating_combo = False
    
    def on_name_changed(self):
        """车型名称改变时更新阶数列表"""
        if self._updating_combo:
            return
            
        self.tier_combo.clear()
        self.lap_time_label.clear()
        
        name = self.name_combo.currentText()
        if not name or name not in self.vehicles_map:
            return
        
        selected_category = self.category_combo.currentData()
        vehicles = self.vehicles_map[name]
        
        # 筛选组别
        if selected_category:
            vehicles = [v for v in vehicles if v.category.value == selected_category]
        
        # 按阶数排序
        vehicles.sort(key=lambda v: v.tier)
        
        # 添加到阶数下拉框
        for vehicle in vehicles:
            display_text = f"{vehicle.tier}阶 ({vehicle.category.value}) - {vehicle.lap_time:.1f} s"
            self.tier_combo.addItem(display_text, vehicle.id)
        
        # 显示第一个的圈速
        if self.tier_combo.count() > 0:
            self.update_lap_time()
            self.update_lap_time()
    
    def update_lap_time(self):
        """更新圈速显示"""
        vehicle_id = self.tier_combo.currentData()
        if vehicle_id:
            # 查找车辆
            name = self.name_combo.currentText()
            if name in self.vehicles_map:
                for vehicle in self.vehicles_map[name]:
                    if vehicle.id == vehicle_id:
                        self.lap_time_label.setText(f"{vehicle.lap_time:.1f} s")
                        break
        
    def validate_and_accept(self):
        """验证并接受"""
        if self.name_combo.count() == 0:
            QMessageBox.warning(self, "警告", "没有可用的车辆")
            return
        
        if self.tier_combo.count() == 0:
            QMessageBox.warning(self, "警告", "请选择阶数")
            return
        
        # 获取选中的车辆名称和阶数
        self.selected_name = self.name_combo.currentText()
        
        # 从阶数下拉框的显示文本中提取阶数
        tier_text = self.tier_combo.currentText()
        # 格式是 "5阶 (极限组) - 327.00秒"，提取阶数
        if tier_text and "阶" in tier_text:
            tier_str = tier_text.split("阶")[0].strip()
            try:
                self.selected_tier = int(tier_str)
            except ValueError:
                QMessageBox.warning(self, "警告", "无法解析阶数")
                return
        else:
            QMessageBox.warning(self, "警告", "请选择有效的阶数")
            return
        
        if not self.selected_name or self.selected_tier is None:
            QMessageBox.warning(self, "警告", "请选择有效的车辆配置")
            return
        
        self.accept()
        
    def get_vehicle_info(self):
        """获取选中的车辆信息 (name, tier)"""
        if self.selected_name and self.selected_tier is not None:
            return (self.selected_name, self.selected_tier)
        return None


class UpgradeTierDialog(QDialog):
    """升阶对话框"""
    
    def __init__(self, vehicle_name: str, current_tier: int, parent=None):
        super().__init__(parent)
        self.vehicle_name = vehicle_name
        self.current_tier = current_tier
        self.new_tier = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("调整阶数")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QFormLayout(self)
        
        # 显示车辆名称
        name_label = QLabel(self.vehicle_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addRow("车型:", name_label)
        
        # 显示当前阶数
        current_tier_label = QLabel(f"{self.current_tier}阶")
        layout.addRow("当前阶数:", current_tier_label)
        
        # 新阶数选择
        self.tier_spin = QSpinBox()
        self.tier_spin.setMinimum(0)
        self.tier_spin.setMaximum(5)
        self.tier_spin.setValue(min(self.current_tier + 1, 5))  # 默认升1阶
        self.tier_spin.setSuffix("阶")
        layout.addRow("新阶数:", self.tier_spin)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_upgrade)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def accept_upgrade(self):
        """确认升阶"""
        new_tier = self.tier_spin.value()
        
        if new_tier == self.current_tier:
            QMessageBox.information(self, "提示", "新阶数与当前阶数相同，无需调整")
            return
        
        self.new_tier = new_tier
        self.accept()
        
    def get_new_tier(self):
        """获取新阶数"""
        return self.new_tier
