from datetime import datetime
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import logger, xray
from app.db.models import Admin, User
from app.models.user import UserStatus
from app.marzyar import crud
from app.marzyar.models import MarzyarAdminSettings, MarzyarUserLock

_audit_lock = threading.Lock()


def check_admin_can_create_user(
    db: Session,
    admin: Admin,
    data_limit: Optional[int],
    inbounds: Optional[Dict[str, List[str]]],
    next_plan: Optional[Any] = None,
) -> None:
    """
    Validate whether an admin is allowed to create a user based on Marzyar limits.
    Sudo admins are exempted.
    """
    if admin.is_sudo:
        return

    admin_id = crud.get_admin_id(db, admin)
    if not admin_id:
        return

    # Lock admin settings row to prevent concurrent race conditions on user creation (TOCTOU)
    try:
        settings = (
            db.query(MarzyarAdminSettings)
            .filter(MarzyarAdminSettings.admin_id == admin_id)
            .with_for_update()
            .first()
        )
    except Exception:
        settings = crud.get_admin_settings(db, admin_id)

    if not settings:
        return

    # 1. Check user count limit
    if settings.users_limit is not None:
        current_count = crud.get_admin_user_count(db, admin_id, for_update=True)
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
        consumed = crud.get_admin_total_consumed_traffic(db, admin_id, settings, for_update=True)
        if consumed >= settings.traffic_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Admin traffic quota exceeded ({consumed}/{settings.traffic_limit} bytes consumed). Cannot create new users until quota is renewed."
            )

        if not settings.oversell_allowed:
            # Oversell Disabled: total allocated limits cannot exceed traffic_limit
            if data_limit is None or data_limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot create user with unlimited data when overselling is disabled for your account. Please specify a data limit."
                )
            if next_plan and (getattr(next_plan, 'data_limit', None) is None or getattr(next_plan, 'data_limit', 0) <= 0):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot specify unlimited data for next plan when overselling is disabled for your account."
                )
            allocated = crud.get_admin_allocated_traffic(db, admin_id, for_update=True)
            if allocated + data_limit > settings.traffic_limit:
                raise HTTPException(
                    status_code=403,
                    detail=f"Admin traffic quota exceeded. New allocated total ({allocated + data_limit} bytes) would exceed your limit ({settings.traffic_limit} bytes)."
                )


def check_admin_can_modify_user(
    db: Session,
    admin: Admin,
    target_user: User,
    new_data_limit: Optional[int],
    new_inbounds: Optional[Dict[str, List[str]]],
    new_status: Optional[UserStatus],
    new_proxies: Optional[Dict[str, Any]] = None,
    new_expire: Optional[int] = None,
    new_next_plan: Optional[Any] = None,
) -> None:
    """
    Validate modifications to existing users under Marzyar constraints.
    """
    if admin.is_sudo:
        return

    admin_id = crud.get_admin_id(db, admin)
    if not admin_id:
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
            .filter(MarzyarAdminSettings.admin_id == admin_id)
            .with_for_update()
            .first()
        )
    except Exception:
        settings = crud.get_admin_settings(db, admin_id)

    if not settings:
        return

    # 2. Check allowed inbounds (empty or None means all permitted)
    if settings.allowed_inbounds:
        allowed_set = set(settings.allowed_inbounds)
        if new_inbounds:
            for proto, tags in new_inbounds.items():
                for tag in tags:
                    if tag not in allowed_set:
                        raise HTTPException(
                            status_code=403,
                            detail=f"Inbound '{tag}' is not permitted for your admin account."
                        )
        # Check newly added proxies if inbounds not explicitly specified for them
        if new_proxies:
            existing_proxy_types = {
                p.type.value if hasattr(p.type, 'value') else str(p.type)
                for p in target_user.proxies
            }
            for p_key in new_proxies:
                p_type = p_key.value if hasattr(p_key, 'value') else str(p_key)
                if p_type not in existing_proxy_types:
                    if not new_inbounds or (p_type not in new_inbounds and p_key not in new_inbounds):
                        for inbound in xray.config.inbounds_by_protocol.get(p_type, []):
                            tag = inbound.get("tag")
                            if tag and tag not in allowed_set:
                                raise HTTPException(
                                    status_code=403,
                                    detail=f"Inbound '{tag}' for protocol '{p_type}' is not permitted for your admin account."
                                )

    # 3. Check traffic quota
    if settings.traffic_limit is not None:
        old_limit = target_user.data_limit or 0
        delta = (new_data_limit - old_limit) if new_data_limit is not None else 0

        now_ts = time.time()
        is_activating = (
            target_user.status not in [UserStatus.active, UserStatus.on_hold]
            and (
                new_status in [UserStatus.active, UserStatus.on_hold]
                or (
                    target_user.status == UserStatus.limited
                    and new_data_limit is not None
                    and (new_data_limit == 0 or (target_user.used_traffic or 0) < new_data_limit)
                    and new_status not in [UserStatus.disabled, UserStatus.expired]
                )
                or (
                    target_user.status == UserStatus.expired
                    and new_expire is not None
                    and (new_expire == 0 or new_expire > now_ts)
                    and new_status not in [UserStatus.disabled, UserStatus.expired]
                )
            )
        )

        consumed = crud.get_admin_total_consumed_traffic(db, admin_id, settings, for_update=True)
        is_consumed_exceeded = consumed >= settings.traffic_limit

        if is_activating and is_consumed_exceeded:
            raise HTTPException(
                status_code=403,
                detail="Admin quota is currently exhausted. Cannot activate users until quota is renewed."
            )

        if not settings.oversell_allowed:
            if new_data_limit is not None and new_data_limit <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot set unlimited data when overselling is disabled for your account. Please specify a data limit."
                )

            if new_next_plan and (getattr(new_next_plan, 'data_limit', None) is None or getattr(new_next_plan, 'data_limit', 0) <= 0):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot specify unlimited data for next plan when overselling is disabled for your account."
                )

            if delta > 0:
                allocated = crud.get_admin_allocated_traffic(db, admin_id, for_update=True)
                if allocated + delta > settings.traffic_limit:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Admin traffic quota exceeded. New allocated total ({allocated + delta} bytes) exceeds limit ({settings.traffic_limit} bytes)."
                    )

            if is_activating:
                allocated = crud.get_admin_allocated_traffic(db, admin_id, for_update=True)
                if allocated + delta > settings.traffic_limit:
                    raise HTTPException(
                        status_code=403,
                        detail="Admin allocated traffic quota is currently exceeded. Cannot activate users until quota is renewed or allocated limits reduced."
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
                # Sudo admins are completely exempt from quotas and locking
                admin = db.query(Admin).filter(Admin.id == s.admin_id).first()
                if not admin or admin.is_sudo:
                    locked_ids = crud.get_locked_user_ids_for_admin(db, s.admin_id)
                    if locked_ids:
                        unlock_and_restore_users(db, list(locked_ids))
                    continue

                if s.traffic_limit is None:
                    # Unlimited quota: unlock any previously locked users if they exist
                    locked_ids = crud.get_locked_user_ids_for_admin(db, s.admin_id)
                    if locked_ids:
                        unlock_and_restore_users(db, list(locked_ids))
                    continue

                # Evaluate quota condition
                consumed = crud.get_admin_total_consumed_traffic(db, s.admin_id, s)
                is_exceeded = consumed >= s.traffic_limit
                
                if not is_exceeded and not s.oversell_allowed:
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
                        unlock_and_restore_users(db, list(currently_locked))
            except Exception as e:
                logger.error(f"[Marzyar] Error during quota audit for admin ID {s.admin_id}: {e}")

        # Clean up any orphaned locks where admin was deleted or no longer in settings
        try:
            active_settings_admin_ids = {s.admin_id for s in all_settings}
            if active_settings_admin_ids:
                orphaned_locks = (
                    db.query(MarzyarUserLock.user_id)
                    .filter(~MarzyarUserLock.admin_id.in_(active_settings_admin_ids))
                    .all()
                )
            else:
                orphaned_locks = db.query(MarzyarUserLock.user_id).all()
            if orphaned_locks:
                orphaned_ids = [r[0] for r in orphaned_locks]
                unlock_and_restore_users(db, orphaned_ids)
        except Exception as e:
            logger.error(f"[Marzyar] Error cleaning up orphaned locks: {e}")


def unlock_and_restore_users(db: Session, user_ids: List[int]) -> List[Tuple[User, str]]:
    """Helper to unlock users, restore their original status, and re-attach active/on-hold ones to Xray."""
    restored = crud.unlock_users(db, user_ids)
    for u, orig_status in restored:
        if u.status in [UserStatus.active, UserStatus.on_hold]:
            try:
                xray.operations.add_user(u)
            except Exception as e:
                logger.warning(f"[Marzyar] Error restoring unlocked user {u.username} to Xray: {e}")
    logger.info(f"[Marzyar] Unlocked and restored {len(restored)} user(s) to original status.")
    return restored


_unlock_and_restore_users = unlock_and_restore_users
