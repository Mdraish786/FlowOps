"""Explicit local administration; never exposed as HTTP endpoints."""
import argparse,getpass,json,os,secrets
from pathlib import Path
from sqlalchemy import select
from cryptography.fernet import Fernet
import pyotp
from .database import Base,engine,SessionLocal
from .models import User,Workflow,ApprovalRequest,AuditLog
from .security import passwords
from .config import settings

def seed():
    s=settings()
    if s.environment == 'production': raise SystemExit('Demo seeding is disabled in production.')
    password=s.demo_password
    if len(password)<12: raise SystemExit('Set DEMO_PASSWORD to at least 12 characters before seeding.')
    source=json.loads((Path(__file__).parent/'seed.json').read_text())
    with SessionLocal() as db:
        existing={u.email.lower():u for u in db.scalars(select(User)).all()}
        if not existing:
            for p in source['people']:
                db.add(User(**{k:v for k,v in p.items() if k!='manager_id'},password_hash=passwords.hash(password)))
            db.flush()
            for p in source['people']:
                u=db.get(User,p['id']);u.manager_id=p.get('manager_id')
            # Managers and department staff report to the designated cross-team manager.
            for uid in [2,3,4,5,6,7]: db.get(User,uid).manager_id=10
            db.get(User,10).manager_id=2
            for f in source['flows']: db.add(Workflow(**f))
            db.flush()
            for row in source['requests']:
                owner=db.get(User,row['owner_id'])
                flows=[f for f in source['flows'] if f['category']==row['category'] and f['min_amount']<=row['amount'] and (f['max_amount'] is None or row['amount']<=f['max_amount'])]
                db.add(ApprovalRequest(**{k:v for k,v in row.items() if k not in ['owner','department','comments','attachments']},workflow_id=flows[0]['id'],manager_id=owner.manager_id))
            db.flush()
            for a in source['audit']: db.add(AuditLog(**a))
            if db.bind.dialect.name=='postgresql':
                from sqlalchemy import text
                for table in ['users','workflow_rules','requests','audit_logs']:
                    db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}','id'), COALESCE((SELECT MAX(id) FROM {table}),1))"))
        demo_email='demo@flowops.app'
        if demo_email not in existing:
            db.add(User(name='Demo Viewer',email=demo_email,password_hash=passwords.hash(password),role='Demo',department='Operations',manager_id=None,active=True))
            print('Demo Viewer added. Sign in at demo@flowops.app with your DEMO_PASSWORD.')
        else:
            print('Demo Viewer already exists; production data left untouched.')
        db.commit()
    print('Sample workspace ready. Sign in with a seeded email and your DEMO_PASSWORD.')
def create_admin():
    email=input('Admin email: ').strip().lower();name=input('Admin name: ').strip()
    password=getpass.getpass('Password (12+ characters): ')
    if len(password)<12: raise SystemExit('Password too short.')
    with SessionLocal() as db:
        db.add(User(name=name,email=email,password_hash=passwords.hash(password),role='Admin',department='Operations'));db.commit()
    print('Admin created. Enroll MFA before production login.')
def enroll(email):
    key=settings().mfa_encryption_key
    if not key: raise SystemExit('Set MFA_ENCRYPTION_KEY to a Fernet key first.')
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if not user: raise SystemExit('Account not found.')
        secret=pyotp.random_base32()
        print('Add this secret to the account owner’s authenticator over a trusted local channel: '+secret)
        code=input('Enter the six-digit code to confirm enrollment: ').strip()
        if not pyotp.TOTP(secret).verify(code): raise SystemExit('Code did not match; enrollment was not saved.')
        user.mfa_secret=Fernet(key.encode()).encrypt(secret.encode()).decode();user.mfa_last_counter=0;db.commit()
        print('Authenticator enrolled.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['init','seed','create-admin','enroll-mfa']);parser.add_argument('--email');args=parser.parse_args()
    if args.command=='init':
        if settings().secure: raise SystemExit('Use Alembic migrations in production.')
        Base.metadata.create_all(engine);print('Development schema created.')
    elif args.command=='seed': seed()
    elif args.command=='create-admin': create_admin()
    elif args.command=='enroll-mfa': enroll(args.email)
