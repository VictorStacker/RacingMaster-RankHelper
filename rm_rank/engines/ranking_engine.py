"""排行榜引擎"""
from typing import List, Optional

from rm_rank.models.data_models import VehicleConfig, RankedVehicle
from rm_rank.repositories import VehicleRepository


class RankingEngine:
    """生成和管理车辆排行榜"""
    
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo
    
    def generate_ranking(self, category: Optional[str] = None) -> List[RankedVehicle]:
        """生成排行榜
        
        Args:
            category: 可选的组别筛选条件
            
        Returns:
            排序后的车辆配置列表，包含排名
        """
        # 获取车辆数据
        if category:
            vehicles = self.vehicle_repo.get_vehicles_by_category(category)
        else:
            vehicles = self.vehicle_repo.get_all_vehicles()
        
        # 按圈速升序排序
        sorted_vehicles = sorted(vehicles, key=lambda v: v.lap_time)
        
        # 计算排名
        return self.calculate_rank(sorted_vehicles)
    
    def calculate_rank(self, vehicles: List[VehicleConfig]) -> List[RankedVehicle]:
        """计算排名，处理并列情况
        
        Args:
            vehicles: 已排序的车辆配置列表
            
        Returns:
            带排名的车辆列表
        """
        if not vehicles:
            return []
        
        ranked_vehicles = []
        current_rank = 1
        
        for i, vehicle in enumerate(vehicles):
            # 如果不是第一个且圈速与前一个相同，使用相同排名
            if i > 0 and vehicle.lap_time == vehicles[i - 1].lap_time:
                rank = ranked_vehicles[-1].rank
            else:
                rank = current_rank
            
            ranked_vehicles.append(RankedVehicle(vehicle=vehicle, rank=rank))
            current_rank += 1
        
        return ranked_vehicles
