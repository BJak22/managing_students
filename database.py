from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

databaseURL = 'mysql+pymysql://root:@localhost:3306/StudentManagement'

engine = create_engine(databaseURL)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()