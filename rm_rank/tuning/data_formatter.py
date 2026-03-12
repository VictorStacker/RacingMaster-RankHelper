"""数据格式化器"""
from rm_rank.tuning.tuning_models import TuningData
from rm_rank.tuning.tuning_errors import TuningError


class DataFormatter:
    """将调教数据格式化为用户友好的文本"""
    
    @staticmethod
    def format_tuning_data(data: TuningData) -> str:
        """格式化调教数据为文本
        
        Args:
            data: 调教数据对象
            
        Returns:
            格式化后的文本
        """
        if not data or not data.parameters:
            return "无调教数据"
        
        # 将参数字典格式化为多行文本
        lines = []
        for param_name, param_value in data.parameters.items():
            lines.append(f"{param_name}: {param_value}")
        
        return "\n".join(lines) if lines else "无调教数据"
    
    @staticmethod
    def format_error(error: Exception) -> str:
        """格式化错误信息
        
        Args:
            error: 异常对象
            
        Returns:
            用户友好的错误提示
        """
        from rm_rank.tuning.tuning_errors import (
            NetworkError, TimeoutError, HTTPError,
            ParserError, DatabaseError
        )
        
        if isinstance(error, (NetworkError, TimeoutError, HTTPError)):
            return "网络错误"
        elif isinstance(error, ParserError):
            return "解析失败"
        elif isinstance(error, DatabaseError):
            return "加载失败"
        elif isinstance(error, TuningError):
            return "加载失败"
        else:
            return "加载失败"
