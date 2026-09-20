from datetime import datetime
from typing import List, Optional, Set, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import logger
from app.db.base import Base, engine
from app.db.models import Admin, User
from app.marzyar.models import MarzyarAdminSettings, MarzyarUserLock
from app.marzyar.schemas import MarzyarAdminSettingsModify


def init_marzyar_db() -> None:
    """
    Safely initialize Marzyar-specific tables if they do not exist.
    Completely isolated from Alembic, ensuring zero crashes if rolling back to standard Marzban/Marzdar.
    """
    try:
        MarzyarAdminSettings.__table__.create(engine, checkfirst=True)
        MarzyarUserLock.__table__.create(engine, checkfirst=True)
        logger.info("[Marzyar] Database tables verified and initialized safely.")
    except Exception as e:
        logger.error(f"[Marzyar] Failed to initialize Marzyar database tables: {e}")


def get_admin_settings(db: Session, admin_id: int) -> Optional[MarzyarAdminSettings]:
    return db.query(MarzyarAdminSettings).filter(MarzyarAdminSettings.admin_id == admin_id).first()


def get_or_create_admin_settings(db: Session, admin_id: int) -> MarzyarAdminSettings:
    settings = get_admin_settings(db, admin_id)
    if not settings:
        settings = MarzyarAdminSettings(admin_id=admin_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_admin_settings(
    db: Session,
    admin_id: int,
    modify: MarzyarAdminSettingsModify
) -> MarzyarAdminSettings:
    settings = get_or_create_admin_settings(db, admin_id)

    if modify.users_limit is not None or "users_limit" in modify.model_fields_set:
        settings.users_limit = modify.users_limit

    if modify.traffic_limit is not None or "traffic_limit" in modify.model_fields_set:
        settings.traffic_limit = modify.traffic_limit

    if modify.oversell_allowed is not None:
        settings.oversell_allowed = modify.oversell_allowed

    if modify.allowed_inbounds is not None or "allowed_inbounds" in modify.model_fields_set:
        settings.allowed_inbounds = modify.allowed_inbounds

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings


def reset_admin_quota_counter(db: Session, admin_id: int) -> None:
    """
    Reset an admin's cumulative consumed quota counter.
    Callable only by Sudo Admin.
    """
    settings = get_or_create_admin_settings(db, admin_id)
    settings.quota_used_traffic = 0
    settings.updated_at = datetime.utcnow()
    db.commit()


def increment_admin_quota_counter(db: Session, admin_id: int, amount: int) -> None:
    """
    Increment admin's consumed traffic when a user's usage is reset so resets cannot bypass quota.
    """
    if amount <= 0:
        return
    settings = get_or_create_admin_settings(db, admin_id)
    settings.quota_used_traffic = (settings.quota_used_traffic or 0) + amount
    db.commit()


def is_user_locked(db: Session, user_id: int) -> bool:
    return db.query(MarzyarUserLock.user_id).filter(MarzyarUserLock.user_id == user_id).first() is not None


def get_locked_user_ids(db: Session) -> Set[int]:
    rows = db.query(MarzyarUserLock.user_id).all()
    return {r[0] for r in rows}


def get_locked_user_ids_for_admin(db: Session, admin_id: int) -> Set[int]:
    rows = db.query(MarzyarUserLock.user_id).filter(MarzyarUserLock.admin_id == admin_id).all()
    return {r[0] for r in rows}


def get_locked_users(db: Session) -> List[Tuple[MarzyarUserLock, User, Admin]]:
    return (
        db.query(MarzyarUserLock, User, Admin)
        .join(User, MarzyarUserLock.user_id == User.id)
        .join(Admin, MarzyarUserLock.admin_id == Admin.id)
        .all()
    )


def lock_users(
    db: Session,
    user_ids: List[int],
    admin_id: int,
    reason: str = "admin_quota_exceeded"
) -> List[int]:
    """
    Lock a list of users under an admin without touching user.status in the users table.
    """
    if not user_ids:
        return []

    existing = set(get_locked_user_ids_for_admin(db, admin_id))
    new_locked = []

    for uid in user_ids:
        if uid not in existing:
            lock_entry = MarzyarUserLock(
                user_id=uid,
                admin_id=admin_id,
                locked_at=datetime.utcnow(),
                lock_reason=reason
            )
            db.add(lock_entry)
            new_locked.append(uid)

    if new_locked:
        db.commit()
    return new_locked


def unlock_users(db: Session, user_ids: List[int]) -> List[int]:
    """
    Remove users from lock table, lifting their lock.
    """
    if not user_ids:
        return []

    deleted_count = (
        db.query(MarzyarUserLock)
        .filter(MarzyarUserLock.user_id.in_(user_ids))
        .delete(synchronize_session=False)
    )
    if deleted_count:
        db.commit()
    return user_ids


def get_admin_user_count(db: Session, admin_id: int) -> int:
    return db.query(func.count(User.id)).filter(User.admin_id == admin_id).scalar() or 0


def get_admin_allocated_traffic(db: Session, admin_id: int) -> int:
    return (
        db.query(func.coalesce(func.sum(User.data_limit), 0))
        .filter(User.admin_id == admin_id, User.data_limit > 0)
        .scalar()
        or 0
    )


def get_admin_active_users_usage(db: Session, admin_id: int) -> int:
    return (
        db.query(func.coalesce(func.sum(User.used_traffic), 0))
        .filter(User.admin_id == admin_id)
        .scalar()
        or 0
    )


def get_admin_total_consumed_traffic(
    db: Session,
    admin_id: int,
    settings: Optional[MarzyarAdminSettings] = None
) -> int:
    if settings is None:
        settings = get_admin_settings(db, admin_id)
    base_counter = settings.quota_used_traffic if settings else 0
    active_usage = get_admin_active_users_usage(db, admin_id)
    return base_counter + active_usage
