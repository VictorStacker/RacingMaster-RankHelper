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
    ):
        """
        初始化 DataExporter

        Args:
            vehicle_repo: 车辆数据仓库
            garage_repo: 车库数据仓库
            combination_repo: 当前组合数据仓库
        """
        self.vehicle_repo = vehicle_repo
        self.garage_repo = garage_repo
        self.combination_repo = combination_repo

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
        导出用户车库数据到 JSON 文件

        Args:
            file_path: 导出文件路径

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            garage_vehicles = self.garage_repo.get_all_garage_vehicles()
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "garage",
                "count": len(garage_vehicles),
                "garage": [self._vehicle_to_dict(v) for v in garage_vehicles],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出 {len(garage_vehicles)} 辆车库数据到 {file_path}")

        except DatabaseError as e:
            logger.error(f"导出车库数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    def export_current_combination(self, file_path: Path) -> None:
        """
        导出当前组合到 JSON 文件

        Args:
            file_path: 导出文件路径

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        try:
            combination = self.combination_repo.get_current_combination()
            data = {
                "export_date": datetime.now().isoformat(),
                "data_type": "current_combination",
                "count": len(combination),
                "combination": [self._vehicle_to_dict(v) for v in combination],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已导出当前组合（{len(combination)} 辆车）到 {file_path}")

        except DatabaseError as e:
            logger.error(f"导出当前组合失败: {e}")
            raise
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            raise IOError(f"写入文件失败: {e}")

    def export_all(self, directory: Path) -> Dict[str, Path]:
        """
        导出所有数据到指定目录

        Args:
            directory: 导出目录

        Returns:
            导出文件路径字典

        Raises:
            DatabaseError: 数据库操作失败
            IOError: 文件写入失败
        """
        directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = {
            "vehicles": directory / f"vehicles_{timestamp}.json",
            "garage": directory / f"garage_{timestamp}.json",
            "combination": directory / f"combination_{timestamp}.json",
        }

        self.export_vehicles(files["vehicles"])
        self.export_garage(files["garage"])
        self.export_current_combination(files["combination"])

        logger.info(f"已导出所有数据到 {directory}")
        return files

    @staticmethod
    def _vehicle_to_dict(vehicle: VehicleConfig) -> Dict[str, Any]:
        """
        将车辆配置转换为字典

        Args:
            vehicle: 车辆配置

        Returns:
            车辆数据字典
        """
        return {
            "name": vehicle.name,
            "category": vehicle.category,
            "tier": vehicle.tier,
            "lap_time": vehicle.lap_time,
        }
