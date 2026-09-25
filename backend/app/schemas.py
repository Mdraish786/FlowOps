from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
Role = Literal['Employee','Manager','IT','Finance','HR','Director','Admin']
Category = Literal['Equipment','Software','Cloud resources','Access','Reimbursement','Leave','Vendor payment','Training']
class Schema(BaseModel):
    model_config=ConfigDict(extra='forbid', str_strip_whitespace=True)
class Login(Schema):
    email: str = Field(min_length=3,max_length=200)
    password: str = Field(min_length=1,max_length=128)
    otp: str|None = None
class NewRequest(Schema):
    title: str = Field(min_length=4,max_length=160)
    category: Category
    amount: Decimal = Field(ge=0,le=100000000,decimal_places=2)
    reason: str = Field(min_length=10,max_length=5000)
    priority: Literal['Normal','High','Urgent']='Normal'
class Decision(Schema):
    comment: str=Field(default='',max_length=3000)
    version: int=Field(ge=1)
class NewComment(Schema):
    text: str=Field(min_length=1,max_length=3000)
class NewWorkflow(Schema):
    id: int|None=None
    name: str=Field(min_length=3,max_length=100)
    category: Category
    min_amount: Decimal=Field(ge=0,le=100000000,decimal_places=2)
    max_amount: Decimal|None=Field(default=None,ge=0,le=100000000,decimal_places=2)
    roles: list[Role]=Field(min_length=1,max_length=8)
    active: bool=True
    @model_validator(mode='after')
    def valid(self):
        if self.max_amount is not None and self.max_amount<self.min_amount: raise ValueError('Invalid amount range')
        if any(r in ['Admin','Employee'] for r in self.roles): raise ValueError('Only approver roles are allowed')
        if len(self.roles)!=len(set(self.roles)): raise ValueError('Duplicate approval roles are not allowed')
        return self
class NewUser(Schema):
    name: str=Field(min_length=2,max_length=100)
    email: str=Field(min_length=5,max_length=200,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str=Field(min_length=12,max_length=128)
    role: Role
    department: str=Field(min_length=2,max_length=100)
    manager_id: int|None=None
class EditUser(Schema):
    role: Role|None=None
    active: bool|None=None
    manager_id: int|None=None
class Forgot(Schema):
    email: str=Field(min_length=3,max_length=200)
class Reset(Schema):
    token: str=Field(min_length=20,max_length=200)
    password: str=Field(min_length=12,max_length=128)
