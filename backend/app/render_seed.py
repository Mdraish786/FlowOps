"""Idempotent demo seeding for a Render/staging deployment."""
from sqlalchemy import select
from .database import SessionLocal
from .models import User
from .manage import seed

with SessionLocal() as db:
    exists = db.scalar(select(User.id).limit(1))

if exists:
    print('FlowOps database already contains users; demo seed skipped.')
else:
    seed()
