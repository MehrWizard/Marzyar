from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Admin as AdminModel
from app.models.admin import Admin
from app.marzyar import crud, quota
from app.marzyar.schemas import (
    MarzyarAdminSettingsModify,
    MarzyarAdminSettingsResponse,
    MarzyarLockedUserResponse,
    MarzyarMyLimitsResponse,
)

router = APIRouter(prefix="/marzyar", tags=["Marzyar"])


def _build_admin_settings_response(db: Session, admin: AdminModel) -> MarzyarAdminSettingsResponse:
    s = crud.get_or_create_admin_settings(db, admin.id)
    u_count = crud.get_admin_user_count(db, admin.id)
    allocated = crud.get_admin_allocated_traffic(db, admin.id)
    consumed = crud.get_admin_total_consumed_traffic(db, admin.id, s)
    locked_count = len(crud.get_locked_user_ids_for_admin(db, admin.id))

    is_user_limit_exceeded = bool(s.users_limit is not None and u_count >= s.users_limit)

    is_quota_exceeded = False
    if s.traffic_limit is not None:
        if s.oversell_allowed:
            is_quota_exceeded = consumed >= s.traffic_limit
        else:
            is_quota_exceeded = allocated > s.traffic_limit

    return MarzyarAdminSettingsResponse(
        admin_id=admin.id,
        username=admin.username,
        is_sudo=admin.is_sudo,
        users_limit=s.users_limit,
        traffic_limit=s.traffic_limit,
        oversell_allowed=s.oversell_allowed,
        allowed_inbounds=s.allowed_inbounds,
        quota_used_traffic=s.quota_used_traffic or 0,
        current_users_count=u_count,
        current_allocated_traffic=allocated,
        current_consumed_traffic=consumed,
        is_quota_exceeded=is_quota_exceeded,
        is_user_limit_exceeded=is_user_limit_exceeded,
        locked_users_count=locked_count,
    )


def _get_admin(db: Session, identifier: str) -> AdminModel:
    admin = None
    if identifier.isdigit():
        admin = db.query(AdminModel).filter(AdminModel.id == int(identifier)).first()
    if not admin:
        admin = db.query(AdminModel).filter(AdminModel.username == identifier).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin


@router.get("/admins", response_model=List[MarzyarAdminSettingsResponse])
def get_all_admin_settings(
    db: Session = Depends(get_db),
    sudo_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Retrieve Marzyar settings, limits, and real-time quotas for all admins (Sudo only)."""
    admins = db.query(AdminModel).all()
    return [_build_admin_settings_response(db, a) for a in admins]


@router.get("/admin/{admin_identifier}/settings", response_model=MarzyarAdminSettingsResponse)
def get_admin_settings(
    admin_identifier: str,
    db: Session = Depends(get_db),
    sudo_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Retrieve Marzyar settings for a specific admin by id or username (Sudo only)."""
    admin = _get_admin(db, admin_identifier)
    return _build_admin_settings_response(db, admin)


@router.put("/admin/{admin_identifier}/settings", response_model=MarzyarAdminSettingsResponse)
def update_admin_settings(
    admin_identifier: str,
    modify: MarzyarAdminSettingsModify,
    db: Session = Depends(get_db),
    sudo_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Update Marzyar limits, quota, oversell flag, and allowed inbounds for an admin (Sudo only)."""
    admin = _get_admin(db, admin_identifier)
    crud.update_admin_settings(db, admin.id, modify)
    # Immediately re-audit quotas to lock or unlock users based on the new settings
    quota.audit_admin_quotas(db)

    return _build_admin_settings_response(db, admin)


@router.post("/admin/{admin_identifier}/reset_quota", response_model=MarzyarAdminSettingsResponse)
def reset_admin_quota(
    admin_identifier: str,
    db: Session = Depends(get_db),
    sudo_admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Reset an admin's cumulative consumed quota counter and unlock their users (Sudo only)."""
    admin = _get_admin(db, admin_identifier)
    crud.reset_admin_quota_counter(db, admin.id)
    # Re-audit quotas immediately to lift locks
    quota.audit_admin_quotas(db)

    return _build_admin_settings_response(db, admin)


@router.get("/my_limits", response_model=MarzyarMyLimitsResponse)
def get_my_limits(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(Admin.get_current),
):
    """Retrieve the current admin's own limits, remaining quota, and allowed inbounds."""
    s = crud.get_or_create_admin_settings(db, current_admin.id)
    u_count = crud.get_admin_user_count(db, current_admin.id)
    allocated = crud.get_admin_allocated_traffic(db, current_admin.id)
    consumed = crud.get_admin_total_consumed_traffic(db, current_admin.id, s)
    locked_count = len(crud.get_locked_user_ids_for_admin(db, current_admin.id))

    is_user_limit_exceeded = bool(s.users_limit is not None and u_count >= s.users_limit)
    is_quota_exceeded = False
    if s.traffic_limit is not None:
        if s.oversell_allowed:
            is_quota_exceeded = consumed >= s.traffic_limit
        else:
            is_quota_exceeded = allocated > s.traffic_limit

    return MarzyarMyLimitsResponse(
        username=current_admin.username,
        is_sudo=current_admin.is_sudo,
        users_limit=s.users_limit,
        traffic_limit=s.traffic_limit,
        oversell_allowed=s.oversell_allowed,
        allowed_inbounds=s.allowed_inbounds,
        current_users_count=u_count,
        current_allocated_traffic=allocated,
        current_consumed_traffic=consumed,
        is_quota_exceeded=is_quota_exceeded,
        is_user_limit_exceeded=is_user_limit_exceeded,
        locked_users_count=locked_count,
    )


@router.get("/locked_users", response_model=List[MarzyarLockedUserResponse])
def get_locked_users_list(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(Admin.get_current),
):
    """List currently locked users with reasons."""
    records = crud.get_locked_users(db)
    if not current_admin.is_sudo:
        records = [r for r in records if r[2].id == current_admin.id]

    return [
        MarzyarLockedUserResponse(
            user_id=lock.user_id,
            username=user.username,
            admin_username=admin.username,
            locked_at=lock.locked_at,
            lock_reason=lock.lock_reason,
        )
        for lock, user, admin in records
    ]
