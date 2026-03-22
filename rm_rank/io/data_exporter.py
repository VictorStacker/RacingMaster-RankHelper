"""
数据导出模块

负责将数据库中的数据导出为 JSON 文件。
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from rm_rank.models.data_models import VehicleConfig
from rm_rank.repositories import VehicleRepository, GarageRepository, CombinationRepository
from rm_rank.exceptions import DatabaseError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class DataExporter:
    """数据导出类"""

    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        garage_repo: GarageRepository,
        combination_repo: CombinationRepository,
        account_repo,
    ):
        """
        初始化 DataExporter

        Args:
            vehicle_repo: 车辆数据仓库
            garage_repo: 车库数据仓库
            combination_repo: 当前组合数据仓库
            account_repo: 账号数据仓库
        """
        self.vehicle_repo = vehicle_repo
        self.garage_repo = garage_repo
        self.combination_repo = combination_repo
        self.account_repo = account_repo


    def export_vehicles(self, file_path: Path) -> None:
        """
        导出所有车辆数据到 JSON 文件

        Args:
            file_path: 导出文件路径

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            vehicles = self.vehicle_repo.get_all_vehicles()
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "vehicles",
                "count": len(vehicles),
                "vehicles": [self._vehicle_to_dict(v) for v in vehicles],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 {len(vehicles)} 辆车辆数据到 {file_path}")

        except DatabaseError as e:
            logger.error(f"导出车辆数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    def export_garage(self, file_path: Path) -> None:
        """
        导出所有账号的车库数据到 JSON 文件

        Args:
            file_path: 导出文件路径

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            # 获取所有账号
            accounts = self.account_repo.get_all_accounts()
            
            accounts_data = []
            total_vehicles = 0
            
            for account in accounts:
                # 切换到该账号的上下文
                self.garage_repo.set_account_id(account.id)
                
                # 获取该账号的车库数据
                garage_vehicles = self.garage_repo.get_all_garage_vehicles()
                
                accounts_data.append({
                    "name": account.name,
                    "description": account.description or "",
                    "garage": [self._vehicle_to_dict(v, include_resting=True) for v in garage_vehicles]
                })
                
                total_vehicles += len(garage_vehicles)
            
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "garage",
                "accounts": accounts_data
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 {len(accounts)} 个账号的车库数据（共 {total_vehicles} 辆车）到 {file_path}")

        except DatabaseError as e:
            logger.error(f"导出车库数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    def export_current_combination(self, file_path: Path) -> None:
        """
        导出所有账号的当前组合到 JSON 文件

        Args:
            file_path: 导出文件路径

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            # 获取所有账号
            accounts = self.account_repo.get_all_accounts()
            
            accounts_data = []
            total_vehicles = 0
            
            # 需要直接访问数据库来按账号查询组合
            from rm_rank.models.db_models import CurrentCombination, Vehicle
            
            for account in accounts:
                # 直接查询该账号的当前组合
                combinations = (
                    self.combination_repo.session.query(CurrentCombination)
                    .filter(CurrentCombination.account_id == account.id)
                    .order_by(CurrentCombination.position)
                    .all()
                )
                
                combination_vehicles = []
                for combo in combinations:
                    vehicle = (
                        self.combination_repo.session.query(Vehicle)
                        .filter_by(id=combo.vehicle_id)
                        .first()
                    )
                    if vehicle:
                        combination_vehicles.append(
                            VehicleConfig(
                                name=vehicle.name,
                                category=vehicle.category,
                                tier=vehicle.tier,
                                lap_time=vehicle.lap_time,
                            )
                        )
                
                accounts_data.append({
                    "name": account.name,
                    "description": account.description or "",
                    "combination": [self._vehicle_to_dict(v) for v in combination_vehicles]
                })
                
                total_vehicles += len(combination_vehicles)
            
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "current_combination",
                "accounts": accounts_data
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 {len(accounts)} 个账号的当前组合（共 {total_vehicles} 辆车）到 {file_path}")

        except DatabaseError as e:
            logger.error(f"导出当前组合失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    def export_all(self, directory: Path) -> Dict[str, Path]:
        """
        导出所有账号的用户数据到指定目录（不包含车辆数据）

        Args:
            directory: 导出目录

        Returns:
            导出文件路径字典

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = directory / f"all_accounts_{timestamp}.json"
            
            # 获取所有账号
            accounts = self.account_repo.get_all_accounts()
            
            accounts_data = []
            
            # 需要直接访问数据库来按账号查询组合
            from rm_rank.models.db_models import CurrentCombination, Vehicle
            
            for account in accounts:
                # 获取该账号的车库数据
                self.garage_repo.set_account_id(account.id)
                garage_vehicles = self.garage_repo.get_all_garage_vehicles()
                
                # 直接查询该账号的当前组合
                combinations = (
                    self.combination_repo.session.query(CurrentCombination)
                    .filter(CurrentCombination.account_id == account.id)
                    .order_by(CurrentCombination.position)
                    .all()
                )
                
                combination_vehicles = []
                for combo in combinations:
                    vehicle = (
                        self.combination_repo.session.query(Vehicle)
                        .filter_by(id=combo.vehicle_id)
                        .first()
                    )
                    if vehicle:
                        combination_vehicles.append(
                            VehicleConfig(
                                name=vehicle.name,
                                category=vehicle.category,
                                tier=vehicle.tier,
                                lap_time=vehicle.lap_time,
                            )
                        )
                
                accounts_data.append({
                    "name": account.name,
                    "description": account.description or "",
                    "garage": [self._vehicle_to_dict(v, include_resting=True) for v in garage_vehicles],
                    "combination": [self._vehicle_to_dict(v) for v in combination_vehicles]
                })
            
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "all_accounts",
                "accounts": accounts_data
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已导出 {len(accounts)} 个账号的所有用户数据到 {file_path}")
            
            return {"all_accounts": file_path}

        except DatabaseError as e:
            logger.error(f"导出所有数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    @staticmethod
    def _vehicle_to_dict(vehicle: VehicleConfig, include_resting: bool = False) -> Dict[str, Any]:
        """
        将车辆配置转换为字典

        Args:
            vehicle: 车辆配置

        Returns:
            车辆数据字典
        """
        data = {
            "name": vehicle.name,
            "category": vehicle.category,
            "tier": vehicle.tier,
            "lap_time": vehicle.lap_time,
        }
        if include_resting:
            data["is_resting"] = getattr(vehicle, "is_resting", False)
            rest_after = getattr(vehicle, "rest_after_races", None)
            if rest_after is not None:
                data["rest_after_races"] = rest_after
            races = getattr(vehicle, "races_completed", 0)
            if races > 0:
                data["races_completed"] = races
        return data
