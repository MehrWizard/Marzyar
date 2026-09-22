"""
Tests for Marzyar quota enforcement:
  - check_admin_can_create_user
  - check_admin_can_modify_user
  - audit_admin_quotas (lock/unlock lifecycle)
"""
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.models.user import UserStatus
from app.marzyar import crud
from app.marzyar.models import MarzyarAdminSettings, MarzyarUserLock
from app.marzyar.quota import (
    check_admin_can_create_user,
    check_admin_can_modify_user,
    audit_admin_quotas,
)


# ======================================================================
# check_admin_can_create_user
# ======================================================================
class TestCheckAdminCanCreateUser:

    def test_sudo_admin_always_passes(self, db, make_admin, make_settings):
        admin = make_admin(is_sudo=True)
        make_settings(admin, users_limit=0, traffic_limit=0)
        # Should not raise even with zero limits
        check_admin_can_create_user(db, admin, data_limit=999, inbounds=None)

    def test_no_settings_always_passes(self, db, make_admin):
        admin = make_admin()
        # No MarzyarAdminSettings row → unrestricted
        check_admin_can_create_user(db, admin, data_limit=1000, inbounds=None)

    def test_user_limit_allows_below(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, users_limit=2)
        make_user(admin)
        # 1 user, limit 2 → OK
        check_admin_can_create_user(db, admin, data_limit=1000, inbounds=None)

    def test_user_limit_blocks_at_limit(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, users_limit=1)
        make_user(admin)
        # 1 user, limit 1 → blocked
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=1000, inbounds=None)
        assert exc.value.status_code == 403
        assert "user limit" in exc.value.detail.lower()

    def test_traffic_consumed_blocks_when_exceeded(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=1000, oversell_allowed=True)
        make_user(admin, used_traffic=1000)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=500, inbounds=None)
        assert exc.value.status_code == 403
        assert "consumed" in exc.value.detail.lower() or "quota" in exc.value.detail.lower()

    def test_traffic_consumed_allows_below(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=True)
        make_user(admin, used_traffic=500)
        check_admin_can_create_user(db, admin, data_limit=5000, inbounds=None)

    def test_strict_mode_blocks_unlimited_data_limit(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=False)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=None, inbounds=None)
        assert exc.value.status_code == 400
        assert "unlimited" in exc.value.detail.lower()

    def test_strict_mode_blocks_zero_data_limit(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=False)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=0, inbounds=None)
        assert exc.value.status_code == 400

    def test_strict_mode_blocks_over_allocated(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=5000, oversell_allowed=False)
        make_user(admin, data_limit=3000, status=UserStatus.active)
        # Trying to create user with 3000 → total = 6000 > 5000
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=3000, inbounds=None)
        assert exc.value.status_code == 403
        assert "allocated" in exc.value.detail.lower()

    def test_strict_mode_allows_within_allocated(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=5000, oversell_allowed=False)
        make_user(admin, data_limit=2000, status=UserStatus.active)
        # 2000 + 2000 = 4000 <= 5000 → OK
        check_admin_can_create_user(db, admin, data_limit=2000, inbounds=None)

    def test_oversell_mode_allows_over_allocated(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=5000, oversell_allowed=True)
        make_user(admin, data_limit=3000, status=UserStatus.active)
        # Oversell: only consumed matters, not allocated → OK
        check_admin_can_create_user(db, admin, data_limit=3000, inbounds=None)

    def test_inbound_restriction_blocks_disallowed(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin, allowed_inbounds=["VLESS_TCP", "VMESS_WS"])
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, admin, data_limit=1000, inbounds={"vless": ["TROJAN_GRPC"]})
        assert exc.value.status_code == 403
        assert "not permitted" in exc.value.detail.lower()

    def test_inbound_restriction_allows_permitted(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin, allowed_inbounds=["VLESS_TCP", "VMESS_WS"])
        check_admin_can_create_user(db, admin, data_limit=1000, inbounds={"vless": ["VLESS_TCP"]})


# ======================================================================
# check_admin_can_modify_user
# ======================================================================
class TestCheckAdminCanModifyUser:

    def test_sudo_always_passes(self, db, make_admin, make_user, make_settings):
        admin = make_admin(is_sudo=True)
        make_settings(admin, traffic_limit=0)
        u = make_user(admin)
        check_admin_can_modify_user(db, admin, u, new_data_limit=999999, new_inbounds=None, new_status=None)

    def test_locked_user_cannot_be_activated(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000)
        u = make_user(admin, status=UserStatus.disabled)
        make_lock(u, admin)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_modify_user(db, admin, u, new_data_limit=None, new_inbounds=None,
                                        new_status=UserStatus.active)
        assert exc.value.status_code == 403
        assert "locked" in exc.value.detail.lower()

    def test_locked_user_can_be_modified_without_activating(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000)
        u = make_user(admin, status=UserStatus.disabled, data_limit=1000)
        make_lock(u, admin)
        # Changing data_limit without activating → OK
        check_admin_can_modify_user(db, admin, u, new_data_limit=2000, new_inbounds=None, new_status=None)

    def test_consumed_blocks_activation(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=1000, oversell_allowed=True)
        make_user(admin, used_traffic=1000, status=UserStatus.active)  # fills quota
        u2 = make_user(admin, status=UserStatus.disabled, used_traffic=0, data_limit=100)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_modify_user(db, admin, u2, new_data_limit=100, new_inbounds=None,
                                        new_status=UserStatus.active)
        assert exc.value.status_code == 403

    def test_strict_mode_blocks_unlimited_data(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=False)
        u = make_user(admin, data_limit=1000, status=UserStatus.active)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_modify_user(db, admin, u, new_data_limit=0, new_inbounds=None, new_status=None)
        assert exc.value.status_code == 400

    def test_strict_mode_blocks_over_allocated_increase(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=5000, oversell_allowed=False)
        u1 = make_user(admin, data_limit=3000, status=UserStatus.active)
        u2 = make_user(admin, data_limit=1500, status=UserStatus.active)
        # Try to raise u2 from 1500 to 3000 → total = 3000 + 3000 = 6000 > 5000
        with pytest.raises(HTTPException) as exc:
            check_admin_can_modify_user(db, admin, u2, new_data_limit=3000, new_inbounds=None, new_status=None)
        assert exc.value.status_code == 403

    def test_inbound_blocks_on_modify(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, allowed_inbounds=["VLESS_TCP"])
        u = make_user(admin, data_limit=1000, status=UserStatus.active)
        with pytest.raises(HTTPException) as exc:
            check_admin_can_modify_user(db, admin, u, new_data_limit=None,
                                        new_inbounds={"vless": ["TROJAN_GRPC"]}, new_status=None)
        assert exc.value.status_code == 403


# ======================================================================
# audit_admin_quotas (integration: lock/unlock lifecycle)
# ======================================================================
class TestAuditAdminQuotas:

    @patch("app.marzyar.quota.xray")
    def test_locks_users_when_over_quota(self, mock_xray, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=1000, oversell_allowed=True)
        u = make_user(admin, used_traffic=2000, status=UserStatus.active)
        audit_admin_quotas(db)
        db.refresh(u)
        assert u.status == UserStatus.disabled
        lock = db.query(MarzyarUserLock).filter_by(user_id=u.id).first()
        assert lock is not None
        assert lock.original_status == "active"

    @patch("app.marzyar.quota.xray")
    def test_unlocks_users_when_under_quota(self, mock_xray, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=True, quota_used_traffic=0)
        u = make_user(admin, used_traffic=100, status=UserStatus.disabled)
        make_lock(u, admin, original_status="active")
        audit_admin_quotas(db)
        db.refresh(u)
        assert u.status == UserStatus.active
        assert db.query(MarzyarUserLock).filter_by(user_id=u.id).first() is None

    @patch("app.marzyar.quota.xray")
    def test_unlock_preserves_expired_status(self, mock_xray, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=100000, oversell_allowed=True)
        u = make_user(admin, used_traffic=0, status=UserStatus.disabled, expire=1)
        make_lock(u, admin, original_status="active")
        audit_admin_quotas(db)
        db.refresh(u)
        # User's expire=1 (past timestamp) → should be expired, not active
        assert u.status == UserStatus.expired

    @patch("app.marzyar.quota.xray")
    def test_unlock_preserves_limited_status(self, mock_xray, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=100000, oversell_allowed=True)
        u = make_user(admin, used_traffic=5000, data_limit=1000, status=UserStatus.disabled)
        make_lock(u, admin, original_status="active")
        audit_admin_quotas(db)
        db.refresh(u)
        # used_traffic(5000) >= data_limit(1000) → should be limited, not active
        assert u.status == UserStatus.limited

    @patch("app.marzyar.quota.xray")
    def test_sudo_admin_is_skipped(self, mock_xray, db, make_admin, make_user, make_settings):
        admin = make_admin(is_sudo=True)
        make_settings(admin, traffic_limit=1, oversell_allowed=True)
        u = make_user(admin, used_traffic=99999, status=UserStatus.active)
        audit_admin_quotas(db)
        db.refresh(u)
        assert u.status == UserStatus.active  # Not locked

    @patch("app.marzyar.quota.xray")
    def test_no_settings_admin_skipped(self, mock_xray, db, make_admin, make_user):
        admin = make_admin()
        # No settings → no limits → user stays active
        u = make_user(admin, used_traffic=99999, status=UserStatus.active)
        audit_admin_quotas(db)
        db.refresh(u)
        assert u.status == UserStatus.active

    @patch("app.marzyar.quota.xray")
    def test_strict_mode_locks_on_allocated_exceeded(self, mock_xray, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin, traffic_limit=5000, oversell_allowed=False, quota_used_traffic=0)
        # Two active users allocating 3000 each = 6000 > 5000
        u1 = make_user(admin, data_limit=3000, used_traffic=0, status=UserStatus.active)
        u2 = make_user(admin, data_limit=3000, used_traffic=0, status=UserStatus.active)
        audit_admin_quotas(db)
        # At least one user should be locked
        locks = db.query(MarzyarUserLock).filter_by(admin_id=admin.id).all()
        assert len(locks) > 0

    @patch("app.marzyar.quota.xray")
    def test_user_limit_not_enforced_by_audit(self, mock_xray, db, make_admin, make_user, make_settings):
        """audit_admin_quotas only checks traffic_limit, not users_limit.
        Users_limit is enforced at creation time only (check_admin_can_create_user)."""
        admin = make_admin()
        make_settings(admin, users_limit=1)
        u1 = make_user(admin, status=UserStatus.active)
        u2 = make_user(admin, status=UserStatus.active)
        audit_admin_quotas(db)
        # No locks created — audit doesn't enforce user count
        locks = db.query(MarzyarUserLock).filter_by(admin_id=admin.id).all()
        assert len(locks) == 0
        db.refresh(u1)
        db.refresh(u2)
        assert u1.status == UserStatus.active
        assert u2.status == UserStatus.active

    def test_pydantic_admin_model_with_and_without_id(self, db, make_admin, make_settings, make_user):
        """Verify check_admin_can_create_user and modify_user work seamlessly with Pydantic Admin models."""
        from app.models.admin import Admin as PydanticAdmin
        orm_admin = make_admin()
        make_settings(orm_admin, users_limit=5, traffic_limit=10000, oversell_allowed=True)

        # 1. Pydantic Admin with explicit id
        p_admin_with_id = PydanticAdmin(id=orm_admin.id, username=orm_admin.username, is_sudo=False)
        check_admin_can_create_user(db, p_admin_with_id, data_limit=1000, inbounds=None)

        # 2. Pydantic Admin with id=None (fallback via username lookup)
        p_admin_no_id = PydanticAdmin(id=None, username=orm_admin.username, is_sudo=False)
        check_admin_can_create_user(db, p_admin_no_id, data_limit=1000, inbounds=None)

        # 3. Modify user with Pydantic Admin
        u = make_user(orm_admin, status=UserStatus.active)
        check_admin_can_modify_user(
            db, p_admin_with_id, target_user=u, new_data_limit=2000, new_inbounds=None, new_status=UserStatus.active
        )
        check_admin_can_modify_user(
            db, p_admin_no_id, target_user=u, new_data_limit=2000, new_inbounds=None, new_status=UserStatus.active
        )

    def test_strict_mode_allocation_cap_error_detail(self, db, make_admin, make_settings, make_user):
        """Verify strict mode error details and my_limits response."""
        from app.marzyar.router import get_my_limits
        from app.models.admin import Admin as PydanticAdmin

        admin = make_admin()
        make_settings(admin, traffic_limit=10000, oversell_allowed=False)
        make_user(admin, data_limit=8000, status=UserStatus.active)

        p_admin = PydanticAdmin(id=admin.id, username=admin.username, is_sudo=False)

        # 1. Check get_my_limits: allocated is 8000/10000 -> is_allocation_limit_reached is False
        limits = get_my_limits(db=db, current_admin=p_admin)
        assert limits.is_allocation_limit_reached is False
        assert limits.is_quota_exceeded is False

        # 2. Add user to reach exact 10000 limit
        make_user(admin, data_limit=2000, status=UserStatus.active)
        limits2 = get_my_limits(db=db, current_admin=p_admin)
        assert limits2.is_allocation_limit_reached is True
        assert limits2.is_quota_exceeded is False  # exactly at limit, not exceeded

        # 3. Trying to create another user throws 403 with allocated detail
        with pytest.raises(HTTPException) as exc:
            check_admin_can_create_user(db, p_admin, data_limit=1000, inbounds=None)
        assert exc.value.status_code == 403
        assert "allocated" in exc.value.detail.lower()
        assert "exceed your limit" in exc.value.detail.lower()
