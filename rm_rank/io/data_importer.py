"""
数据导入模块

负责从 JSON 文件导入数据到数据库。
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from rm_rank.models.data_models import VehicleData, VehicleConfig
from rm_rank.repositories import VehicleRepository, GarageRepository, CombinationRepository
from rm_rank.validator import DataValidator
from rm_rank.exceptions import ValidationError, DatabaseError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class DataImporter:
    """数据导入类"""

    def __init__(
        self,
        vehicle_repo: VehicleRepository,
        garage_repo: GarageRepository,
        combination_repo: CombinationRepository,
        validator: DataValidator,
        account_repo=None,
    ):
        """
        初始化 DataImporter

        Args:
            vehicle_repo: 车辆数据仓库
            garage_repo: 车库数据仓库
            combination_repo: 当前组合数据仓库
            validator: 数据验证器
            account_repo: 账号数据仓库（可选，用于多账号导入）
        """
        self.vehicle_repo = vehicle_repo
        self.garage_repo = garage_repo
        self.combination_repo = combination_repo
        self.validator = validator
        self.account_repo = account_repo

    def import_vehicles(self, file_path: Path, replace: bool = False) -> int:
        """
        从 JSON 文件导入车辆数据

        Args:
            file_path: 导入文件路径
            replace: 是否替换现有数据（True）或追加（False）

        Returns:
            导入的车辆数量

        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
            IOError: 文件读取失败
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("data_type") != "vehicles":
                raise ValidationError(["文件类型错误：期望 'vehicles' 类型"])

            vehicles_data = data.get("vehicles", [])
            vehicles = []

            # 验证并转换数据
            for item in vehicles_data:
                try:
                    vehicle = VehicleData(
                        name=item["name"],
                        category=item["category"],
                        tier=item["tier"],
                        lap_time=item["lap_time"],
                    )
                    self.validator.validate_vehicle_data(vehicle)
                    vehicles.append(vehicle)
                except Exception as e:
                    logger.warning(f"跳过无效车辆数据: {item}, 错误: {e}")

            if not vehicles:
                raise ValidationError(["没有有效的车辆数据"])

            # 保存到数据库
            if replace:
                self.vehicle_repo.save_vehicles(vehicles)
            else:
                # 追加模式：逐个添加，跳过已存在的
                added = 0
                for vehicle in vehicles:
                    if not self.vehicle_repo.vehicle_exists(
                        vehicle.name, vehicle.category, vehicle.tier
                    ):
                        self.vehicle_repo.save_vehicles([vehicle])
                        added += 1
                logger.info(f"追加模式：导入 {added} 辆新车辆，跳过 {len(vehicles) - added} 辆已存在的车辆")
                return added

            logger.info(f"已导入 {len(vehicles)} 辆车辆数据")
            return len(vehicles)

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise IOError(f"JSON 解析失败: {e}")
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise IOError(f"文件不存在: {file_path}")
        except (ValidationError, DatabaseError) as e:
            logger.error(f"导入车辆数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise IOError(f"读取文件失败: {e}")

    def import_garage(self, file_path: Path, clear_existing: bool = False, selected_accounts: List[str] = None) -> int:
        """
        从 JSON 文件导入车库数据

        Args:
            file_path: 导入文件路径
            clear_existing: 是否清空现有车库
            selected_accounts: 要导入的账号名称列表（仅用于多账号格式，None表示导入所有账号）

        Returns:
            导入的车辆数量

        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
            IOError: 文件读取失败
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("data_type") != "garage":
                raise ValidationError(["文件类型错误：期望 'garage' 类型"])

            # 检测文件格式（旧格式 vs 新格式）
            if "accounts" in data:
                # 新格式：多账号数据
                return self._import_garage_multi_account(data, clear_existing, selected_accounts)
            else:
                # 旧格式：单账号数据
                return self._import_garage_single_account(data, clear_existing)

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise IOError(f"JSON 解析失败: {e}")
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise IOError(f"文件不存在: {file_path}")
        except (ValidationError, DatabaseError) as e:
            logger.error(f"导入车库数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise IOError(f"读取文件失败: {e}")

    def _import_garage_single_account(self, data: Dict[str, Any], clear_existing: bool) -> int:
        """
        导入单账号格式的车库数据（旧格式）

        Args:
            data: JSON数据
            clear_existing: 是否清空现有车库

        Returns:
            导入的车辆数量
        """
        if clear_existing:
            # 清空现有车库
            existing = self.garage_repo.get_all_garage_vehicles()
            for vehicle in existing:
                self.garage_repo.remove_vehicle(vehicle.name, vehicle.tier)

        garage_data = data.get("garage", [])
        added = 0

        for item in garage_data:
            try:
                # 检查车辆是否存在于数据库
                if self.vehicle_repo.vehicle_exists(
                    item["name"], item["category"], item["tier"]
                ):
                    # 检查是否已在车库中
                    if not self.garage_repo.vehicle_exists(
                        item["name"], item["tier"]
                    ):
                        self.garage_repo.add_vehicle(item["name"], item["tier"])
                        added += 1
                else:
                    logger.warning(
                        f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                    )
            except Exception as e:
                logger.warning(f"添加车辆到车库失败: {item}, 错误: {e}")

        logger.info(f"已导入 {added} 辆车辆到车库")
        return added

    def _import_garage_multi_account(self, data: Dict[str, Any], clear_existing: bool, selected_accounts: List[str] = None) -> int:
        """
        导入多账号格式的车库数据（新格式）

        Args:
            data: JSON数据
            clear_existing: 是否清空现有车库
            selected_accounts: 要导入的账号名称列表（None表示导入所有账号）

        Returns:
            导入的车辆数量
        """
        if not self.account_repo:
            raise ValidationError(["多账号导入需要 AccountRepository"])

        accounts_data = data.get("accounts", [])
        total_added = 0

        for account_data in accounts_data:
            account_name = account_data.get("name")
            account_description = account_data.get("description", "")
            garage_data = account_data.get("garage", [])

            # 如果指定了要导入的账号列表，检查当前账号是否在列表中
            if selected_accounts is not None and account_name not in selected_accounts:
                logger.info(f"跳过账号: {account_name}")
                continue

            # 查找或创建账号
            account = self.account_repo.get_account_by_name(account_name)
            if not account:
                logger.info(f"创建新账号: {account_name}")
                account = self.account_repo.create_account(account_name, account_description)
            
            # 切换到该账号的上下文
            self.garage_repo.set_account_id(account.id)

            # 清空该账号的现有车库（如果需要）
            if clear_existing:
                existing = self.garage_repo.get_all_garage_vehicles()
                for vehicle in existing:
                    self.garage_repo.remove_vehicle(vehicle.name, vehicle.tier)

            # 导入该账号的车库数据
            added = 0
            for item in garage_data:
                try:
                    # 检查车辆是否存在于数据库
                    if self.vehicle_repo.vehicle_exists(
                        item["name"], item["category"], item["tier"]
                    ):
                        # 检查是否已在车库中
                        if not self.garage_repo.vehicle_exists(
                            item["name"], item["tier"]
                        ):
                            self.garage_repo.add_vehicle(item["name"], item["tier"])
                            added += 1
                    else:
                        logger.warning(
                            f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                        )
                except Exception as e:
                    logger.warning(f"添加车辆到车库失败: {item}, 错误: {e}")

            logger.info(f"已为账号 {account_name} 导入 {added} 辆车辆到车库")
            total_added += added

        return total_added

    def import_current_combination(self, file_path: Path, selected_accounts: List[str] = None) -> int:
        """
        从 JSON 文件导入当前组合

        Args:
            file_path: 导入文件路径
            selected_accounts: 要导入的账号名称列表（仅用于多账号格式，None表示导入所有账号）

        Returns:
            导入的车辆数量

        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
            IOError: 文件读取失败
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("data_type") != "current_combination":
                raise ValidationError(["文件类型错误：期望 'current_combination' 类型"])

            # 检测文件格式（旧格式 vs 新格式）
            if "accounts" in data:
                # 新格式：多账号数据
                return self._import_combination_multi_account(data, selected_accounts)
            else:
                # 旧格式：单账号数据
                return self._import_combination_single_account(data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise IOError(f"JSON 解析失败: {e}")
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise IOError(f"文件不存在: {file_path}")
        except (ValidationError, DatabaseError) as e:
            logger.error(f"导入当前组合失败: {e}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise IOError(f"读取文件失败: {e}")

    def _import_combination_single_account(self, data: Dict[str, Any]) -> int:
        """
        导入单账号格式的当前组合数据（旧格式）

        Args:
            data: JSON数据

        Returns:
            导入的车辆数量
        """
        combination_data = data.get("combination", [])
        vehicles = []

        for item in combination_data:
            try:
                # 检查车辆是否存在于数据库
                if self.vehicle_repo.vehicle_exists(
                    item["name"], item["category"], item["tier"]
                ):
                    vehicle = VehicleConfig(
                        name=item["name"],
                        category=item["category"],
                        tier=item["tier"],
                        lap_time=item["lap_time"],
                    )
                    vehicles.append(vehicle)
                else:
                    logger.warning(
                        f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                    )
            except Exception as e:
                logger.warning(f"处理车辆数据失败: {item}, 错误: {e}")

        if vehicles:
            self.combination_repo.save_current_combination(vehicles)
            logger.info(f"已导入当前组合（{len(vehicles)} 辆车）")
        else:
            logger.warning("没有有效的车辆数据可导入")

        return len(vehicles)

    def _import_combination_multi_account(self, data: Dict[str, Any], selected_accounts: List[str] = None) -> int:
        """
        导入多账号格式的当前组合数据（新格式）

        Args:
            data: JSON数据
            selected_accounts: 要导入的账号名称列表（None表示导入所有账号）

        Returns:
            导入的车辆数量
        """
        if not self.account_repo:
            raise ValidationError(["多账号导入需要 AccountRepository"])

        accounts_data = data.get("accounts", [])
        total_added = 0

        for account_data in accounts_data:
            account_name = account_data.get("name")
            account_description = account_data.get("description", "")
            combination_data = account_data.get("combination", [])

            # 如果指定了要导入的账号列表，检查当前账号是否在列表中
            if selected_accounts is not None and account_name not in selected_accounts:
                logger.info(f"跳过账号: {account_name}")
                continue

            # 查找或创建账号
            account = self.account_repo.get_account_by_name(account_name)
            if not account:
                logger.info(f"创建新账号: {account_name}")
                account = self.account_repo.create_account(account_name, account_description)
            
            # 切换到该账号的上下文
            self.combination_repo.set_account_id(account.id)

            # 导入该账号的组合数据
            vehicles = []
            for item in combination_data:
                try:
                    # 检查车辆是否存在于数据库
                    if self.vehicle_repo.vehicle_exists(
                        item["name"], item["category"], item["tier"]
                    ):
                        vehicle = VehicleConfig(
                            name=item["name"],
                            category=item["category"],
                            tier=item["tier"],
                            lap_time=item["lap_time"],
                        )
                        vehicles.append(vehicle)
                    else:
                        logger.warning(
                            f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                        )
                except Exception as e:
                    logger.warning(f"处理车辆数据失败: {item}, 错误: {e}")

            if vehicles:
                self.combination_repo.save_current_combination(vehicles)
                logger.info(f"已为账号 {account_name} 导入当前组合（{len(vehicles)} 辆车）")
                total_added += len(vehicles)
            else:
                logger.warning(f"账号 {account_name} 没有有效的车辆数据可导入")

        return total_added

    def import_all_accounts(self, file_path: Path, clear_existing: bool = False, selected_accounts: List[str] = None) -> Dict[str, int]:
        """
        从统一格式的JSON文件导入所有账号的数据（包括车库和组合）

        Args:
            file_path: 导入文件路径
            clear_existing: 是否清空现有数据
            selected_accounts: 要导入的账号名称列表（None表示导入所有账号）

        Returns:
            包含导入统计信息的字典 {"garage": 车库车辆数, "combination": 组合车辆数}

        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
            IOError: 文件读取失败
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("data_type") != "all":
                raise ValidationError(["文件类型错误：期望 'all' 类型"])

            if not self.account_repo:
                raise ValidationError(["多账号导入需要 AccountRepository"])

            accounts_data = data.get("accounts", [])
            total_garage = 0
            total_combination = 0

            for account_data in accounts_data:
                account_name = account_data.get("name")
                account_description = account_data.get("description", "")
                garage_data = account_data.get("garage", [])
                combination_data = account_data.get("combination", [])

                # 如果指定了要导入的账号列表，检查当前账号是否在列表中
                if selected_accounts is not None and account_name not in selected_accounts:
                    logger.info(f"跳过账号: {account_name}")
                    continue

                # 查找或创建账号
                account = self.account_repo.get_account_by_name(account_name)
                if not account:
                    logger.info(f"创建新账号: {account_name}")
                    account = self.account_repo.create_account(account_name, account_description)
                
                # 切换到该账号的上下文
                self.garage_repo.set_account_id(account.id)
                self.combination_repo.set_account_id(account.id)

                # 清空该账号的现有数据（如果需要）
                if clear_existing:
                    existing = self.garage_repo.get_all_garage_vehicles()
                    for vehicle in existing:
                        self.garage_repo.remove_vehicle(vehicle.name, vehicle.tier)

                # 导入该账号的车库数据
                garage_added = 0
                for item in garage_data:
                    try:
                        if self.vehicle_repo.vehicle_exists(
                            item["name"], item["category"], item["tier"]
                        ):
                            if not self.garage_repo.vehicle_exists(
                                item["name"], item["tier"]
                            ):
                                self.garage_repo.add_vehicle(item["name"], item["tier"])
                                garage_added += 1
                        else:
                            logger.warning(
                                f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                            )
                    except Exception as e:
                        logger.warning(f"添加车辆到车库失败: {item}, 错误: {e}")

                # 导入该账号的组合数据
                vehicles = []
                for item in combination_data:
                    try:
                        if self.vehicle_repo.vehicle_exists(
                            item["name"], item["category"], item["tier"]
                        ):
                            vehicle = VehicleConfig(
                                name=item["name"],
                                category=item["category"],
                                tier=item["tier"],
                                lap_time=item["lap_time"],
                            )
                            vehicles.append(vehicle)
                        else:
                            logger.warning(
                                f"跳过不存在的车辆: {item['name']} {item['tier']}阶"
                            )
                    except Exception as e:
                        logger.warning(f"处理车辆数据失败: {item}, 错误: {e}")

                if vehicles:
                    self.combination_repo.save_current_combination(vehicles)

                logger.info(f"已为账号 {account_name} 导入 {garage_added} 辆车库车辆和 {len(vehicles)} 辆组合车辆")
                total_garage += garage_added
                total_combination += len(vehicles)

            logger.info(f"总计导入 {total_garage} 辆车库车辆和 {total_combination} 辆组合车辆")
            return {"garage": total_garage, "combination": total_combination}

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise IOError(f"JSON 解析失败: {e}")
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise IOError(f"文件不存在: {file_path}")
        except (ValidationError, DatabaseError) as e:
            logger.error(f"导入所有账号数据失败: {e}")
            raise
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise IOError(f"读取文件失败: {e}")
