"""
Tests for Marzyar Pydantic schemas:
  - MarzyarAdminSettingsModify validation (negative values, null handling)
  - MarzyarAdminSettingsResponse / MarzyarMyLimitsResponse serialization
"""
import pytest
from pydantic import ValidationError

from app.marzyar.schemas import (
    MarzyarAdminSettingsModify,
    MarzyarAdminSettingsResponse,
    MarzyarMyLimitsResponse,
    MarzyarLockedUserResponse,
)


class TestAdminSettingsModifyValidation:

    def test_valid_limits(self):
        m = MarzyarAdminSettingsModify(users_limit=10, traffic_limit=1_000_000_000)
        assert m.users_limit == 10
        assert m.traffic_limit == 1_000_000_000

    def test_null_limits_allowed(self):
        m = MarzyarAdminSettingsModify(users_limit=None, traffic_limit=None)
        assert m.users_limit is None
        assert m.traffic_limit is None

    def test_zero_limits_allowed(self):
        m = MarzyarAdminSettingsModify(users_limit=0, traffic_limit=0)
        assert m.users_limit == 0
        assert m.traffic_limit == 0

    def test_negative_users_limit_rejected(self):
        with pytest.raises(ValidationError) as exc:
            MarzyarAdminSettingsModify(users_limit=-1)
        assert "non-negative" in str(exc.value).lower()

    def test_negative_traffic_limit_rejected(self):
        with pytest.raises(ValidationError) as exc:
            MarzyarAdminSettingsModify(traffic_limit=-100)
        assert "non-negative" in str(exc.value).lower()

    def test_oversell_allowed_bool(self):
        m = MarzyarAdminSettingsModify(oversell_allowed=True)
        assert m.oversell_allowed is True

    def test_allowed_inbounds_list(self):
        m = MarzyarAdminSettingsModify(allowed_inbounds=["VLESS_TCP", "VMESS_WS"])
        assert m.allowed_inbounds == ["VLESS_TCP", "VMESS_WS"]

    def test_allowed_inbounds_null(self):
        m = MarzyarAdminSettingsModify(allowed_inbounds=None)
        assert m.allowed_inbounds is None

    def test_empty_body_valid(self):
        """All fields optional — empty body is valid (no changes)."""
        m = MarzyarAdminSettingsModify()
        assert m.users_limit is None
        assert m.traffic_limit is None
        assert m.oversell_allowed is None
        assert m.allowed_inbounds is None

    def test_model_fields_set_tracking(self):
        """Fields not provided should NOT be in model_fields_set."""
        m = MarzyarAdminSettingsModify(users_limit=5)
        assert "users_limit" in m.model_fields_set
        assert "traffic_limit" not in m.model_fields_set
        assert "oversell_allowed" not in m.model_fields_set


class TestAdminSettingsResponse:

    def test_defaults(self):
        r = MarzyarAdminSettingsResponse(admin_id=1, username="test", is_sudo=False)
        assert r.users_limit is None
        assert r.traffic_limit is None
        assert r.oversell_allowed is False
        assert r.is_quota_exceeded is False
        assert r.is_user_limit_exceeded is False
        assert r.locked_users_count == 0
        assert r.current_consumed_traffic == 0
        assert r.current_allocated_traffic == 0

    def test_all_fields_populated(self):
        r = MarzyarAdminSettingsResponse(
            admin_id=1,
            username="reseller",
            is_sudo=False,
            users_limit=10,
            traffic_limit=5_000_000_000,
            oversell_allowed=True,
            allowed_inbounds=["VLESS_TCP"],
            quota_used_traffic=1_000_000,
            current_users_count=5,
            current_allocated_traffic=2_000_000_000,
            current_consumed_traffic=500_000,
            is_quota_exceeded=False,
            is_user_limit_exceeded=False,
            locked_users_count=0,
        )
        assert r.current_users_count == 5
        assert r.allowed_inbounds == ["VLESS_TCP"]


class TestMyLimitsResponse:

    def test_defaults(self):
        r = MarzyarMyLimitsResponse(username="test", is_sudo=False)
        assert r.is_quota_exceeded is False
        assert r.is_user_limit_exceeded is False

    def test_exceeded_flags(self):
        r = MarzyarMyLimitsResponse(
            username="test",
            is_sudo=False,
            is_quota_exceeded=True,
            is_user_limit_exceeded=True,
        )
        assert r.is_quota_exceeded is True
        assert r.is_user_limit_exceeded is True


class TestLockedUserResponse:

    def test_serialization(self):
        from datetime import datetime
        r = MarzyarLockedUserResponse(
            user_id=42,
            username="locked_user",
            admin_username="admin1",
            locked_at=datetime(2024, 1, 1, 12, 0, 0),
            lock_reason="admin_quota_exceeded",
        )
        assert r.user_id == 42
        assert r.lock_reason == "admin_quota_exceeded"
