import copy
from sqlalchemy import select
from fastapi import HTTPException
from .models import User,Workflow,ApprovalRequest,Comment,Attachment,AuditLog,Notification,now

def can_view(r,u):
    return u.role=='Admin' or r.owner_id==u.id or u.role=='Manager' and r.manager_id==u.id or u.role not in ['Employee','Manager'] and any(s['role']==u.role for s in r.steps)
def can_approve(r,u):
    step=next((s for s in r.steps if s['status']=='Pending'),None)
    return r.status=='Pending' and r.owner_id!=u.id and step and step['role']==u.role and (u.role!='Manager' or r.manager_id==u.id)
def load_request(db,rid,user,lock=False):
    q=select(ApprovalRequest).where(ApprovalRequest.id==rid)
    if lock: q=q.with_for_update()
    r=db.scalar(q)
    if not r: raise HTTPException(404,'Request not found.')
    if not can_view(r,user): raise HTTPException(403,'You cannot access this request.')
    return r

def log(db,user,action,target,request_id=None):
    db.add(AuditLog(actor_id=user.id if user else None,actor=user.name if user else 'Unknown account',action=action,target=target,request_id=request_id))
def notify(db,r,message):
    ids={r.owner_id}
    current=next((s for s in r.steps if s['status']=='Pending'),None)
    if current and r.status=='Pending':
        if current['role']=='Manager': ids.add(r.manager_id)
        else: ids.update(db.scalars(select(User.id).where(User.role==current['role'],User.active==True)).all())
    for uid in ids:
        if uid: db.add(Notification(user_id=uid,request_id=r.id,message=message))
def request_dict(db,r):
    owner=db.get(User,r.owner_id)
    data={k:getattr(r,k) for k in ('id','title','category','amount','reason','priority','status','owner_id','manager_id','created_at','steps','version')}
    data['amount']=float(data['amount'])
    data.update(owner=owner.name,department=owner.department)
    data['comments']=[{'id':c.id,'author':db.get(User,c.author_id).name,'text':c.text,'at':c.at} for c in db.scalars(select(Comment).where(Comment.request_id==r.id).order_by(Comment.id))]
    data['attachments']=[{'id':a.id,'name':a.name,'size':a.size} for a in db.scalars(select(Attachment).where(Attachment.request_id==r.id))]
    return data

def choose_workflow(db,category,amount):
    matches=[w for w in db.scalars(select(Workflow).where(Workflow.category==category,Workflow.active==True)) if w.min_amount<=amount and (w.max_amount is None or amount<=w.max_amount)]
    if len(matches)!=1: raise HTTPException(422,'No unique active workflow matches this request. Contact your admin.')
    return matches[0]
def check_workflow_overlap(db,data,exclude=None):
    if not data.active: return
    # PostgreSQL advisory lock serializes concurrent workflow edits per category.
    if db.bind.dialect.name=='postgresql':
        from sqlalchemy import text
        db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:category))'),{'category':data.category})
    for f in db.scalars(select(Workflow).where(Workflow.category==data.category,Workflow.active==True)):
        if f.id!=exclude and f.min_amount <= (data.max_amount if data.max_amount is not None else float('inf')) and data.min_amount <= (f.max_amount if f.max_amount is not None else float('inf')):
            raise HTTPException(409,'This amount range overlaps an active workflow.')

def transition(db,r,u,action,data):
    if r.version!=data.version: raise HTTPException(409,'This request changed. Refresh before making a decision.')
    if action=='cancel':
        if r.owner_id!=u.id or r.status not in ['Pending','Needs information']: raise HTTPException(403,'You cannot cancel this request.')
        r.status='Cancelled'
    elif action=='resubmit':
        if r.owner_id!=u.id or r.status!='Needs information': raise HTTPException(403,'You cannot resubmit this request.')
        if len(data.comment)<3: raise HTTPException(422,'Add the requested information.')
        r.status='Pending'
    else:
        if not can_approve(r,u): raise HTTPException(403,'This approval step is not assigned to you.')
        if action in ['reject','request-info'] and len(data.comment)<3: raise HTTPException(422,'Add a reason for your decision.')
        steps=copy.deepcopy(r.steps)
        idx=next(i for i,s in enumerate(steps) if s['status']=='Pending')
        if action=='approve':
            steps[idx].update(status='Approved',actor=u.name,at=now(),comment=data.comment)
            if idx+1<len(steps): steps[idx+1]['status']='Pending'
            else: r.status='Approved'
        elif action=='reject':
            steps[idx].update(status='Rejected',actor=u.name,at=now(),comment=data.comment)
            r.status='Rejected'
        elif action=='request-info': r.status='Needs information'
        else: raise HTTPException(404,'Unknown action.')
        r.steps=steps
    # Force a versioned UPDATE even when asking for info or approving a middle step.
    r.version += 1
    if data.comment: db.add(Comment(request_id=r.id,author_id=u.id,text=data.comment))
    action_name={'approve':'Approved step','reject':'Rejected request','request-info':'Requested information','cancel':'Cancelled request','resubmit':'Resubmitted request'}[action]
    log(db,u,action_name,'REQ-'+str(r.id),r.id)
    notify(db,r,action_name+': '+r.title)
