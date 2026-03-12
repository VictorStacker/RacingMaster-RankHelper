"""内存缓存"""
from typing import Optional, Dict, Tuple

from rm_rank.tuning.tuning_models import TuningData


class TuningCache:
    """提供快速的内存级数据访问"""
    
    def __init__(self):
        """初始化缓存"""
        self._cache: Dict[Tuple[str, int], TuningData] = {}
    
    def get(self, vehicle_name: str, tier: int) -> Optional[TuningData]:
        """从缓存获取数据
        
        Args:
            vehicle_name: 车辆名称
            tier: 阶位
            
        Returns:
            调教数据或None
        """
        key = (vehicle_name, tier)
        return self._cache.get(key)
    
    def set(self, vehicle_name: str, tier: int, data: TuningData) -> None:
        """设置缓存数据
        
        Args:
            vehicle_name: 车辆名称
            tier: 阶位
            data: 调教数据
        """
        key = (vehicle_name, tier)
        self._cache[key] = data
    
    def invalidate(self, vehicle_name: str, tier: int) -> None:
        """使缓存失效
        
        Args:
            vehicle_name: 车辆名称
            tier: 阶位
        """
        key = (vehicle_name, tier)
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
