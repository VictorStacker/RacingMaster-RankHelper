"""推荐引擎"""
from typing import List, Optional

from rm_rank.models.data_models import (
    VehicleConfig,
    RecommendationResult,
    ComparisonResult,
    RankedVehicle,
    Category,
)
from rm_rank.engines.ranking_engine import RankingEngine
from rm_rank.config import DEFAULT_RECOMMENDATION_LIMIT


class RecommendationEngine:
    """生成最优车辆组合推荐"""
    
    def __init__(self, ranking_engine: RankingEngine):
        self.ranking_engine = ranking_engine
    
    def recommend_optimal_combination(
        self,
        user_garage: List[VehicleConfig],
        category: Optional[str] = None,
        limit: int = DEFAULT_RECOMMENDATION_LIMIT
    ) -> RecommendationResult:
        """推荐最优车辆组合
        
        Args:
            user_garage: 用户车库中的车辆配置
            category: 可选的组别限制
            limit: 推荐数量，默认9辆
            
        Returns:
            推荐结果，包含车辆列表和统计信息
        """
        # 筛选组别
        if category:
            filtered_garage = [v for v in user_garage if v.category.value == category]
        else:
            filtered_garage = user_garage
        
        # 按圈速排序
        sorted_vehicles = sorted(filtered_garage, key=lambda v: v.lap_time)
        
        # 选择前N个
        selected = sorted_vehicles[:limit]
        
        # 生成排名
        ranked = self.ranking_engine.calculate_rank(selected)
        
        # 计算总圈速
        total_lap_time = sum(v.vehicle.lap_time for v in ranked)
        
        return RecommendationResult(
            vehicles=ranked,
            total_lap_time=total_lap_time,
            count=len(ranked),
            category=Category(category) if category else None
        )
    
    def recommend_all_categories(
        self,
        user_garage: List[VehicleConfig],
        limit_per_category: int = DEFAULT_RECOMMENDATION_LIMIT
    ) -> RecommendationResult:
        """推荐所有组别的最优车辆组合（每组各选前N辆）
        
        Args:
            user_garage: 用户车库中的车辆配置
            limit_per_category: 每个组别的推荐数量，默认9辆
            
        Returns:
            推荐结果，包含所有组别的车辆列表和统计信息
        """
        all_selected = []
        
        # 对每个组别分别推荐
        for category in ["运动组", "性能组", "极限组"]:
            # 筛选该组别的车辆
            category_vehicles = [v for v in user_garage if v.category.value == category]
            
            # 按圈速排序并选择前N个
            sorted_vehicles = sorted(category_vehicles, key=lambda v: v.lap_time)
            selected = sorted_vehicles[:limit_per_category]
            
            all_selected.extend(selected)
        
        # 对所有选中的车辆按圈速排序
        all_selected.sort(key=lambda v: v.lap_time)
        
        # 对所有选中的车辆重新排名
        ranked = self.ranking_engine.calculate_rank(all_selected)
        
        # 计算总圈速
        total_lap_time = sum(v.vehicle.lap_time for v in ranked)
        
        return RecommendationResult(
            vehicles=ranked,
            total_lap_time=total_lap_time,
            count=len(ranked),
            category=None  # 全部组别
        )
    
    def recommend_all_categories_custom(
        self,
        user_garage: List[VehicleConfig],
        extreme_count: int,
        performance_count: int,
        sports_count: int
    ) -> RecommendationResult:
        """推荐所有组别的最优车辆组合（每组不同数量）
        
        Args:
            user_garage: 用户车库中的车辆配置
            extreme_count: 极限组推荐数量
            performance_count: 性能组推荐数量
            sports_count: 运动组推荐数量
            
        Returns:
            推荐结果，包含所有组别的车辆列表和统计信息
        """
        all_selected = []
        
        # 定义每个组别的数量
        category_limits = {
            "极限组": extreme_count,
            "性能组": performance_count,
            "运动组": sports_count
        }
        
        # 对每个组别分别推荐
        for category, limit in category_limits.items():
            # 筛选该组别的车辆
            category_vehicles = [v for v in user_garage if v.category.value == category]
            
            # 按圈速排序并选择前N个
            sorted_vehicles = sorted(category_vehicles, key=lambda v: v.lap_time)
            selected = sorted_vehicles[:limit]
            
            all_selected.extend(selected)
        
        # 对所有选中的车辆按圈速排序
        all_selected.sort(key=lambda v: v.lap_time)
        
        # 对所有选中的车辆重新排名
        ranked = self.ranking_engine.calculate_rank(all_selected)
        
        # 计算总圈速
        total_lap_time = sum(v.vehicle.lap_time for v in ranked)
        
        return RecommendationResult(
            vehicles=ranked,
            total_lap_time=total_lap_time,
            count=len(ranked),
            category=None  # 全部组别
        )
    
    def compare_combinations(
        self,
        recommended: List[VehicleConfig],
        current: List[VehicleConfig]
    ) -> ComparisonResult:
        """对比推荐组合与当前组合
        
        Args:
            recommended: 推荐的车辆组合
            current: 当前使用的车辆组合
            
        Returns:
            对比结果，包含差异和改进百分比
        """
        recommended_total = sum(v.lap_time for v in recommended)
        current_total = sum(v.lap_time for v in current)
        
        improvement = current_total - recommended_total
        improvement_percentage = (improvement / current_total * 100) if current_total > 0 else 0
        
        # 找出不同的车辆
        current_ids = {v.id for v in current}
        different_vehicles = [v for v in recommended if v.id not in current_ids]
        
        return ComparisonResult(
            recommended_total=recommended_total,
            current_total=current_total,
            improvement=improvement,
            improvement_percentage=improvement_percentage,
            different_vehicles=different_vehicles
        )
