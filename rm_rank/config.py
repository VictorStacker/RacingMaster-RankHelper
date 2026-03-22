"""配置管理模块"""
import os
from pathlib import Path

# 应用程序配置
APP_NAME = "racingmaster-rankhelper"
APP_VERSION = "1.6"

# 数据目录
DATA_DIR = Path.home() / f".{APP_NAME}"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 数据库配置
DATABASE_PATH = DATA_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 调教数据库配置
TUNING_DATABASE_PATH = DATA_DIR / "tuning_data.db"

# 日志配置
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# 数据源配置
DATA_SOURCE_URL = "https://waylongrank.top/chart.html"
CRAWLER_TIMEOUT = 30000  # 毫秒

# 推荐配置
DEFAULT_RECOMMENDATION_LIMIT = 9

# 用户偏好设置文件
PREFERENCES_FILE = DATA_DIR / "preferences.json"


def load_preferences() -> dict:
    """读取用户偏好设置"""
    if PREFERENCES_FILE.exists():
        import json
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_preferences(prefs: dict) -> None:
    """保存用户偏好设置"""
    import json
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
