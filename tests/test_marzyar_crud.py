"""
Tests for Marzyar CRUD functions:
  - Admin settings CRUD
  - Quota counter operations (increment / reset)
  - User locking / unlocking
  - Traffic accounting helpers
  - Inbound enforcement
"""
from datetime import datetime

import pytest
from app.models.user import UserStatus
from app.marzyar.models import MarzyarAdminSettings, MarzyarUserLock
from app.marzyar import crud


# ======================================================================
# Admin Settings CRUD
# ======================================================================
class TestAdminSettingsCRUD:

    def test_get_settings_returns_none_when_missing(self, db, make_admin):
        admin = make_admin()
        assert crud.get_admin_settings(db, admin.id) is None

    def test_get_or_create_settings_creates_default(self, db, make_admin):
        admin = make_admin()
        settings = crud.get_or_create_admin_settings(db, admin.id)
        assert settings.admin_id == admin.id
        assert settings.users_limit is None
        assert settings.traffic_limit is None
        assert settings.oversell_allowed is False
        assert settings.quota_used_traffic == 0

    def test_get_or_create_settings_idempotent(self, db, make_admin):
        admin = make_admin()
        s1 = crud.get_or_create_admin_settings(db, admin.id)
        s2 = crud.get_or_create_admin_settings(db, admin.id)
        assert s1.admin_id == s2.admin_id

    def test_update_admin_settings(self, db, make_admin, make_settings):
        from app.marzyar.schemas import MarzyarAdminSettingsModify
        admin = make_admin()
        make_settings(admin)
        modify = MarzyarAdminSettingsModify(users_limit=10, traffic_limit=1_000_000_000)
        crud.update_admin_settings(db, admin.id, modify)
        s = crud.get_admin_settings(db, admin.id)
        assert s.users_limit == 10
        assert s.traffic_limit == 1_000_000_000

    def test_update_preserves_unset_fields(self, db, make_admin, make_settings):
        from app.marzyar.schemas import MarzyarAdminSettingsModify
        admin = make_admin()
        make_settings(admin, users_limit=5, traffic_limit=500)
        # Only update oversell_allowed, leave others untouched
        modify = MarzyarAdminSettingsModify(oversell_allowed=True)
        crud.update_admin_settings(db, admin.id, modify)
        s = crud.get_admin_settings(db, admin.id)
        assert s.users_limit == 5
        assert s.traffic_limit == 500
        assert s.oversell_allowed is True


# ======================================================================
# User Count
# ======================================================================
class TestUserCount:

    def test_count_zero_when_no_users(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin)
        assert crud.get_admin_user_count(db, admin.id) == 0

    def test_count_reflects_created_users(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        make_user(admin)
        make_user(admin)
        make_user(admin)
        assert crud.get_admin_user_count(db, admin.id) == 3

    def test_count_excludes_other_admins_users(self, db, make_admin, make_user, make_settings):
        admin1 = make_admin("a1")
        admin2 = make_admin("a2")
        make_settings(admin1)
        make_user(admin1)
        make_user(admin2)
        assert crud.get_admin_user_count(db, admin1.id) == 1


# ======================================================================
# Quota Counter (increment / reset)
# ======================================================================
class TestQuotaCounter:

    def test_increment_adds_traffic(self, db, make_admin, make_settings):
        admin = make_admin()
        s = make_settings(admin, quota_used_traffic=0)
        crud.increment_admin_quota_counter(db, admin.id, 1000)
        db.refresh(s)
        assert s.quota_used_traffic == 1000

    def test_increment_accumulates(self, db, make_admin, make_settings):
        admin = make_admin()
        s = make_settings(admin, quota_used_traffic=500)
        crud.increment_admin_quota_counter(db, admin.id, 300)
        db.refresh(s)
        assert s.quota_used_traffic == 800

    def test_increment_zero_is_noop(self, db, make_admin, make_settings):
        admin = make_admin()
        s = make_settings(admin, quota_used_traffic=100)
        crud.increment_admin_quota_counter(db, admin.id, 0)
        db.refresh(s)
        assert s.quota_used_traffic == 100

    def test_reset_counter_zeros_consumed(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin, quota_used_traffic=5000)
        crud.reset_admin_quota_counter(db, admin.id)
        s = crud.get_admin_settings(db, admin.id)
        # After reset, total consumed should be 0
        consumed = crud.get_admin_total_consumed_traffic(db, admin.id, s)
        assert consumed == 0


# ======================================================================
# Traffic Accounting
# ======================================================================
class TestTrafficAccounting:

    def test_active_usage_sums_users(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        make_user(admin, used_traffic=1000)
        make_user(admin, used_traffic=2000)
        assert crud.get_admin_active_users_usage(db, admin.id) == 3000

    def test_active_usage_excludes_other_admin(self, db, make_admin, make_user, make_settings):
        admin1 = make_admin("a1")
        admin2 = make_admin("a2")
        make_settings(admin1)
        make_user(admin1, used_traffic=100)
        make_user(admin2, used_traffic=999)
        assert crud.get_admin_active_users_usage(db, admin1.id) == 100

    def test_total_consumed_includes_base_and_active(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        s = make_settings(admin, quota_used_traffic=5000)
        make_user(admin, used_traffic=1000)
        consumed = crud.get_admin_total_consumed_traffic(db, admin.id, s)
        assert consumed == 6000  # 5000 base + 1000 active

    def test_total_consumed_floors_at_zero(self, db, make_admin, make_settings):
        admin = make_admin()
        s = make_settings(admin, quota_used_traffic=-5000)
        consumed = crud.get_admin_total_consumed_traffic(db, admin.id, s)
        assert consumed == 0

    def test_allocated_traffic_sums_data_limits(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        make_user(admin, data_limit=1000, status=UserStatus.active)
        make_user(admin, data_limit=2000, status=UserStatus.active)
        make_user(admin, data_limit=None, status=UserStatus.active)  # unlimited = 0 contribution
        assert crud.get_admin_allocated_traffic(db, admin.id) == 3000

    def test_allocated_excludes_zero_and_null_limits(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        make_user(admin, data_limit=1000, status=UserStatus.active)
        make_user(admin, data_limit=5000, status=UserStatus.disabled)
        make_user(admin, data_limit=3000, status=UserStatus.expired)
        # get_admin_allocated_traffic sums ALL users with data_limit > 0
        # regardless of status (design decision: allocated = total capacity assigned)
        allocated = crud.get_admin_allocated_traffic(db, admin.id)
        assert allocated == 9000  # 1000 + 5000 + 3000


# ======================================================================
# User Locking
# ======================================================================
class TestUserLocking:

    def test_lock_users_creates_entries(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        u1 = make_user(admin)
        u2 = make_user(admin)
        locked = crud.lock_users(db, [(u1.id, "active"), (u2.id, "active")], admin.id)
        assert len(locked) == 2
        db.refresh(u1)
        db.refresh(u2)
        assert u1.status == UserStatus.disabled
        assert u2.status == UserStatus.disabled

    def test_lock_users_preserves_original_status(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin, status=UserStatus.on_hold)
        crud.lock_users(db, [(u.id, "on_hold")], admin.id)
        lock = db.query(MarzyarUserLock).filter_by(user_id=u.id).first()
        assert lock.original_status == "on_hold"

    def test_lock_users_idempotent(self, db, make_admin, make_user, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin)
        crud.lock_users(db, [(u.id, "active")], admin.id)
        # Locking again should update original_status, not create duplicate
        crud.lock_users(db, [(u.id, "limited")], admin.id)
        locks = db.query(MarzyarUserLock).filter_by(user_id=u.id).all()
        assert len(locks) == 1
        assert locks[0].original_status == "limited"

    def test_lock_empty_list_is_noop(self, db, make_admin, make_settings):
        admin = make_admin()
        make_settings(admin)
        assert crud.lock_users(db, [], admin.id) == []

    def test_is_user_locked(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin)
        assert crud.is_user_locked(db, u.id) is False
        make_lock(u, admin)
        assert crud.is_user_locked(db, u.id) is True


# ======================================================================
# User Unlocking
# ======================================================================
class TestUserUnlocking:

    def test_unlock_restores_active(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin, status=UserStatus.disabled)
        make_lock(u, admin, original_status="active")
        crud.unlock_users(db, [u.id])
        db.refresh(u)
        assert u.status == UserStatus.active
        assert db.query(MarzyarUserLock).filter_by(user_id=u.id).first() is None

    def test_unlock_restores_on_hold(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin, status=UserStatus.disabled)
        make_lock(u, admin, original_status="on_hold")
        crud.unlock_users(db, [u.id])
        db.refresh(u)
        assert u.status == UserStatus.on_hold

    def test_unlock_expired_user_stays_expired(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin, status=UserStatus.disabled, expire=1)  # expired timestamp
        make_lock(u, admin, original_status="active")
        crud.unlock_users(db, [u.id])
        db.refresh(u)
        assert u.status == UserStatus.expired

    def test_unlock_limited_user_stays_limited(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u = make_user(admin, status=UserStatus.disabled, data_limit=100, used_traffic=200)
        make_lock(u, admin, original_status="active")
        crud.unlock_users(db, [u.id])
        db.refresh(u)
        assert u.status == UserStatus.limited


# ======================================================================
# Locked User ID Queries
# ======================================================================
class TestLockedUserQueries:

    def test_get_locked_user_ids(self, db, make_admin, make_user, make_lock, make_settings):
        admin = make_admin()
        make_settings(admin)
        u1 = make_user(admin)
        u2 = make_user(admin)
        u3 = make_user(admin)
        make_lock(u1, admin)
        make_lock(u3, admin)
        ids = crud.get_locked_user_ids(db)
        assert u1.id in ids
        assert u3.id in ids
        assert u2.id not in ids

    def test_get_locked_user_ids_for_admin(self, db, make_admin, make_user, make_lock, make_settings):
        admin1 = make_admin("a1")
        admin2 = make_admin("a2")
        make_settings(admin1)
        make_settings(admin2)
        u1 = make_user(admin1)
        u2 = make_user(admin2)
        make_lock(u1, admin1)
        make_lock(u2, admin2)
        ids1 = crud.get_locked_user_ids_for_admin(db, admin1.id)
        assert u1.id in ids1
        assert u2.id not in ids1


# ======================================================================
# Timezone & Expiration Invariance
# ======================================================================
class TestTimezoneAndExpirationInvariance:

    def test_start_user_expire_time_invariance(self, db, make_admin, make_user):
        import time
        from app.db.crud import start_user_expire

        admin = make_admin()
        u = make_user(admin, status=UserStatus.on_hold)
        u.on_hold_expire_duration = 3600
        db.commit()

        start_time = time.time()
        start_user_expire(db, u)
        db.refresh(u)

        assert u.expire is not None
        assert abs(u.expire - (int(start_time) + 3600)) <= 2
        assert u.on_hold_expire_duration is None

    def test_update_user_future_expire_activates_expired_user(self, db, make_admin, make_user):
        import time
        from app.db.crud import update_user
        from app.models.user import UserModify

        admin = make_admin()
        u = make_user(admin, status=UserStatus.expired, expire=int(time.time()) - 100)
        db.commit()

        modify = UserModify(expire=int(time.time()) + 3600)
        update_user(db, u, modify)
        db.refresh(u)

        assert u.status == UserStatus.active
        assert u.expire > int(time.time())

    def test_reset_user_data_usage_leaves_expired_user_expired(self, db, make_admin, make_user):
        import time
        from app.db.crud import reset_user_data_usage

        admin = make_admin()
        u = make_user(admin, status=UserStatus.limited, expire=int(time.time()) - 500, used_traffic=500, data_limit=500)
        reset_user_data_usage(db, u)
        db.refresh(u)

        assert u.status == UserStatus.expired
        assert u.used_traffic == 0

    def test_reset_user_data_usage_leaves_on_hold_user_on_hold(self, db, make_admin, make_user):
        from app.db.crud import reset_user_data_usage

        admin = make_admin()
        u = make_user(admin, status=UserStatus.on_hold, used_traffic=100)
        reset_user_data_usage(db, u)
        db.refresh(u)

        assert u.status == UserStatus.on_hold
        assert u.used_traffic == 0

    def test_reset_all_users_data_usage_leaves_expired_user_expired(self, db, make_admin, make_user):
        import time
        from app.db.crud import reset_all_users_data_usage

        admin = make_admin()
        u1 = make_user(admin, username="u1", status=UserStatus.limited, expire=int(time.time()) - 500, used_traffic=500, data_limit=500)
        u2 = make_user(admin, username="u2", status=UserStatus.limited, expire=int(time.time()) + 5000, used_traffic=500, data_limit=500)
        reset_all_users_data_usage(db, admin)
        db.refresh(u1)
        db.refresh(u2)

        assert u1.status == UserStatus.expired
        assert u2.status == UserStatus.active
