"""调教数据模型"""
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class TuningData:
    """调教数据模型"""
    vehicle_name: str
    tier: int  # 0 or 5
    parameters: Dict[str, str]  # 调教参数键值对
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'vehicle_name': self.vehicle_name,
            'tier': self.tier,
            'parameters': self.parameters,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TuningData':
        """从字典创建对象"""
        return cls(
            vehicle_name=data['vehicle_name'],
            tier=data['tier'],
            parameters=data['parameters'],
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )
