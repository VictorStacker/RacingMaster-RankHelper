"""调教系统配置"""
from dataclasses import dataclass
from rm_rank import config


@dataclass
class TuningConfig:
    """调教系统配置"""
    chart_url: str = "https://waylongrank.top/chart.html"  # 圈速数据
    tuning_url: str = "https://waylongrank.top/index.html"  # 调教数据
    database_path: str = str(config.TUNING_DATABASE_PATH)
    request_timeout: int = 30
    max_retries: int = 3
    data_max_age_days: int = 7
    cache_enabled: bool = True
