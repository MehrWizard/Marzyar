"""
Shared test fixtures for Marzyar tests.

Uses an in-memory SQLite database so tests are fast, isolated, and require
no external dependencies (no running Marzban/Xray instance).
"""
import logging
import os
import sys
from datetime import datetime, timezone
from enum import Enum as _Enum
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# 1. Set environment variables BEFORE importing config
# ---------------------------------------------------------------------------
os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("XRAY_SUBSCRIPTION_URL_PREFIX", "")

# ---------------------------------------------------------------------------
# 2. Stub native/heavy dependencies that can't be installed in test env
# ---------------------------------------------------------------------------

# Enum stubs for xray_api types used by Pydantic models
class _XTLSFlows(str, _Enum):
    NONE = ""
    VISION = "xtls-rprx-vision"

class _ShadowsocksMethods(str, _Enum):
    AES_128_GCM = "aes-128-gcm"
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-ietf-poly1305"

# Create a proper xray_api.types.account module with real enum classes
_xray_account = MagicMock()
_xray_account.XTLSFlows = _XTLSFlows
_xray_account.ShadowsocksMethods = _ShadowsocksMethods

for _mod_name in [
    # gRPC native binaries
    "grpc", "grpc._channel", "grpc.aio",
    # xray_api (uses grpc)
    "xray_api", "xray_api.exceptions", "xray_api.base", "xray_api.proto",
    "xray_api.proto.app", "xray_api.proto.app.proxyman",
    "xray_api.proto.app.proxyman.command",
    "xray_api.proto.app.stats", "xray_api.proto.app.stats.command",
    "xray_api.proto.common", "xray_api.proto.common.protocol",
    "xray_api.proto.common.serial", "xray_api.proto.common.net",
    "xray_api.types",
    # Telegram bot
    "telebot", "telebot.types", "telebot.custom_filters", "telebot.apihelper", "telebot.formatting",
    # APScheduler
    "apscheduler", "apscheduler.schedulers", "apscheduler.schedulers.background",
    # Other optional deps
    "commentjson", "jdatetime", "psutil",
]:
    sys.modules.setdefault(_mod_name, MagicMock())

_telebot_formatting = MagicMock()
_telebot_formatting.escape_html = lambda text: str(text) if text else ""
sys.modules["telebot.formatting"] = _telebot_formatting

# Override xray_api.types.account with our enum-bearing module
sys.modules["xray_api.types.account"] = _xray_account
sys.modules["xray_api"].exc = MagicMock()
sys.modules["xray_api"].XRay = MagicMock

# ---------------------------------------------------------------------------
# 3. Create minimal `app` package namespace WITHOUT running app/__init__.py
#    (which starts FastAPI, scheduler, imports all routers/jobs/telegram)
# ---------------------------------------------------------------------------
import types as _types

_app_mod = _types.ModuleType("app")
_app_mod.__path__ = [os.path.join(os.path.dirname(__file__), "..", "app")]
_app_mod.__package__ = "app"
_app_mod.__version__ = "0.1.26"
_app_mod.logger = logging.getLogger("test")
_app_mod.scheduler = MagicMock()

# xray stub
_xray_mod = _types.ModuleType("app.xray")
_xray_mod.__path__ = [os.path.join(_app_mod.__path__[0], "xray")]
_xray_mod.__package__ = "app.xray"
_xray_config = MagicMock()
_xray_config.inbounds_by_protocol = {}
_xray_mod.config = _xray_config
_xray_mod.api = MagicMock()
_xray_mod.nodes = {}
_app_mod.xray = _xray_mod

sys.modules["app"] = _app_mod
sys.modules["app.xray"] = _xray_mod
sys.modules["app.xray.config"] = _xray_config
_xray_operations = MagicMock()
_xray_mod.operations = _xray_operations
sys.modules["app.xray.operations"] = _xray_operations

_routers_mod = _types.ModuleType("app.routers")
_routers_mod.__path__ = [os.path.join(_app_mod.__path__[0], "routers")]
_routers_mod.__package__ = "app.routers"
_routers_mod.api_router = MagicMock()
sys.modules["app.routers"] = _routers_mod

_telegram_mod = _types.ModuleType("app.telegram")
_telegram_mod.__path__ = [os.path.join(_app_mod.__path__[0], "telegram")]
_telegram_mod.__package__ = "app.telegram"
_telegram_mod.bot = MagicMock()
sys.modules["app.telegram"] = _telegram_mod

_jobs_mod = _types.ModuleType("app.jobs")
_jobs_mod.__path__ = [os.path.join(_app_mod.__path__[0], "jobs")]
_jobs_mod.__package__ = "app.jobs"
sys.modules["app.jobs"] = _jobs_mod

# Stub heavy subpackages that app.db.crud imports transitively
for _mod_name in [
    "app.dashboard",
    "app.routers.api_router", "app.utils.report",
]:
    sys.modules.setdefault(_mod_name, MagicMock())

# ---------------------------------------------------------------------------
# 4. Now safe to import app.db and app.marzyar
# ---------------------------------------------------------------------------
from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models import Admin, User
from app.models.user import UserStatus, UserDataLimitResetStrategy
from app.marzyar.models import MarzyarAdminSettings, MarzyarUserLock


# ---------------------------------------------------------------------------
# Engine & Session fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """In-memory SQLite engine shared across the test session."""
    eng = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="function")
def db(engine):
    """Per-test database session. Rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def make_admin(db):
    """Factory to create Admin rows."""
    _counter = [0]
    def _make(username=None, is_sudo=False):
        _counter[0] += 1
        admin = Admin(
            username=username or f"admin_{_counter[0]}",
            hashed_password="fakehash",
            is_sudo=is_sudo,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(admin)
        db.flush()
        return admin
    return _make


@pytest.fixture
def make_user(db):
    """Factory to create User rows."""
    _counter = [0]
    def _make(admin, username=None, status=UserStatus.active,
              used_traffic=0, data_limit=None, expire=None):
        _counter[0] += 1
        user = User(
            username=username or f"user_{_counter[0]}",
            status=status, used_traffic=used_traffic,
            data_limit=data_limit, expire=expire,
            admin_id=admin.id, created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            data_limit_reset_strategy=UserDataLimitResetStrategy.no_reset,
        )
        db.add(user)
        db.flush()
        return user
    return _make


@pytest.fixture
def make_settings(db):
    """Factory to create MarzyarAdminSettings rows."""
    def _make(admin, users_limit=None, traffic_limit=None,
              oversell_allowed=False, allowed_inbounds=None, quota_used_traffic=0):
        settings = MarzyarAdminSettings(
            admin_id=admin.id, users_limit=users_limit,
            traffic_limit=traffic_limit, oversell_allowed=oversell_allowed,
            allowed_inbounds=allowed_inbounds, quota_used_traffic=quota_used_traffic,
        )
        db.add(settings)
        db.flush()
        return settings
    return _make


@pytest.fixture
def make_lock(db):
    """Factory to create MarzyarUserLock rows."""
    def _make(user, admin, original_status="active", reason="admin_quota_exceeded"):
        lock = MarzyarUserLock(
            user_id=user.id, admin_id=admin.id,
            locked_at=datetime.now(timezone.utc).replace(tzinfo=None), lock_reason=reason,
            original_status=original_status,
        )
        db.add(lock)
        db.flush()
        return lock
    return _make
