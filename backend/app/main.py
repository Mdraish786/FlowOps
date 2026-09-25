import asyncio,io,os,secrets,time,zipfile
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException,Request,Response,UploadFile,File,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from sqlalchemy import select,update
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from .config import settings
from .database import db_session,SessionLocal,engine
from .models import *
from .schemas import *
from .security import current_user,admin,passwords,verify,verify_otp,issue,digest,rate_limit,user_dict,dummy_hash
from .services import *
s=settings()
app=FastAPI(title='FlowOps API',version='1.0.0',docs_url='/docs' if not s.secure else None,redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=[s.frontend_origin],allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','Authorization'])

@app.middleware('http')
async def protection(request:Request,call_next):
    if request.method not in ['GET','HEAD','OPTIONS']:
        origin=request.headers.get('origin')
        # SameSite cookies plus strict Origin checks protect every cookie-auth mutation.
        if (origin and origin!=s.frontend_origin) or (request.cookies and not origin and not request.headers.get('authorization')):
            return JSONResponse({'detail':'Origin not allowed.'},status_code=403)
        length=request.headers.get('content-length')
        if length and (not length.isdigit() or int(length)>6*1024*1024):
            return JSONResponse({'detail':'Request too large.'},status_code=413)
    result=await call_next(request)
    result.headers['X-Content-Type-Options']='nosniff'
    result.headers['X-Frame-Options']='DENY'
    result.headers['Referrer-Policy']='same-origin'
    result.headers['Cache-Control']='no-store'
    if s.secure: result.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return result

@app.exception_handler(StaleDataError)
async def stale(request,exc): return JSONResponse({'detail':'This record changed. Refresh and try again.'},status_code=409)
@app.exception_handler(IntegrityError)
async def integrity(request,exc): return JSONResponse({'detail':'That record already exists or references an invalid account.'},status_code=409)
@app.get('/health')
def health():
    from sqlalchemy import text
    with engine.connect() as conn: conn.execute(text('SELECT 1'))
    return {'status':'ok'}

@app.post('/auth/login')
def login(data:Login,request:Request,response:Response,db:Session=Depends(db_session)):
    ip=request.client.host if request.client else 'unknown'
    rate_limit('login:ip:'+ip,30)
    rate_limit('login:account:'+data.email.lower(),8)
    user=db.scalar(select(User).where(User.email==data.email.lower()).with_for_update())
    valid=verify(data.password,user.password_hash if user else dummy_hash)
    if not user or not valid or not user.active or not verify_otp(user,data.otp):
        log(db,user,'Failed login','Authentication');db.commit()
        raise HTTPException(401,'Invalid email, password, or authenticator code.')
    issue(db,user,response);log(db,user,'Signed in','Authentication');db.commit()
    return user_dict(user)

@app.post('/auth/refresh')
def refresh(request:Request,response:Response,db:Session=Depends(db_session)):
    rate_limit('refresh:'+(request.client.host if request.client else 'unknown'),60,60)
    raw=request.cookies.get('flowops_refresh','')
    try: sid,token=raw.split('.',1)
    except ValueError: raise HTTPException(401,'Sign in again.')
    session=db.scalar(select(LoginSession).where(LoginSession.id==sid).with_for_update())
    if not session or session.revoked or session.expires<time.time(): raise HTTPException(401,'Sign in again.')
    if not secrets.compare_digest(session.refresh_hash,digest(token)):
        session.revoked=True;db.commit();raise HTTPException(401,'Session has been revoked.')
    user=db.get(User,session.user_id)
    if not user or not user.active: raise HTTPException(401,'Account unavailable.')
    issue(db,user,response,session);db.commit()
    return {'ok':True}

@app.post('/auth/logout')
def logout(request:Request,response:Response,db:Session=Depends(db_session)):
    sid=request.cookies.get('flowops_refresh','').split('.')[0]
    session=db.get(LoginSession,sid)
    if session:
        session.revoked=True;log(db,db.get(User,session.user_id),'Signed out','Authentication');db.commit()
    response.delete_cookie('flowops_access',path='/');response.delete_cookie('flowops_refresh',path='/')
    return {'ok':True}

@app.post('/auth/forgot-password')
def forgot(data:Forgot,request:Request,db:Session=Depends(db_session)):
    rate_limit('reset:'+data.email.lower(),3,900)
    rate_limit('reset-ip:'+(request.client.host if request.client else 'unknown'),12,900)
    user=db.scalar(select(User).where(User.email==data.email.lower(),User.active==True))
    if user:
        token=secrets.token_urlsafe(48)
        db.add(ResetToken(token_hash=digest(token),user_id=user.id,expires=time.time()+1800))
        log(db,user,'Requested password reset','Authentication');db.commit()
        # Queue the same task shape for known/unknown accounts to avoid mail latency leaking account existence.
        if s.redis_url:
            from .tasks import send_reset
            send_reset.delay(user.email,token)
    return {'message':'If that account exists, reset instructions will be sent. Contact your admin if no email arrives.'}

@app.post('/auth/reset-password')
def reset(data:Reset,db:Session=Depends(db_session)):
    row=db.scalar(select(ResetToken).where(ResetToken.token_hash==digest(data.token)).with_for_update())
    if not row or row.expires<time.time(): raise HTTPException(400,'Reset token is invalid or expired.')
    user=db.get(User,row.user_id)
    user.password_hash=passwords.hash(data.password)
    db.execute(update(LoginSession).where(LoginSession.user_id==user.id).values(revoked=True))
    for token in db.scalars(select(ResetToken).where(ResetToken.user_id==user.id)): db.delete(token)
    log(db,user,'Reset password','Authentication');db.commit()
    return {'ok':True}

@app.get('/users/me')
def me(user:User=Depends(current_user)): return user_dict(user)
@app.get('/users')
def users(user:User=Depends(current_user),db:Session=Depends(db_session)):
    # Only return the minimum directory needed for ownership and manager checks.
    rows=db.scalars(select(User)).all()
    if user.role=='Admin': return [user_dict(u) for u in rows]
    return [user_dict(u) for u in rows if u.id==user.id or u.manager_id==user.id or u.department==user.department or u.id==user.manager_id]
@app.get('/workflows')
def workflows(user:User=Depends(current_user),db:Session=Depends(db_session)):
    return [{**{k:getattr(w,k) for k in ('id','name','category','roles','active')},'min_amount':float(w.min_amount),'max_amount':float(w.max_amount) if w.max_amount is not None else None} for w in db.scalars(select(Workflow).order_by(Workflow.id))]

@app.get('/requests')
def requests(user:User=Depends(current_user),db:Session=Depends(db_session)):
    return [request_dict(db,r) for r in db.scalars(select(ApprovalRequest).order_by(ApprovalRequest.id.desc())) if can_view(r,user)]
@app.get('/requests/{rid}')
def detail(rid:int,user:User=Depends(current_user),db:Session=Depends(db_session)):
    return request_dict(db,load_request(db,rid,user))
@app.post('/requests',status_code=201)
def create_request(data:NewRequest,user:User=Depends(current_user),db:Session=Depends(db_session)):
    rate_limit('create:'+str(user.id),30,60)
    flow=choose_workflow(db,data.category,data.amount)
    if 'Manager' in flow.roles and not user.manager_id: raise HTTPException(422,'Your administrator must assign a manager before you submit this request.')
    if user.manager_id==user.id: raise HTTPException(422,'Your manager cannot be yourself.')
    r=ApprovalRequest(**data.model_dump(),owner_id=user.id,manager_id=user.manager_id,workflow_id=flow.id,steps=[{'role':role,'status':'Pending' if i==0 else 'Waiting'} for i,role in enumerate(flow.roles)])
    db.add(r);db.flush();log(db,user,'Submitted request','REQ-'+str(r.id),r.id);notify(db,r,'New request: '+r.title);db.commit()
    return request_dict(db,r)
@app.post('/requests/{rid}/{action}')
def decision(rid:int,action:str,data:Decision,user:User=Depends(current_user),db:Session=Depends(db_session)):
    # Explicitly limited action set keeps resource routes below unambiguous.
    if action not in ['approve','reject','request-info','cancel','resubmit']: raise HTTPException(404,'Action not found.')
    r=load_request(db,rid,user,lock=True)
    transition(db,r,user,action,data);db.commit()
    return request_dict(db,r)
# Resource paths have two suffix segments so they never match the decision path.
@app.post('/requests/{rid}/comments/add',status_code=201)
def add_comment(rid:int,data:NewComment,user:User=Depends(current_user),db:Session=Depends(db_session)):
    r=load_request(db,rid,user)
    rate_limit('comment:'+str(user.id),60,60)
    db.add(Comment(request_id=rid,author_id=user.id,text=data.text));log(db,user,'Added comment','REQ-'+str(rid),rid);notify(db,r,'New comment: '+r.title);db.commit()
    return request_dict(db,r)

@app.get('/activity')
def activity(user:User=Depends(current_user),db:Session=Depends(db_session)):
    visible_ids={r.id for r in db.scalars(select(ApprovalRequest)) if can_view(r,user)}
    logs=db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(2000))
    return [{k:getattr(a,k) for k in ('id','actor','action','target','at')} for a in logs if user.role=='Admin' or a.request_id in visible_ids or a.actor_id==user.id][:200]
@app.get('/notifications')
def notifications(user:User=Depends(current_user),db:Session=Depends(db_session)):
    return [{k:getattr(n,k) for k in ('id','request_id','message','at','read')} for n in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.id.desc()).limit(200))]
@app.post('/notifications/read')
def read_notifications(user:User=Depends(current_user),db:Session=Depends(db_session)):
    db.execute(update(Notification).where(Notification.user_id==user.id).values(read=True));db.commit();return {'ok':True}
@app.get('/analytics/dashboard')
def analytics(user:User=Depends(current_user),db:Session=Depends(db_session)):
    rows=[r for r in db.scalars(select(ApprovalRequest)) if can_view(r,user)]
    return {'total':len(rows),'pending':sum(r.status=='Pending' for r in rows),'approved':sum(r.status=='Approved' for r in rows),'pending_value':sum(float(r.amount) for r in rows if r.status=='Pending')}

@app.post('/admin/users',status_code=201)
def new_user(data:NewUser,user:User=Depends(admin),db:Session=Depends(db_session)):
    if data.role=='Employee' and not data.manager_id: raise HTTPException(422,'Employees need an assigned manager.')
    if data.manager_id:
        manager=db.get(User,data.manager_id)
        if not manager or not manager.active or manager.role!='Manager': raise HTTPException(422,'Choose an active manager.')
    u=User(**data.model_dump(exclude={'password'}),password_hash=passwords.hash(data.password));u.email=u.email.lower()
    db.add(u);db.flush();log(db,user,'Created account',u.email);db.commit();return user_dict(u)
@app.put('/admin/users/{uid}')
def edit_user(uid:int,data:EditUser,user:User=Depends(admin),db:Session=Depends(db_session)):
    if uid==user.id: raise HTTPException(403,'You cannot change your own administrative access.')
    target=db.get(User,uid)
    if not target: raise HTTPException(404,'Account not found.')
    if data.manager_id is not None:
        manager=db.get(User,data.manager_id)
        if data.manager_id==uid or not manager or not manager.active or manager.role!='Manager': raise HTTPException(422,'Choose another active manager.')
    if target.role=='Manager' and (data.active is False or data.role and data.role!='Manager'):
        if db.scalar(select(User.id).where(User.manager_id==uid,User.active==True).limit(1)): raise HTTPException(409,'Reassign this manager’s employees before changing their access.')
    for k,v in data.model_dump(exclude_unset=True).items():
        if v is not None: setattr(target,k,v)
    db.execute(update(LoginSession).where(LoginSession.user_id==uid).values(revoked=True))
    log(db,user,'Updated account access',target.email);db.commit();return user_dict(target)
@app.post('/admin/workflows',status_code=201)
def new_workflow(data:NewWorkflow,user:User=Depends(admin),db:Session=Depends(db_session)):
    check_workflow_overlap(db,data)
    w=Workflow(**data.model_dump(exclude={'id'}));db.add(w);log(db,user,'Created workflow',w.name);db.commit();return {'id':w.id}
@app.put('/admin/workflows/{wid}')
def edit_workflow(wid:int,data:NewWorkflow,user:User=Depends(admin),db:Session=Depends(db_session)):
    w=db.scalar(select(Workflow).where(Workflow.id==wid).with_for_update())
    if not w: raise HTTPException(404,'Workflow not found.')
    check_workflow_overlap(db,data,wid)
    for k,v in data.model_dump(exclude={'id'}).items(): setattr(w,k,v)
    log(db,user,'Updated workflow',w.name);db.commit();return {'id':w.id}

@app.post('/requests/{rid}/attachments/upload',status_code=201)
async def upload(rid:int,file:UploadFile=File(...),user:User=Depends(current_user),db:Session=Depends(db_session)):
    r=load_request(db,rid,user)
    if r.owner_id!=user.id or r.status not in ['Pending','Needs information']: raise HTTPException(403,'Attachments can only be added to your active requests.')
    if len(db.scalars(select(Attachment).where(Attachment.request_id==rid)).all())>=10: raise HTTPException(422,'Maximum 10 attachments per request.')
    rate_limit('upload:'+str(user.id),15,60)
    data=await file.read(5*1024*1024+1)
    if not data or len(data)>5*1024*1024: raise HTTPException(413,'Upload must be between 1 byte and 5 MB.')
    name=Path((file.filename or '').replace('\\','/')).name[:180]
    ext=Path(name).suffix.lower()
    kinds={'.pdf':'application/pdf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
    mime=kinds.get(ext)
    valid=(ext=='.pdf' and data.startswith(b'%PDF-')) or (ext=='.png' and data.startswith(b'\x89PNG\r\n\x1a\n')) or (ext in ['.jpg','.jpeg'] and data.startswith(b'\xff\xd8\xff'))
    if ext=='.docx':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names=z.namelist()
                valid='[Content_Types].xml' in names and 'word/document.xml' in names and len(names)<2000 and sum(x.file_size for x in z.infolist())<30*1024*1024 and not any('vbaProject' in n for n in names)
        except zipfile.BadZipFile: valid=False
    if not mime or not valid or file.content_type!=mime: raise HTTPException(415,'File type does not match a supported PDF, image, or DOCX document.')
    if s.require_malware_scan:
        import clamd
        try:
            result=await asyncio.to_thread(clamd.ClamdNetworkSocket(s.clamav_host,3310,timeout=30).instream,io.BytesIO(data))
        except Exception: raise HTTPException(503,'File scanner unavailable. Try again later.')
        if not result or result.get('stream',('ERROR',))[0]!='OK': raise HTTPException(422,'File did not pass security scanning.')
    root=Path(s.upload_dir);root.mkdir(parents=True,exist_ok=True)
    stored=secrets.token_hex(24)+ext;path=root/stored
    path.write_bytes(data)
    try:
        a=Attachment(request_id=rid,name=name,stored_name=stored,mime=mime,size=len(data));db.add(a);log(db,user,'Uploaded attachment','REQ-'+str(rid),rid);db.commit()
    except Exception:
        path.unlink(missing_ok=True);raise
    return {'id':a.id,'name':a.name,'size':a.size}
@app.get('/attachments/{aid}')
def download(aid:int,user:User=Depends(current_user),db:Session=Depends(db_session)):
    a=db.get(Attachment,aid)
    if not a: raise HTTPException(404,'Attachment not found.')
    load_request(db,a.request_id,user)
    path=Path(s.upload_dir)/a.stored_name
    if not path.exists(): raise HTTPException(404,'Attachment unavailable.')
    return FileResponse(path,media_type='application/octet-stream',filename=a.name,headers={'Content-Security-Policy':"default-src 'none'; sandbox"})

@app.websocket('/ws/notifications')
async def ws_notifications(ws:WebSocket):
    if ws.headers.get('origin')!=s.frontend_origin: await ws.close(code=1008);return
    with SessionLocal() as db:
        try: user=current_user(ws,db)
        except HTTPException: await ws.close(code=1008);return
        uid=user.id
    await ws.accept()
    last=0
    try:
        while True:
            with SessionLocal() as db:
                try: current_user(ws,db) # Re-check expiry and revocation for the connection.
                except HTTPException: await ws.close(code=1008);return
                rows=db.scalars(select(Notification).where(Notification.user_id==uid,Notification.id>last).order_by(Notification.id)).all()
                if rows:
                    await ws.send_json([{'id':n.id,'message':n.message,'request_id':n.request_id} for n in rows]);last=rows[-1].id
            await asyncio.sleep(3)
    except (WebSocketDisconnect,RuntimeError): pass


# Render/single-service mode: expose the API under /api and serve the built React app
# from the same HTTPS origin. Local development keeps the original API-only layout.
if os.getenv('SERVE_FRONTEND','').lower() in {'1','true','yes'}:
    from fastapi.staticfiles import StaticFiles
    api_app=app
    shell=FastAPI(title='FlowOps',docs_url=None,redoc_url=None)
    shell.mount('/api',api_app)
    frontend_dir=Path(os.getenv('FRONTEND_DIST','/app/frontend-dist'))
    if not frontend_dir.exists():
        raise RuntimeError(f'Frontend build not found at {frontend_dir}')
    shell.mount('/',StaticFiles(directory=str(frontend_dir),html=True),name='frontend')
    app=shell
