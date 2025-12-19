from backend.config.database import engine, Base
from backend.models.orm.tables import *


def init_database():
    """初始化数据库，创建所有表结构"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")


if __name__ == "__main__":
    init_database()