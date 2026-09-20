from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship, backref
from app.db.base import Base


class MarzyarAdminSettings(Base):
    """
    Independent settings table for Marzyar reseller admin limits, quotas, and inbound rules.
    Keeps original Marzban/Marzdar admins table 100% clean and intact.
    """
    __tablename__ = "marzyar_admin_settings"

    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), primary_key=True)
    users_limit = Column(Integer, nullable=True, default=None)  # None = unlimited
    traffic_limit = Column(BigInteger, nullable=True, default=None)  # Bytes, None = unlimited
    oversell_allowed = Column(Boolean, nullable=False, default=False)  # False = allocated limits, True = consumed usage
    allowed_inbounds = Column(JSON, nullable=True, default=None)  # List of allowed inbound tags (e.g. ["VLESS TCP..."]), None = all
    quota_used_traffic = Column(BigInteger, nullable=False, default=0)  # Consumed traffic counter, only reset by Sudo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = relationship("Admin", backref=backref("marzyar_settings", uselist=False), foreign_keys=[admin_id])


class MarzyarUserLock(Base):
    """
    Tracks locked users whose admin exceeded quota.
    Preserves original user.status in the users table so rollback to Marzban/Marzdar is 100% safe.
    """
    __tablename__ = "marzyar_user_locks"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="CASCADE"), index=True)
    locked_at = Column(DateTime, default=datetime.utcnow)
    lock_reason = Column(String(64), default="admin_quota_exceeded")
    original_status = Column(String(32), default="active", nullable=False)

    user = relationship("User", backref=backref("marzyar_lock", uselist=False), foreign_keys=[user_id])
    admin = relationship("Admin", backref="marzyar_user_locks", foreign_keys=[admin_id])
