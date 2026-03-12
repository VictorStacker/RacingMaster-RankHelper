"""阶位匹配器"""
from rm_rank.tuning.tuning_errors import MatcherError, InvalidTierError


class TierMatcher:
    """根据车辆阶位选择合适的调教数据"""
    
    @staticmethod
    def get_target_tier(vehicle_tier: int) -> int:
        """根据车辆阶位确定目标调教阶位
        
        Args:
            vehicle_tier: 车辆阶位（0-5）
            
        Returns:
            目标阶位（0或5）
            
        Raises:
            InvalidTierError: 无效阶位
        """
        if vehicle_tier < 0 or vehicle_tier > 5:
            raise InvalidTierError(f"无效的车辆阶位: {vehicle_tier}，有效范围为0-5")
        
        # 0阶车辆使用0阶调教，1-5阶车辆使用5阶调教
        return 0 if vehicle_tier == 0 else 5
