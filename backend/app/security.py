import hashlib,secrets,time,threading
from collections import defaultdict
import jwt,pyotp,redis
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError,InvalidHashError
from cryptography.fernet import Fernet
from fastapi import Depends,HTTPException,Request,Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import db_session
from .models import User,LoginSession
s=settings()
passwords=PasswordHasher()
dummy_hash=passwords.hash(secrets.token_urlsafe(32))
redis_client=redis.Redis.from_url(s.redis_url) if s.redis_url else None
buckets=defaultdict(list)
bucket_lock=threading.Lock()
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def rate_limit(key,limit=8,seconds=300):
    key='flowops:rate:'+digest(key)
    if redis_client:
        try:
            count=redis_client.eval("local c=redis.call('INCR',KEYS[1]); if c==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return c",1,key,seconds)
        except redis.RedisError: raise HTTPException(503,'Security service unavailable. Try again shortly.')
    else:
        with bucket_lock:
            now=time.time()
            buckets[key]=[t for t in buckets[key] if t>now-seconds]
            buckets[key].append(now)
            count=len(buckets[key])
            if len(buckets)>10000:
                for old in list(buckets)[:5000]:
                    if old!=key: buckets.pop(old,None)
    if count>limit: raise HTTPException(429,'Too many attempts. Please wait and try again.',headers={'Retry-After':str(seconds)})
def verify(password,hashed):
    try: return passwords.verify(hashed,password)
    except (VerifyMismatchError,InvalidHashError): return False

def user_dict(u): return {k:getattr(u,k) for k in ('id','name','email','role','department','manager_id','active')}
def current_user(request:Request,db:Session=Depends(db_session)):
    token=request.cookies.get('flowops_access')
    auth=request.headers.get('authorization','')
    if auth.startswith('Bearer '): token=auth[7:]
    try:
        data=jwt.decode(token,s.jwt_secret,algorithms=['HS256'],issuer='flowops',audience='flowops',options={'require':['exp','iat','sub','sid']})
        session=db.get(LoginSession,data['sid'])
        if not session or session.revoked or session.expires<time.time() or str(session.user_id)!=data['sub']: raise ValueError()
        user=db.get(User,session.user_id)
        if not user or not user.active: raise ValueError()
        return user
    except (jwt.PyJWTError,ValueError,TypeError): raise HTTPException(401,'Please sign in to continue.')
def admin(user:User=Depends(current_user)):
    if user.role=='Demo': raise HTTPException(403,'Demo account is read-only.')
    if user.role!='Admin': raise HTTPException(403,'Administrator access required.')
    return user

def demo_read_only(user:User=Depends(current_user)):
    if user.role=='Demo': raise HTTPException(403,'Demo account is read-only.')
    return user

def issue(db,user,response,session=None):
    token=secrets.token_urlsafe(48)
    if session is None:
        session=LoginSession(id=secrets.token_hex(24),user_id=user.id,refresh_hash=digest(token),expires=time.time()+7*86400)
        db.add(session)
    else:
        session.refresh_hash=digest(token)
    db.flush()
    now=int(time.time())
    access=jwt.encode({'sub':str(user.id),'sid':session.id,'iat':now,'exp':now+900,'iss':'flowops','aud':'flowops'},s.jwt_secret,algorithm='HS256')
    response.set_cookie('flowops_access',access,max_age=900,httponly=True,secure=s.secure,samesite='strict',path='/')
    response.set_cookie('flowops_refresh',session.id+'.'+token,max_age=max(1,int(session.expires-time.time())),httponly=True,secure=s.secure,samesite='strict',path='/')
    return access

def verify_otp(user,code):
    if not user.mfa_secret: return not(s.require_mfa and user.role in ['Admin','Finance','IT','Director'])
    if not s.mfa_encryption_key or not code: return False
    secret=Fernet(s.mfa_encryption_key.encode()).decrypt(user.mfa_secret.encode()).decode()
    counter=int(time.time())//30
    if counter<=user.mfa_last_counter or not pyotp.TOTP(secret).verify(code,valid_window=0): return False
    user.mfa_last_counter=counter
    return True
