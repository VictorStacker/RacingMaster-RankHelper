"""pytest 配置文件"""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_HOME = Path(__file__).resolve().parent / ".test_home"
TEST_HOME.mkdir(parents=True, exist_ok=True)
TEST_TEMP = TEST_HOME / "tmp"
TEST_TEMP.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = str(TEST_HOME)
os.environ["USERPROFILE"] = str(TEST_HOME)
os.environ["TMP"] = str(TEST_TEMP)
os.environ["TEMP"] = str(TEST_TEMP)
os.environ["PYTEST_DEBUG_TEMPROOT"] = str(TEST_TEMP)
tempfile.tempdir = str(TEST_TEMP)

from rm_rank.models.db_models import Base


@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 使用内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
