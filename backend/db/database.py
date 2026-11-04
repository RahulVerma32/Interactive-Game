from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import settings

def database_url(raw_url: str):
    url = make_url(raw_url)
    if url.drivername == "postgres":
        url = url.set(drivername="postgresql+psycopg2")
    if url.host and url.host.endswith(".neon.tech") and "sslmode" not in url.query:
        url = url.update_query_dict({"sslmode": "require"})
    return url


engine = create_engine(database_url(settings.DATABASE_URL), pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    if settings.DATABASE_URL_UNPOOLED:
        schema_engine = create_engine(database_url(settings.DATABASE_URL_UNPOOLED), pool_pre_ping=True)
        try:
            Base.metadata.create_all(bind=schema_engine)
        finally:
            schema_engine.dispose()
    else:
        Base.metadata.create_all(bind=engine)
