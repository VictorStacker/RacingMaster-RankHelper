"""调教系统错误类型"""


class TuningError(Exception):
    """调教系统基础异常"""
    pass


class ScraperError(TuningError):
    """网页抓取错误"""
    pass


class NetworkError(ScraperError):
    """网络连接错误"""
    pass


class TimeoutError(ScraperError):
    """请求超时"""
    pass


class HTTPError(ScraperError):
    """HTTP状态码错误"""
    pass


class ParserError(TuningError):
    """数据解析错误"""
    pass


class HTMLStructureError(ParserError):
    """HTML结构错误"""
    pass


class DataFormatError(ParserError):
    """数据格式错误"""
    pass


class DatabaseError(TuningError):
    """数据库操作错误"""
    pass


class ConnectionError(DatabaseError):
    """数据库连接错误"""
    pass


class QueryError(DatabaseError):
    """查询执行错误"""
    pass


class MatcherError(TuningError):
    """阶位匹配错误"""
    pass


class InvalidTierError(MatcherError):
    """无效阶位"""
    pass


class ServiceError(TuningError):
    """服务层错误"""
    pass
