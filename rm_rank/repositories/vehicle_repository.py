"""车辆数据仓库"""
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from rm_rank.models.data_models import VehicleData, VehicleConfig, Category
from rm_rank.models.db_models import Vehicle
from rm_rank.exceptions import DatabaseError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class VehicleRepository:
    """车辆数据的数据访问对象"""
    
    def __init__(self, session: Session):
        """
        初始化 VehicleRepository
        
        Args:
            session: SQLAlchemy 数据库会话
        """
        self.session = session
    
    def save_vehicles(self, vehicles: List[VehicleData]) -> None:
        """保存车辆数据（替换现有数据）
        
        Args:
            vehicles: 车辆数据列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            # 清空现有数据
            self.session.query(Vehicle).delete()
            
            # 插入新数据
            for vehicle_data in vehicles:
                vehicle = Vehicle(
                    name=vehicle_data.name,
                    category=vehicle_data.category.value,
                    tier=vehicle_data.tier,
                    lap_time=vehicle_data.lap_time
                )
                self.session.add(vehicle)
            
            self.session.commit()
            logger.info(f"成功保存 {len(vehicles)} 条车辆数据")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"保存车辆数据失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"保存数据失败: {str(e)}")
    
    def get_all_vehicles(self) -> List[VehicleConfig]:
        """获取所有车辆配置
        
        Returns:
            车辆配置列表
        """
        try:
            vehicles = self.session.query(Vehicle).all()
            return [self._to_vehicle_config(v) for v in vehicles]
        except SQLAlchemyError as e:
            logger.error(f"获取车辆数据失败: {str(e)}")
            raise DatabaseError(f"获取数据失败: {str(e)}")
    
    def get_vehicles_by_category(self, category: str) -> List[VehicleConfig]:
        """按组别获取车辆配置
        
        Args:
            category: 组别名称
            
        Returns:
            该组别的车辆配置列表
        """
        try:
            vehicles = self.session.query(Vehicle).filter(Vehicle.category == category).all()
            return [self._to_vehicle_config(v) for v in vehicles]
        except SQLAlchemyError as e:
            logger.error(f"按组别获取车辆失败: {str(e)}")
            raise DatabaseError(f"获取数据失败: {str(e)}")
    
    def vehicle_exists(self, name: str, category: str = None, tier: int = None) -> bool:
        """检查车型是否存在
        
        Args:
            name: 车型名称
            category: 组别（可选）
            tier: 阶数（可选）
            
        Returns:
            是否存在
        """
        try:
            query = self.session.query(Vehicle).filter(Vehicle.name == name)
            if category:
                query = query.filter(Vehicle.category == category)
            if tier:
                query = query.filter(Vehicle.tier == tier)
            count = query.count()
            return count > 0
        except SQLAlchemyError as e:
            logger.error(f"检查车辆存在失败: {str(e)}")
            return False
    
    def get_vehicle_by_name_and_tier(self, name: str, tier: int) -> Optional[VehicleConfig]:
        """根据车型名称和阶数获取车辆配置
        
        Args:
            name: 车型名称
            tier: 阶数
            
        Returns:
            车辆配置，如果不存在则返回 None
        """
        try:
            vehicle = self.session.query(Vehicle).filter(
                Vehicle.name == name,
                Vehicle.tier == tier
            ).first()
            return self._to_vehicle_config(vehicle) if vehicle else None
        except SQLAlchemyError as e:
            logger.error(f"获取车辆失败: {str(e)}")
            return None
    
    @staticmethod
    def _to_vehicle_config(vehicle: Vehicle) -> VehicleConfig:
        """将 ORM 模型转换为 Pydantic 模型
        
        Args:
            vehicle: ORM 车辆对象
            
        Returns:
            Pydantic 车辆配置对象
        """
        return VehicleConfig(
            id=vehicle.id,
            name=vehicle.name,
            category=Category(vehicle.category),
            tier=vehicle.tier,
            lap_time=vehicle.lap_time,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )
