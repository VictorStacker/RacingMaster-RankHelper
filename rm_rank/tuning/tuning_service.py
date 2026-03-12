"""调教服务协调层"""
from typing import Optional

from rm_rank.tuning.tuning_models import TuningData
from rm_rank.tuning.tuning_database import DatabaseManager
from rm_rank.tuning.tuning_cache import TuningCache
from rm_rank.tuning.tier_matcher import TierMatcher
from rm_rank.tuning.data_formatter import DataFormatter
from rm_rank.tuning.tuning_errors import TuningError, ServiceError
from rm_rank.logger import logger


class TuningService:
    """协调各组件，提供统一的调教数据获取接口"""
    
    def __init__(self, db_manager: DatabaseManager, cache: TuningCache):
        """初始化服务
        
        Args:
            db_manager: 数据库管理器
            cache: 缓存管理器
        """
        self.db_manager = db_manager
        self.cache = cache
        self.tier_matcher = TierMatcher()
        self.formatter = DataFormatter()
    
    def get_tuning_recommendation(self, vehicle_name: str, vehicle_tier: int) -> str:
        """获取调教推荐
        
        Args:
            vehicle_name: 车辆名称
            vehicle_tier: 车辆阶位
            
        Returns:
            格式化的调教推荐文本或错误提示
        """
        try:
            # 确定目标调教阶位
            target_tier = self.tier_matcher.get_target_tier(vehicle_tier)
            
            # 1. 优先从缓存获取
            tuning_data = self.cache.get(vehicle_name, target_tier)
            if tuning_data:
                logger.debug(f"从缓存获取调教数据: {vehicle_name} ({target_tier}阶)")
                return self.formatter.format_tuning_data(tuning_data)
            
            # 2. 从数据库获取
            tuning_data = self.db_manager.get_tuning_data(vehicle_name, target_tier)
            if tuning_data:
                # 更新缓存
                self.cache.set(vehicle_name, target_tier, tuning_data)
                logger.debug(f"从数据库获取调教数据: {vehicle_name} ({target_tier}阶)")
                return self.formatter.format_tuning_data(tuning_data)
            
            # 3. 数据不存在
            return "无调教数据"
            
        except TuningError as e:
            logger.error(f"获取调教推荐失败: {str(e)}", exc_info=True)
            return self.formatter.format_error(e)
        except Exception as e:
            logger.error(f"获取调教推荐时发生未知错误: {str(e)}", exc_info=True)
            return "加载失败"
    
    def refresh_data(self, vehicle_name: str, vehicle_tier: int):
        """刷新调教数据
        
        Args:
            vehicle_name: 车辆名称
            vehicle_tier: 车辆阶位
            
        Raises:
            ServiceError: 刷新失败
        """
        try:
            target_tier = self.tier_matcher.get_target_tier(vehicle_tier)
            
            # 使缓存失效
            self.cache.invalidate(vehicle_name, target_tier)
            
            logger.info(f"刷新调教数据: {vehicle_name} ({target_tier}阶)")
            
        except Exception as e:
            logger.error(f"刷新调教数据失败: {str(e)}", exc_info=True)
            raise ServiceError(f"刷新调教数据失败: {str(e)}")
    
    def clear_cache(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("已清空调教数据缓存")
