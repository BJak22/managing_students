from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

db_username = os.getenv('DB_USERNAME', 'your_clearDB_username')
db_password = os.getenv('DB_PASSWORD', 'your_clearDB_password')
# DB_HOST for testing
#db_host = os.getenv('DB_HOST', 'localhost')
db_host = os.getenv('DB_HOST', 'your_clearDB_host')
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'your_clearDB_dbname')

databaseURL = os.getenv('JAWSDB_URL', 'mysql+pymysql://g50549r7ajudojfr:o5zejchzh3rmq01e@sabaik6fx8he7pua.chr7pe7iynqr.eu-west-1.rds.amazonaws.com/su5bsnthxe4u5i8t')


engine = create_engine(databaseURL)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()