"""车库数据仓库"""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from rm_rank.models.data_models import GarageVehicleConfig, Category
from rm_rank.models.db_models import UserGarage, Vehicle, Account
from rm_rank.exceptions import DatabaseError, BusinessLogicError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class GarageRepository:
    """用户车库的数据访问对象"""
    
    def __init__(self, session: Session, account_id: Optional[int] = None):
        """
        初始化 GarageRepository
        
        Args:
            session: SQLAlchemy 数据库会话
            account_id: 账号ID（可选，如果不提供则使用当前激活的账号）
        """
        self.session = session
        self._account_id = account_id
    
    def _get_account_id(self) -> int:
        """获取当前账号ID
        
        Returns:
            账号ID
            
        Raises:
            BusinessLogicError: 没有激活的账号
        """
        if self._account_id:
            return self._account_id
        
        # 查找激活的账号
        active_account = self.session.query(Account).filter(Account.is_active == True).first()
        if not active_account:
            raise BusinessLogicError("没有激活的账号，请先创建或激活一个账号")
        
        return active_account.id
    
    def set_account_id(self, account_id: int) -> None:
        """设置当前操作的账号ID
        
        Args:
            account_id: 账号ID
        """
        self._account_id = account_id
    
    def add_vehicle(self, name: str, tier: int) -> None:
        """添加车辆到当前账号的车库
        
        Args:
            name: 车型名称
            tier: 阶数
            
        Raises:
            BusinessLogicError: 车辆不存在或已在车库中
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            # 查找车辆
            vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == tier
            ).first()
            
            if not vehicle:
                raise BusinessLogicError(f"车辆不存在: {name} {tier}阶")
            
            # 检查是否已在车库中
            existing = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id,
                UserGarage.vehicle_id == vehicle.id
            ).first()
            
            if existing:
                raise BusinessLogicError(f"车辆已在车库中: {name} {tier}阶")
            
            # 添加到车库
            garage_entry = UserGarage(account_id=account_id, vehicle_id=vehicle.id)
            self.session.add(garage_entry)
            self.session.commit()
            
            logger.info(f"添加车辆到车库 (账号ID={account_id}): {name} {tier}阶")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"添加车辆到车库失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"添加车辆失败: {str(e)}")
    
    def remove_vehicle(self, name: str, tier: int) -> None:
        """从当前账号的车库移除车辆
        
        Args:
            name: 车型名称
            tier: 阶数
            
        Raises:
            BusinessLogicError: 车辆不在车库中
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            # 查找车辆
            vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == tier
            ).first()
            
            if not vehicle:
                raise BusinessLogicError(f"车辆不存在: {name} {tier}阶")
            
            # 从车库移除
            deleted = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id,
                UserGarage.vehicle_id == vehicle.id
            ).delete()
            
            if deleted == 0:
                raise BusinessLogicError(f"车辆不在车库中: {name} {tier}阶")
            
            self.session.commit()
            logger.info(f"从车库移除车辆 (账号ID={account_id}): {name} {tier}阶")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"移除车辆失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"移除车辆失败: {str(e)}")
    
    def get_all_garage_vehicles(self) -> List[GarageVehicleConfig]:
        """获取当前账号车库中的所有车辆
        
        Returns:
            车辆配置列表
        """
        try:
            account_id = self._get_account_id()
            
            garage_entries = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id
            ).all()
            
            vehicles = []
            
            for entry in garage_entries:
                vehicle = self.session.query(Vehicle).filter(
                    Vehicle.id == entry.vehicle_id
                ).first()
                
                if vehicle:
                    vehicles.append(self._to_garage_vehicle_config(vehicle, entry.is_resting))
            
            return vehicles
            
        except Exception as e:
            logger.error(f"获取车库车辆失败: {str(e)}")
            if isinstance(e, BusinessLogicError):
                raise
            raise DatabaseError(f"获取车库数据失败: {str(e)}")
    
    def vehicle_exists(self, name: str, tier: int) -> bool:
        """检查车辆是否在当前账号的车库中
        
        Args:
            name: 车型名称
            tier: 阶数
            
        Returns:
            是否在车库中
        """
        try:
            account_id = self._get_account_id()
            
            vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == tier
            ).first()
            
            if not vehicle:
                return False
            
            count = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id,
                UserGarage.vehicle_id == vehicle.id
            ).count()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"检查车库车辆失败: {str(e)}")
            return False
    
    def update_vehicle_tier(self, name: str, old_tier: int, new_tier: int) -> None:
        """更新当前账号车库中车辆的阶数
        
        Args:
            name: 车型名称
            old_tier: 旧阶数
            new_tier: 新阶数
            
        Raises:
            BusinessLogicError: 车辆不在车库中或新阶数的车辆不存在
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            # 查找旧车辆
            old_vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == old_tier
            ).first()
            if not old_vehicle:
                raise BusinessLogicError(f"车辆不存在: {name} {old_tier}阶")
            
            # 查找新阶数车辆
            new_vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == new_tier
            ).first()
            if not new_vehicle:
                raise BusinessLogicError(f"车辆不存在: {name} {new_tier}阶")
            
            # 找到车库记录
            garage_entry = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id,
                UserGarage.vehicle_id == old_vehicle.id
            ).first()
            if not garage_entry:
                raise BusinessLogicError(f"车辆不在车库中: {name} {old_tier}阶")
            
            # 直接更新 vehicle_id，避免先删后加导致的重复检查问题
            garage_entry.vehicle_id = new_vehicle.id
            self.session.commit()
            
            logger.info(f"更新车辆阶数 (账号ID={account_id}): {name} {old_tier}阶 -> {new_tier}阶")
            
        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"更新车辆阶数失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"更新车辆阶数失败: {str(e)}")

    def set_vehicle_resting_status(self, name: str, tier: int, is_resting: bool) -> None:
        """设置当前账号车库车辆的休息状态"""
        try:
            account_id = self._get_account_id()

            vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == tier
            ).first()
            if not vehicle:
                raise BusinessLogicError(f"车辆不存在: {name} {tier}阶")

            garage_entry = self.session.query(UserGarage).filter(
                UserGarage.account_id == account_id,
                UserGarage.vehicle_id == vehicle.id
            ).first()
            if not garage_entry:
                raise BusinessLogicError(f"车辆不在车库中: {name} {tier}阶")

            garage_entry.is_resting = is_resting
            self.session.commit()

            logger.info(
                f"设置车辆休息状态 (账号ID={account_id}): {name} {tier}阶 -> {is_resting}"
            )

        except BusinessLogicError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"设置车辆休息状态失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"设置车辆休息状态失败: {str(e)}")
    
    @staticmethod
    def _to_garage_vehicle_config(vehicle: Vehicle, is_resting: bool) -> GarageVehicleConfig:
        """将 ORM 模型转换为 Pydantic 模型
        
        Args:
            vehicle: ORM 车辆对象
            
        Returns:
            Pydantic 车辆配置对象
        """
        return GarageVehicleConfig(
            id=vehicle.id,
            name=vehicle.name,
            category=Category(vehicle.category),
            tier=vehicle.tier,
            lap_time=vehicle.lap_time,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
            is_resting=is_resting,
        )
