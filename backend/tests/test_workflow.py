import os,tempfile,time
from pathlib import Path
os.environ.update(JWT_SECRET='test-only-secret-at-least-thirty-two-characters',DATABASE_URL='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db'),FRONTEND_ORIGIN='http://localhost:5173',UPLOAD_DIR=tempfile.mkdtemp(),DEMO_PASSWORD='test-password-for-local-tests',REDIS_URL='',ENVIRONMENT='test')
import pytest,jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError
from app.main import app
from app.database import Base,engine,SessionLocal
from app.models import ApprovalRequest,AuditLog,Notification,ResetToken
from app.manage import seed
from app.security import buckets,digest
@pytest.fixture(autouse=True)
def setup():
    Base.metadata.drop_all(engine);Base.metadata.create_all(engine);buckets.clear();seed()
def client(email='arjun@flowops.local'):
    c=TestClient(app,headers={'Origin':'http://localhost:5173'})
    r=c.post('/auth/login',json={'email':email,'password':os.environ['DEMO_PASSWORD']})
    assert r.status_code==200,r.text
    return c
def create(c,amount=75000):
    r=c.post('/requests',json={'title':'Development laptop','category':'Equipment','amount':amount,'reason':'Replacement laptop for development and testing.','priority':'High'})
    assert r.status_code==201,r.text
    return r.json()
def act(c,r,action='approve',comment=''):
    return c.post(f"/requests/{r['id']}/{action}",json={'version':r['version'],'comment':comment})
def test_employee_object_security():
    c=client();assert all(r['owner_id']==1 for r in c.get('/requests').json())
    assert c.get('/requests/1047').status_code==403
    assert c.get('/requests/99999').status_code==404

def test_public_demo_auth_endpoint():
    c=TestClient(app,headers={'Origin':'http://localhost:5173'})
    r=c.post('/auth/demo')
    assert r.status_code==200,r.text
    body=r.json();assert body['role']=='Demo';assert body['email']=='demo@flowops.app'
    assert c.get('/users/me').json()['role']=='Demo'
    assert c.post('/requests',json={'title':'Should fail','category':'Equipment','amount':2500,'reason':'Public demo login cannot create requests.','priority':'Normal'}).status_code==403

def test_demo_read_only_account():
    d=client('demo@flowops.app');
    assert d.get('/users/me').json()['role']=='Demo'
    assert d.get('/requests').status_code==200
    assert d.get('/users').status_code==200
    assert d.get('/analytics/dashboard').status_code==200
    assert d.get('/workflows').status_code==200

    r=create(client())
    assert d.post('/requests',json={'title':'Should fail','category':'Equipment','amount':2500,'reason':'Demo is read only and cannot create requests.','priority':'Normal'}).status_code==403
    assert d.post(f"/requests/{r['id']}/comments/add",json={'text':'No comments allowed.'}).status_code==403
    assert d.post(f"/requests/{r['id']}/attachments/upload",files={'file':('note.pdf',b'%PDF-1.4\n test','application/pdf')}).status_code==403
    assert d.post('/notifications/read').status_code==403
    assert d.post('/admin/workflows',json={'name':'Demo workflow','category':'Equipment','min_amount':0,'max_amount':1000,'roles':['Manager','IT'],'active':True}).status_code==403
    assert d.put('/admin/users/1',json={'role':'Admin'}).status_code==403

def test_complete_multistage_workflow():
    r=create(client());assert [s['role'] for s in r['steps']]==['Manager','IT','Finance']
    for email in ['raish@flowops.local','neha@flowops.local','priya@flowops.local']:
        response=act(client(email),r,comment='Requirement verified.');assert response.status_code==200,response.text;r=response.json()
    assert r['status']=='Approved' and all(s['status']=='Approved' for s in r['steps']) and len(r['comments'])==3
    with SessionLocal() as db:
        assert len(db.scalars(select(AuditLog).where(AuditLog.request_id==r['id'])).all())==4
        assert db.scalar(select(Notification.id).where(Notification.request_id==r['id']))
def test_self_wrong_manager_out_of_order():
    e=client();r=create(e)
    assert act(e,r).status_code==403
    assert act(client('meera@flowops.local'),r).status_code==403
    assert act(client('priya@flowops.local'),r).status_code==403
    m=client('raish@flowops.local');own=create(m,1000)
    assert act(m,own).status_code==403
def test_stale_approval():
    r=create(client(),1000);m=client('raish@flowops.local')
    assert act(m,r).status_code==200
    assert act(m,r).status_code==409
def test_information_resubmit_rejection():
    e=client();r=create(e);m=client('raish@flowops.local')
    assert act(m,r,'request-info').status_code==422
    r=act(m,r,'request-info','Please add a quotation.').json();assert r['status']=='Needs information'
    r=act(e,r,'resubmit','Quotation supplied.').json();assert r['status']=='Pending'
    r=act(m,r,'reject','Budget not available.').json();assert r['status']=='Rejected'
def test_cancel_comments():
    e=client();r=create(e)
    assert act(client('sara@flowops.local'),r,'cancel').status_code==403
    response=e.post(f"/requests/{r['id']}/comments/add",json={'text':'Please review before Friday.'})
    assert response.status_code==201,response.text
    assert len(response.json()['comments'])==1
    assert act(e,r,'cancel').json()['status']=='Cancelled'
def test_refresh_rotation_logout():
    c=client();old=c.cookies.get('flowops_refresh');access=c.cookies.get('flowops_access')
    assert c.post('/auth/refresh').status_code==200
    assert old!=c.cookies.get('flowops_refresh')
    assert c.post('/auth/logout').status_code==200
    assert c.get('/users/me',headers={'Authorization':'Bearer '+access}).status_code==401
def test_refresh_replay_revokes():
    c=client();old=c.cookies.get('flowops_refresh');assert c.post('/auth/refresh').status_code==200
    replay=TestClient(app,headers={'Origin':'http://localhost:5173'});replay.cookies.set('flowops_refresh',old)
    assert replay.post('/auth/refresh').status_code==401
    assert c.get('/users/me').status_code==401
def test_csrf_privilege_escalation():
    c=client()
    assert c.post('/auth/logout',headers={'Origin':'https://evil.example'}).status_code==403
    assert c.put('/admin/users/1',json={'role':'Admin'}).status_code==403
def test_upload_access_and_type_validation():
    c=client();r=create(c);url=f"/requests/{r['id']}/attachments/upload"
    assert c.post(url,files={'file':('test.pdf',b'MZ fake file','application/pdf')}).status_code==415
    a=c.post(url,files={'file':('quote.pdf',b'%PDF-1.4\n test','application/pdf')});assert a.status_code==201,a.text
    assert c.get('/attachments/'+str(a.json()['id'])).status_code==200
    assert client('sara@flowops.local').get('/attachments/'+str(a.json()['id'])).status_code==403
def test_workflow_overlap_and_snapshot():
    e=client();r=create(e);a=client('admin@flowops.local')
    body={'name':'Revised high value','category':'Equipment','min_amount':50000.01,'max_amount':100000,'roles':['Manager','Finance'],'active':True}
    assert a.put('/admin/workflows/3',json=body).status_code==200
    assert len(e.get('/requests/'+str(r['id'])).json()['steps'])==3
    assert len(create(e)['steps'])==2
    assert a.post('/admin/workflows',json=body).status_code==409
def test_validation_rate_limiting():
    c=client();assert c.post('/requests',json={'title':'Valid title','category':'Equipment','amount':-1,'reason':'Valid business reason.'}).status_code==422
    a=TestClient(app);responses=[a.post('/auth/login',json={'email':'unknown@example.com','password':'wrong'}).status_code for _ in range(9)]
    assert responses[-1]==429
def test_expired_token():
    c=client();data=jwt.decode(c.cookies.get('flowops_access'),os.environ['JWT_SECRET'],algorithms=['HS256'],audience='flowops',issuer='flowops');data['exp']=int(time.time())-10
    bad=jwt.encode(data,os.environ['JWT_SECRET'],algorithm='HS256')
    assert c.get('/users/me',headers={'Authorization':'Bearer '+bad}).status_code==401
def test_optimistic_concurrency():
    r=create(client())
    with SessionLocal() as a,SessionLocal() as b:
        ra=a.get(ApprovalRequest,r['id']);rb=b.get(ApprovalRequest,r['id']);ra.status='Cancelled';a.commit();rb.status='Rejected'
        with pytest.raises(StaleDataError): b.commit()
def test_single_use_reset_revokes():
    c=client();token='unique-test-password-reset-token'
    with SessionLocal() as db: db.add(ResetToken(token_hash=digest(token),user_id=1,expires=time.time()+100));db.commit()
    body={'token':token,'password':'new-secure-test-password'}
    assert c.post('/auth/reset-password',json=body).status_code==200
    assert c.get('/users/me').status_code==401
    assert c.post('/auth/reset-password',json=body).status_code==400
def test_deactivation_revokes():
    e=client();a=client('admin@flowops.local')
    assert a.put('/admin/users/1',json={'active':False}).status_code==200
    assert e.get('/users/me').status_code==401
