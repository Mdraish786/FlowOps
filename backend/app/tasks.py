import smtplib
from email.message import EmailMessage
from datetime import datetime,timezone,timedelta
from celery import Celery
from sqlalchemy import select
from .config import settings
from .database import SessionLocal
from .models import User,Notification,ApprovalRequest,AuditLog
from .services import notify
s=settings()
celery=Celery('flowops',broker=s.redis_url or 'memory://')
celery.conf.update(accept_content=['json'],task_serializer='json',result_serializer='json',timezone='UTC',beat_schedule={'mail-outbox':{'task':'app.tasks.send_notifications','schedule':60.0},'approval-reminders':{'task':'app.tasks.reminders','schedule':3600.0}})
def mail(to,subject,text):
    if not s.smtp_host: raise RuntimeError('SMTP is not configured')
    m=EmailMessage();m['From']=s.smtp_from;m['To']=to;m['Subject']=subject;m.set_content(text)
    with smtplib.SMTP(s.smtp_host,s.smtp_port,timeout=20) as server:
        if s.smtp_starttls: server.starttls()
        if s.smtp_username: server.login(s.smtp_username,s.smtp_password)
        server.send_message(m)
@celery.task(name='app.tasks.send_reset',autoretry_for=(Exception,),retry_backoff=True,max_retries=3)
def send_reset(email,token):
    mail(email,'Reset your FlowOps password','Open '+s.frontend_origin+' and choose Forgot password, then enter this reset token:\n\n'+token+'\n\nThe token expires in 30 minutes.')
@celery.task(name='app.tasks.send_notifications')
def send_notifications():
    if not s.smtp_host: return {'skipped':'SMTP not configured'}
    with SessionLocal() as db:
        rows=db.scalars(select(Notification).where(Notification.emailed==False).with_for_update(skip_locked=True).limit(50)).all()
        for n in rows:
            user=db.get(User,n.user_id)
            if not user or not user.active: n.emailed=True;continue
            mail(user.email,'FlowOps request update',n.message+'\n\nOpen your workspace: '+s.frontend_origin)
            n.emailed=True
        db.commit()
    return {'sent':len(rows)}
@celery.task(name='app.tasks.reminders')
def reminders():
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=24)).isoformat()
    day=datetime.now(timezone.utc).date().isoformat()
    with SessionLocal() as db:
        for r in db.scalars(select(ApprovalRequest).where(ApprovalRequest.status=='Pending',ApprovalRequest.created_at<cutoff).with_for_update(skip_locked=True)):
            marker=f'Reminder {day}'
            if db.scalar(select(AuditLog.id).where(AuditLog.request_id==r.id,AuditLog.action==marker)): continue
            notify(db,r,'Reminder: '+r.title+' is waiting for review.')
            db.add(AuditLog(actor='FlowOps',action=marker,target='REQ-'+str(r.id),request_id=r.id))
            if r.created_at < (datetime.now(timezone.utc)-timedelta(hours=48)).isoformat():
                for director in db.scalars(select(User).where(User.role=='Director',User.active==True)):
                    db.add(Notification(user_id=director.id,request_id=r.id,message='Escalation: '+r.title+' has been waiting more than 48 hours.'))
        db.commit()
