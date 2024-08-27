from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

db_username = os.getenv('DB_USERNAME', 'your_clearDB_username')
db_password = os.getenv('DB_PASSWORD', 'your_clearDB_password')
# DB_HOST for testing
#db_host = os.getenv('DB_HOST', 'localhost')
db_host = os.getenv('DB_HOST', 'your_clearDB_host')  # Przykład: us-cdbr-east-05.cleardb.net
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'your_clearDB_dbname')

databaseURL = os.getenv('JAWSDB_URL')


engine = create_engine(databaseURL)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()