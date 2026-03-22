"""Pydantic 数据模型定义"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """车辆组别枚举"""
    SPORTS = "运动组"
    PERFORMANCE = "性能组"
    EXTREME = "极限组"


class VehicleData(BaseModel):
    """从网页爬取的原始车辆数据"""
    name: str = Field(..., min_length=1, description="车型名称")
    category: Category = Field(..., description="组别")
    tier: int = Field(..., ge=0, description="阶数")
    lap_time: float = Field(..., gt=0, description="圈速总和（秒）")
    
    @field_validator('lap_time')
    @classmethod
    def validate_lap_time(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('圈速必须大于0')
        return v


class VehicleConfig(BaseModel):
    """数据库中的车辆配置"""
    id: Optional[int] = None
    name: str
    category: Category
    tier: int
    lap_time: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class GarageVehicleConfig(VehicleConfig):
    """车库中的车辆配置，包含账号级状态"""
    is_resting: bool = False
    rest_after_races: Optional[int] = None  # 几场后自动休息，None=不启用
    races_completed: int = 0  # 已完成场次

    @property
    def is_effectively_resting(self) -> bool:
        """有效休息状态：手动停用 或 场次达标"""
        if self.is_resting:
            return True
        if self.rest_after_races is not None and self.races_completed >= self.rest_after_races:
            return True
        return False


class RankedVehicle(BaseModel):
    """带排名的车辆配置"""
    vehicle: VehicleConfig
    rank: int = Field(..., gt=0, description="排名")


class ValidationResult(BaseModel):
    """单个数据验证结果"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    data: Optional[VehicleData] = None


class BatchValidationResult(BaseModel):
    """批量验证结果"""
    total: int
    valid_count: int
    invalid_count: int
    valid_data: List[VehicleData]
    errors: List[str]


class RecommendationResult(BaseModel):
    """推荐结果"""
    vehicles: List[RankedVehicle]
    total_lap_time: float
    count: int
    category: Optional[Category] = None


class ComparisonResult(BaseModel):
    """组合对比结果"""
    recommended_total: float
    current_total: float
    improvement: float = Field(..., description="圈速改进（秒）")
    improvement_percentage: float = Field(..., description="改进百分比")
    different_vehicles: List[VehicleConfig] = Field(
        ..., 
        description="推荐组合中与当前组合不同的车辆"
    )
