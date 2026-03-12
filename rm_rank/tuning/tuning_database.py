"""调教数据库管理器"""
import sqlite3
import json
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from rm_rank.tuning.tuning_models import TuningData
from rm_rank.tuning.tuning_errors import DatabaseError, ConnectionError as DBConnectionError, QueryError
from rm_rank.logger import logger


class DatabaseManager:
    """管理调教数据的持久化存储"""
    
    def __init__(self, db_path: str = "tuning_data.db"):
        """初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self.initialize_schema()
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        if db_dir and not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接
        
        Returns:
            数据库连接对象
            
        Raises:
            DBConnectionError: 连接失败
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {str(e)}", exc_info=True)
            raise DBConnectionError(f"数据库连接失败: {str(e)}")
    
    def initialize_schema(self):
        """初始化数据库表结构
        
        Raises:
            DatabaseError: 初始化失败
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 创建tuning_data表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tuning_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_name TEXT NOT NULL,
                    tier INTEGER NOT NULL CHECK(tier IN (0, 5)),
                    parameters TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vehicle_name, tier)
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_vehicle_tier 
                ON tuning_data(vehicle_name, tier)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库schema初始化成功")
            
        except sqlite3.Error as e:
            logger.error(f"数据库schema初始化失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"数据库schema初始化失败: {str(e)}")
    
    def save_tuning_data(self, data: TuningData):
        """保存或更新调教数据
        
        Args:
            data: 调教数据对象
            
        Raises:
            DatabaseError: 保存失败
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 将parameters字典转换为JSON字符串
            parameters_json = json.dumps(data.parameters, ensure_ascii=False)
            
            # 使用UPSERT操作（INSERT OR REPLACE）
            cursor.execute('''
                INSERT OR REPLACE INTO tuning_data 
                (vehicle_name, tier, parameters, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (
                data.vehicle_name,
                data.tier,
                parameters_json,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"保存调教数据: {data.vehicle_name} ({data.tier}阶)")
            
        except sqlite3.Error as e:
            logger.error(f"保存调教数据失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"保存调教数据失败: {str(e)}")
    
    def get_tuning_data(self, vehicle_name: str, tier: int) -> Optional[TuningData]:
        """查询调教数据
        
        Args:
            vehicle_name: 车辆名称
            tier: 阶位（0或5）
            
        Returns:
            调教数据对象或None
            
        Raises:
            DatabaseError: 查询失败
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT vehicle_name, tier, parameters, last_updated
                FROM tuning_data
                WHERE vehicle_name = ? AND tier = ?
            ''', (vehicle_name, tier))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # 解析JSON参数
                parameters = json.loads(row['parameters'])
                last_updated = datetime.fromisoformat(row['last_updated'])
                
                return TuningData(
                    vehicle_name=row['vehicle_name'],
                    tier=row['tier'],
                    parameters=parameters,
                    last_updated=last_updated
                )
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"查询调教数据失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"查询调教数据失败: {str(e)}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析数据库数据失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"解析数据库数据失败: {str(e)}")
    
    def is_data_stale(self, vehicle_name: str, tier: int, max_age_days: int = 7) -> bool:
        """检查数据是否过期
        
        Args:
            vehicle_name: 车辆名称
            tier: 阶位
            max_age_days: 最大有效天数
            
        Returns:
            数据是否过期
        """
        try:
            data = self.get_tuning_data(vehicle_name, tier)
            
            if not data or not data.last_updated:
                return True
            
            age = datetime.now() - data.last_updated
            return age > timedelta(days=max_age_days)
            
        except DatabaseError:
            # 查询失败视为数据过期
            return True
    
    def reset_tuning_data(self):
        """重置调教数据库（清空所有调教数据）
        
        此方法会删除tuning_data表中的所有数据，但保留表结构。
        不会影响其他数据库表（如账号数据）。
        
        Raises:
            DatabaseError: 重置失败
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 删除tuning_data表中的所有数据
            cursor.execute('DELETE FROM tuning_data')
            
            # 重置自增ID
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="tuning_data"')
            
            conn.commit()
            conn.close()
            
            logger.info("调教数据库已重置")
            
        except sqlite3.Error as e:
            logger.error(f"重置调教数据库失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"重置调教数据库失败: {str(e)}")
    
    def get_tuning_data_count(self) -> int:
        """获取调教数据总数
        
        Returns:
            调教数据记录数
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM tuning_data')
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return count
            
        except sqlite3.Error as e:
            logger.error(f"查询调教数据总数失败: {str(e)}", exc_info=True)
            return 0
    def reset_tuning_data(self):
        """重置调教数据库（清空所有调教数据）

        此方法会删除tuning_data表中的所有数据，但保留表结构。
        不会影响其他数据库表（如账号数据）。

        Raises:
            DatabaseError: 重置失败
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 删除tuning_data表中的所有数据
            cursor.execute('DELETE FROM tuning_data')

            # 重置自增ID
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="tuning_data"')

            conn.commit()
            conn.close()

            logger.info("调教数据库已重置")

        except sqlite3.Error as e:
            logger.error(f"重置调教数据库失败: {str(e)}", exc_info=True)
            raise DatabaseError(f"重置调教数据库失败: {str(e)}")

    def get_tuning_data_count(self) -> int:
        """获取调教数据总数

        Returns:
            调教数据记录数
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM tuning_data')
            count = cursor.fetchone()[0]

            conn.close()

            return count

        except sqlite3.Error as e:
            logger.error(f"查询调教数据总数失败: {str(e)}", exc_info=True)
            return 0
