from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

db_username = os.getenv('DB_USERNAME', 'root')
db_password = os.getenv('DB_PASSWORD', '')
#db_host = os.getenv('DB_HOST', 'localhost')
db_host = os.getenv('DB_HOST', 'host.docker.internal')
db_port = os.getenv('DB_PORT', '3306')  # Domyślny port dla MySQL
db_name = os.getenv('DB_NAME', 'StudentManagement')

databaseURL = f'mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'


#'mysql+pymysql://root:@localhost:3306/StudentManagement'

engine = create_engine(databaseURL)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()