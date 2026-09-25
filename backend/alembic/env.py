from alembic import context
from app.database import Base,engine
from app import models
config=context.config
def offline():
    from app.config import settings
    context.configure(url=settings().database_url,target_metadata=Base.metadata,literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
def online():
    with engine.connect() as conn:
        context.configure(connection=conn,target_metadata=Base.metadata)
        with context.begin_transaction(): context.run_migrations()
offline() if context.is_offline_mode() else online()
