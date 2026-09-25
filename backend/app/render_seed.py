"""Idempotent demo seeding for a Render/staging deployment."""
from sqlalchemy import select
from .database import SessionLocal
from .models import User
from .manage import seed

with SessionLocal() as db:
    exists = db.scalar(select(User.id).limit(1))
    demo_exists = db.scalar(select(User.id).where(User.email == 'demo@flowops.app'))

if exists and demo_exists:
    print('FlowOps database already contains users and Demo Viewer already exists; demo seed skipped.')
elif exists and not demo_exists:
    print('Existing database detected; creating Demo Viewer without overwriting production users.')
    from .manage import seed
    seed()
else:
    seed()
