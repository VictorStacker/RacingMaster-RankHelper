"""数据验证器"""
from typing import List

from pydantic import ValidationError as PydanticValidationError

from rm_rank.models.data_models import VehicleData, ValidationResult, BatchValidationResult


class DataValidator:
    """验证爬取数据的完整性和有效性"""
    
    def validate_vehicle_data(self, data: dict) -> ValidationResult:
        """验证单个车辆数据
        
        Args:
            data: 待验证的车辆数据字典
            
        Returns:
            验证结果，包含是否通过和错误信息
        """
        errors = []
        
        try:
            validated = VehicleData(**data)
            return ValidationResult(is_valid=True, data=validated)
        except PydanticValidationError as e:
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")
            
            return ValidationResult(is_valid=False, errors=errors)
    
    def validate_batch(self, data_list: List[dict]) -> BatchValidationResult:
        """批量验证车辆数据
        
        Args:
            data_list: 车辆数据字典列表
            
        Returns:
            批量验证结果
        """
        valid_data = []
        all_errors = []
        
        for i, data in enumerate(data_list):
            result = self.validate_vehicle_data(data)
            if result.is_valid and result.data:
                valid_data.append(result.data)
            else:
                all_errors.extend([f"数据{i+1}: {err}" for err in result.errors])
        
        return BatchValidationResult(
            total=len(data_list),
            valid_count=len(valid_data),
            invalid_count=len(data_list) - len(valid_data),
            valid_data=valid_data,
            errors=all_errors
        )
