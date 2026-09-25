from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings

class Base(DeclarativeBase): pass
database_url=settings().database_url
if database_url.startswith('postgres://'):
    database_url='postgresql+psycopg://'+database_url[len('postgres://'):]
elif database_url.startswith('postgresql://'):
    database_url='postgresql+psycopg://'+database_url[len('postgresql://'):]
engine = create_engine(database_url, pool_pre_ping=True, connect_args={'check_same_thread': False} if database_url.startswith('sqlite') else {})
SessionLocal = sessionmaker(engine, expire_on_commit=False)
def db_session():
    with SessionLocal() as db:
        try: yield db
        except Exception:
            db.rollback()
            raise
