from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine
from backend.app.core.config import settings

engine = create_engine(settings.DATABASE_URL,pool_pre_ping=True)
sessionlocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()
def get_db():
    db = sessionlocal()
    try :
        yield db
    finally:
        db.close()

