import bcrypt
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
# import Database url from .env
from dotenv import dotenv_values

# Load environment variables
config = dotenv_values(".env")
password = config['DB_PASSWORD']

conn_string = 'mysql://{user}:{password}@{host}:{port}/{db}?charset=utf8'.format(
    user='Project_Orpheus',
    password=password,
    host = 'jsedocc7.scrc.nyu.edu',
    port     = 3306,
    encoding = 'utf-8',
    db = 'Project_Orpheus'
)
engine = create_engine(conn_string)
print("Connected to database" if engine else "Failed to connect to database")




# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
Base = declarative_base()
Base.metadata.create_all(bind=engine)

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# Function to get a database session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create a new user
def create_user(db, username: str, password: str):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username=username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

# Function to check if a username exists
def username_exists(db, username: str):
    return db.query(User).filter(User.username == username).first()

# Function to verify a password
def verify_password(stored_password: str, password: str):
    return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
