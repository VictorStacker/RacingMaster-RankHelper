"""
当前组合数据访问层

负责管理用户标记的当前使用车辆组合。
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from rm_rank.models.db_models import CurrentCombination, Vehicle
from rm_rank.models.data_models import VehicleConfig
from rm_rank.exceptions import DatabaseError
from rm_rank.logger import get_logger

logger = get_logger(__name__)


class CombinationRepository:
    """当前组合数据访问类"""

    def __init__(self, session: Session, account_id: Optional[int] = None):
        """
        初始化 CombinationRepository

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
            DatabaseError: 没有激活的账号
        """
        from rm_rank.models.db_models import Account
        
        if self._account_id:
            return self._account_id
        
        # 查找激活的账号
        active_account = self.session.query(Account).filter(Account.is_active == True).first()
        if not active_account:
            raise DatabaseError("没有激活的账号，请先创建或激活一个账号")
        
        return active_account.id

    def set_account_id(self, account_id: int) -> None:
        """设置当前操作的账号ID
        
        Args:
            account_id: 账号ID
        """
        self._account_id = account_id

    def save_current_combination(self, vehicle_configs: List[VehicleConfig]) -> None:
        """
        保存当前使用的车辆组合

        Args:
            vehicle_configs: 车辆配置列表

        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            # 清空现有组合
            self.clear_current_combination()

            # 保存新组合
            for position, config in enumerate(vehicle_configs, start=1):
                # 查找对应的车辆记录
                vehicle = (
                    self.session.query(Vehicle)
                    .filter_by(
                        name=config.name, category=config.category, tier=config.tier
                    )
                    .first()
                )

                if vehicle:
                    combination = CurrentCombination(
                        account_id=account_id,
                        vehicle_id=vehicle.id, 
                        position=position
                    )
                    self.session.add(combination)

            self.session.commit()
            logger.info(f"已保存当前组合（账号ID={account_id}），共 {len(vehicle_configs)} 辆车")

        except Exception as e:
            self.session.rollback()
            logger.error(f"保存当前组合失败: {e}")
            raise DatabaseError(f"保存当前组合失败: {e}")

    def get_current_combination(self) -> List[VehicleConfig]:
        """
        获取当前标记的车辆组合

        Returns:
            车辆配置列表，按位置排序

        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            combinations = (
                self.session.query(CurrentCombination)
                .filter(CurrentCombination.account_id == account_id)
                .order_by(CurrentCombination.position)
                .all()
            )

            result = []
            for combo in combinations:
                vehicle = (
                    self.session.query(Vehicle)
                    .filter_by(id=combo.vehicle_id)
                    .first()
                )
                if vehicle:
                    result.append(
                        VehicleConfig(
                            name=vehicle.name,
                            category=vehicle.category,
                            tier=vehicle.tier,
                            lap_time=vehicle.lap_time,
                        )
                    )

            logger.info(f"获取当前组合（账号ID={account_id}），共 {len(result)} 辆车")
            return result

        except Exception as e:
            logger.error(f"获取当前组合失败: {e}")
            raise DatabaseError(f"获取当前组合失败: {e}")

    def clear_current_combination(self) -> None:
        """
        清空当前组合

        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            account_id = self._get_account_id()
            
            self.session.query(CurrentCombination).filter(
                CurrentCombination.account_id == account_id
            ).delete()
            self.session.commit()
            logger.info(f"已清空当前组合（账号ID={account_id}）")

        except Exception as e:
            self.session.rollback()
            logger.error(f"清空当前组合失败: {e}")
            raise DatabaseError(f"清空当前组合失败: {e}")

    def has_current_combination(self) -> bool:
        """
        检查是否存在当前组合

        Returns:
            如果存在当前组合返回 True，否则返回 False
        """
        try:
            account_id = self._get_account_id()
            
            count = self.session.query(CurrentCombination).filter(
                CurrentCombination.account_id == account_id
            ).count()
            return count > 0
        except Exception as e:
            logger.error(f"检查当前组合失败: {e}")
            return False
