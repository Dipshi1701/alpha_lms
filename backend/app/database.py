from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app import config

# Connect to MySQL using PyMySQL driver
engine = create_engine(config.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yield a database session, then close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
