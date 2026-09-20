import threading
from typing import Dict, List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import logger, xray
from app.db.models import Admin, User
from app.models.user import UserStatus
from app.marzyar import crud
from app.marzyar.models import MarzyarAdminSettings

_audit_lock = threading.Lock()


def check_admin_can_create_user(
    db: Session,
    admin: Admin,
    data_limit: Optional[int],
    inbounds: Optional[Dict[str, List[str]]]
) -> None:
    """
    Validate whether an admin is allowed to create a user based on Marzyar limits.
    Sudo admins are exempted.
    """
    if admin.is_sudo:
        return

    # Lock admin settings row to prevent concurrent race conditions on user creation (TOCTOU)
    try:
        settings = (
            db.query(MarzyarAdminSettings)
            .filter(MarzyarAdminSettings.admin_id == admin.id)
            .with_for_update()
            .first()
        )
    except Exception:
        settings = crud.get_admin_settings(db, admin.id)

    if not settings:
        return

    # 1. Check user count limit
    if settings.users_limit is not None:
        current_count = crud.get_admin_user_count(db, admin.id)
        if current_count >= settings.users_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Admin user limit reached ({current_count}/{settings.users_limit}). Cannot create more users."
            )

    # 2. Check allowed inbounds (empty or None means all permitted)
    if settings.allowed_inbounds and inbounds:
        allowed_set = set(settings.allowed_inbounds)
        for proto, tags in inbounds.items():
            for tag in tags:
                if tag not in allowed_set:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Inbound '{tag}' is not permitted for your admin account."
                    )

    # 3. Check traffic quota
    if settings.traffic_limit is not None:
        if not settings.oversell_allowed:
            # Oversell Disabled: total allocated limits cannot exceed traffic_limit
            if data_limit is None or data_limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot create user with unlimited data when overselling is disabled for your account. Please specify a data limit."
                )
            allocated = crud.get_admin_allocated_traffic(db, admin.id)
            if allocated + data_limit > settings.traffic_limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Admin traffic quota exceeded. New allocated total ({allocated + data_limit} bytes) would exceed your limit ({settings.traffic_limit} bytes)."
                )
        else:
            # Oversell Enabled: check total consumed traffic
            consumed = crud.get_admin_total_consumed_traffic(db, admin.id, settings)
            if consumed >= settings.traffic_limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Admin traffic quota exceeded ({consumed}/{settings.traffic_limit} bytes consumed). Cannot create new users until quota is renewed."
                )


def check_admin_can_modify_user(
    db: Session,
    admin: Admin,
    target_user: User,
    new_data_limit: Optional[int],
    new_inbounds: Optional[Dict[str, List[str]]],
    new_status: Optional[UserStatus]
) -> None:
    """
    Validate modifications to existing users under Marzyar constraints.
    """
    if admin.is_sudo:
        return

    # 1. Prevent activating or putting on-hold a locked user if the admin is still locked
    if crud.is_user_locked(db, target_user.id):
        if new_status in [UserStatus.active, UserStatus.on_hold]:
            raise HTTPException(
                status_code=403,
                detail="User is currently locked due to admin quota limits and cannot be activated. Increase or reset admin quota first."
            )

    # Lock admin settings row to prevent concurrent race conditions on user modification
    try:
        settings = (
            db.query(MarzyarAdminSettings)
            .filter(MarzyarAdminSettings.admin_id == admin.id)
            .with_for_update()
            .first()
        )
    except Exception:
        settings = crud.get_admin_settings(db, admin.id)

    if not settings:
        return

    # 2. Check allowed inbounds (empty or None means all permitted)
    if settings.allowed_inbounds and new_inbounds:
        allowed_set = set(settings.allowed_inbounds)
        for proto, tags in new_inbounds.items():
            for tag in tags:
                if tag not in allowed_set:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Inbound '{tag}' is not permitted for your admin account."
                    )

    # 3. Check traffic quota
    if settings.traffic_limit is not None:
        old_limit = target_user.data_limit or 0
        delta = (new_data_limit - old_limit) if new_data_limit is not None else 0

        is_activating = (
            target_user.status not in [UserStatus.active, UserStatus.on_hold]
            and new_status in [UserStatus.active, UserStatus.on_hold]
        )

        if not settings.oversell_allowed:
            if new_data_limit is not None and new_data_limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot set unlimited data when overselling is disabled for your account. Please specify a data limit."
                )

            if delta > 0:
                allocated = crud.get_admin_allocated_traffic(db, admin.id)
                if allocated + delta > settings.traffic_limit:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Admin traffic quota exceeded. New allocated total ({allocated + delta} bytes) exceeds limit ({settings.traffic_limit} bytes)."
                    )

            if is_activating:
                allocated = crud.get_admin_allocated_traffic(db, admin.id)
                if allocated + delta > settings.traffic_limit:
                    raise HTTPException(
                        status_code=403,
                        detail="Admin allocated traffic quota is currently exceeded. Cannot activate users until quota is renewed or allocated limits reduced."
                    )
        elif settings.oversell_allowed and is_activating:
            consumed = crud.get_admin_total_consumed_traffic(db, admin.id, settings)
            if consumed >= settings.traffic_limit:
                raise HTTPException(
                    status_code=403,
                    detail="Admin quota is currently exhausted. Cannot activate users until quota is renewed."
                )


def audit_admin_quotas(db: Session) -> None:
    """
    Audit all reseller admins against their quota limits.
    - If an admin is over quota: lock their active users and remove them from Xray inbounds.
    - If an admin is back under quota: unlock their users and restore them to Xray inbounds.
    Original user.status remains intact in the database for 100% rollback compatibility.
    Thread-safe against concurrent invocations.
    """
    with _audit_lock:
        all_settings = db.query(MarzyarAdminSettings).all()

        for s in all_settings:
            try:
                if s.traffic_limit is None:
                    # Unlimited quota: unlock any previously locked users if they exist
                    locked_ids = crud.get_locked_user_ids_for_admin(db, s.admin_id)
                    if locked_ids:
                        _unlock_and_restore_users(db, list(locked_ids))
                    continue

                # Evaluate quota condition
                if s.oversell_allowed:
                    consumed = crud.get_admin_total_consumed_traffic(db, s.admin_id, s)
                    is_exceeded = consumed >= s.traffic_limit
                else:
                    allocated = crud.get_admin_allocated_traffic(db, s.admin_id)
                    is_exceeded = allocated > s.traffic_limit

                currently_locked = crud.get_locked_user_ids_for_admin(db, s.admin_id)

                if is_exceeded:
                    query = db.query(User).filter(
                        User.admin_id == s.admin_id,
                        User.status.in_([UserStatus.active, UserStatus.on_hold, UserStatus.limited]),
                    )
                    if currently_locked:
                        query = query.filter(~User.id.in_(currently_locked))
                    active_users = query.all()

                    if active_users:
                        to_lock = [(u.id, u.status.value) for u in active_users]
                        new_locked = crud.lock_users(db, to_lock, s.admin_id, reason="admin_quota_exceeded")
                        if new_locked:
                            for u in active_users:
                                try:
                                    xray.operations.remove_user(u)
                                except Exception as e:
                                    logger.warning(f"[Marzyar] Error removing locked user {u.username} from Xray: {e}")
                            logger.warning(
                                f"[Marzyar] Admin ID {s.admin_id} exceeded quota ({s.traffic_limit} bytes). "
                                f"Locked {len(new_locked)} user(s) (set status to disabled and recorded original status)."
                            )
                else:
                    # Under quota: unlock users if currently locked
                    if currently_locked:
                        _unlock_and_restore_users(db, list(currently_locked))
            except Exception as e:
                logger.error(f"[Marzyar] Error during quota audit for admin ID {s.admin_id}: {e}")


def _unlock_and_restore_users(db: Session, user_ids: List[int]) -> None:
    """Helper to unlock users, restore their original status, and re-attach active/on-hold ones to Xray."""
    restored = crud.unlock_users(db, user_ids)
    for u, orig_status in restored:
        if u.status in [UserStatus.active, UserStatus.on_hold]:
            try:
                xray.operations.add_user(u)
            except Exception as e:
                logger.warning(f"[Marzyar] Error restoring unlocked user {u.username} to Xray: {e}")
    logger.info(f"[Marzyar] Unlocked and restored {len(restored)} user(s) to original status.")
