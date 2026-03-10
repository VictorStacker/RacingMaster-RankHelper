"""异常类定义"""
from typing import List


class PeakSpeedError(Exception):
    """系统基础异常类"""
    pass


class NetworkError(PeakSpeedError):
    """网络相关错误"""
    pass


class CrawlerError(NetworkError):
    """爬虫错误"""
    pass


class ValidationError(PeakSpeedError):
    """数据验证错误"""
    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors


class DatabaseError(PeakSpeedError):
    """数据库错误"""
    pass


class BusinessLogicError(PeakSpeedError):
    """业务逻辑错误"""
    pass


class VehicleNotFoundError(BusinessLogicError):
    """车型不存在"""
    pass


class InvalidTierError(BusinessLogicError):
    """阶数无效"""
    pass


class EmptyGarageError(BusinessLogicError):
    """车库为空"""
    pass
