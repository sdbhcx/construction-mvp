from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 数据库配置
# 格式：postgresql://username:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/construction")

# 创建SQLAlchemy引擎
# 配置连接池参数
engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 连接池最大溢出
    pool_timeout=30,        # 获取连接的超时时间
    pool_recycle=3600,      # 连接回收时间
    echo=False              # 是否打印SQL语句
)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖项函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()