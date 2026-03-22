"""SQLAlchemy ORM 模型定义"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    create_engine,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from rm_rank.config import DATABASE_URL

Base = declarative_base()


class Account(Base):
    """账号表"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)  # 当前激活的账号
    sort_order = Column(Integer, default=0)  # 排列顺序
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    garage_entries = relationship("UserGarage", back_populates="account", cascade="all, delete-orphan")
    combination_entries = relationship("CurrentCombination", back_populates="account", cascade="all, delete-orphan")


class Vehicle(Base):
    """车辆数据表"""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    tier = Column(Integer, nullable=False)
    lap_time = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    garage_entries = relationship("UserGarage", back_populates="vehicle", cascade="all, delete-orphan")
    combination_entries = relationship("CurrentCombination", back_populates="vehicle", cascade="all, delete-orphan")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('name', 'tier', name='uq_vehicle_name_tier'),
        Index('idx_vehicles_category', 'category'),
        Index('idx_vehicles_lap_time', 'lap_time'),
        Index('idx_vehicles_name', 'name'),
    )


class UserGarage(Base):
    """用户车库表"""
    __tablename__ = "user_garage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    is_resting = Column(Boolean, default=False, nullable=False)
    rest_after_races = Column(Integer, nullable=True, default=None)  # 几场后自动休息
    races_completed = Column(Integer, nullable=False, default=0)     # 已完成场次

    # 关系
    account = relationship("Account", back_populates="garage_entries")
    vehicle = relationship("Vehicle", back_populates="garage_entries")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('account_id', 'vehicle_id', name='uq_garage_account_vehicle'),
        Index('idx_garage_account_id', 'account_id'),
    )


class CurrentCombination(Base):
    """当前组合表"""
    __tablename__ = "current_combination"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    position = Column(Integer, nullable=False)
    
    # 关系
    account = relationship("Account", back_populates="combination_entries")
    vehicle = relationship("Vehicle", back_populates="combination_entries")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('account_id', 'vehicle_id', name='uq_combination_account_vehicle'),
        Index('idx_combination_account_id', 'account_id'),
    )


def init_database(database_url: str = DATABASE_URL) -> None:
    """初始化数据库，创建所有表"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    
    # 迁移：若 accounts 表缺少 sort_order 列则补上
    with engine.connect() as conn:
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        cols = [c['name'] for c in inspector.get_columns('accounts')]
        if 'sort_order' not in cols:
            conn.execute(text("ALTER TABLE accounts ADD COLUMN sort_order INTEGER DEFAULT 0"))
        garage_cols = [c['name'] for c in inspector.get_columns('user_garage')]
        if 'is_resting' not in garage_cols:
            conn.execute(text("ALTER TABLE user_garage ADD COLUMN is_resting BOOLEAN DEFAULT 0 NOT NULL"))
        if 'rest_after_races' not in garage_cols:
            conn.execute(text("ALTER TABLE user_garage ADD COLUMN rest_after_races INTEGER DEFAULT NULL"))
        if 'races_completed' not in garage_cols:
            conn.execute(text("ALTER TABLE user_garage ADD COLUMN races_completed INTEGER DEFAULT 0 NOT NULL"))
        conn.commit()


def get_session_maker(database_url: str = DATABASE_URL) -> sessionmaker:
    """获取 Session 工厂
    
    Args:
        database_url: 数据库连接URL
        
    Returns:
        Session 工厂
    """
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)


def get_session(database_url: str = DATABASE_URL):
    """获取数据库会话
    
    Args:
        database_url: 数据库连接URL
        
    Returns:
        数据库会话对象
    """
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
