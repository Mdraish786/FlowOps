from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, Text, Float, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def now(): return datetime.now(timezone.utc).isoformat()
class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30))
    department: Mapped[str] = mapped_column(String(100))
    manager_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_secret: Mapped[str|None] = mapped_column(Text, nullable=True)
    mfa_last_counter: Mapped[int] = mapped_column(Integer, default=0)
class LoginSession(Base):
    __tablename__='refresh_tokens'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires: Mapped[float] = mapped_column(Float)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    __mapper_args__={'version_id_col': version}
class Workflow(Base):
    __tablename__='workflow_rules'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(40), index=True)
    min_amount: Mapped[float] = mapped_column(Numeric(14,2), default=0)
    max_amount: Mapped[float|None] = mapped_column(Numeric(14,2), nullable=True)
    roles: Mapped[list] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class ApprovalRequest(Base):
    __tablename__='requests'
    __table_args__=(CheckConstraint('amount >= 0', name='nonnegative_amount'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    manager_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40))
    amount: Mapped[float] = mapped_column(Numeric(14,2))
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(15))
    status: Mapped[str] = mapped_column(String(30), default='Pending', index=True)
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    workflow_id: Mapped[int] = mapped_column(ForeignKey('workflow_rules.id'))
    steps: Mapped[list] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__={'version_id_col': version}
class Comment(Base):
    __tablename__='comments'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    text: Mapped[str] = mapped_column(Text)
    at: Mapped[str] = mapped_column(String(40), default=now)
class Attachment(Base):
    __tablename__='attachments'
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    stored_name: Mapped[str] = mapped_column(String(80))
    mime: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
class AuditLog(Base):
    __tablename__='audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int|None] = mapped_column(ForeignKey('users.id'), nullable=True)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    target: Mapped[str] = mapped_column(String(200))
    request_id: Mapped[int|None] = mapped_column(ForeignKey('requests.id'), nullable=True, index=True)
    at: Mapped[str] = mapped_column(String(40), default=now)
class Notification(Base):
    __tablename__='notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey('requests.id'))
    message: Mapped[str] = mapped_column(String(300))
    at: Mapped[str] = mapped_column(String(40), default=now)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    # Transactional outbox: workers only process committed notifications.
    emailed: Mapped[bool] = mapped_column(Boolean, default=False)
class ResetToken(Base):
    __tablename__='password_reset_tokens'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    expires: Mapped[float] = mapped_column(Float)
