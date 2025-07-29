from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase PostgreSQL bağlantısı
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.jqukwkywcocypdjbbbze:Jawdropping.269@aws-0-us-east-2.pooler.supabase.com:5432/postgres")

# Engine oluştur - connection pool ve timeout ayarları ile
engine = create_engine(
    DATABASE_URL,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        "connect_timeout": 30,
        "application_name": "edufast_api",
        "options": "-c statement_timeout=30000"
    },
    echo=False  # SQL loglarını kapatır
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()