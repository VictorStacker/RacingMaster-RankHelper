"""pytest 配置文件"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from rm_rank.models.db_models import Base


@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 使用内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = session()
    
    yield session
    
    session.close()
