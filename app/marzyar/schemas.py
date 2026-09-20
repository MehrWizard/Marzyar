from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MarzyarAdminSettingsModify(BaseModel):
    users_limit: Optional[int] = Field(None, description="Maximum number of users allowed (null for unlimited)")
    traffic_limit: Optional[int] = Field(None, description="Maximum traffic quota in bytes (null for unlimited)")
    oversell_allowed: Optional[bool] = Field(None, description="False: allocated data limits; True: consumed traffic")
    allowed_inbounds: Optional[List[str]] = Field(None, description="List of permitted inbound tags (null for all)")


class MarzyarAdminSettingsResponse(BaseModel):
    admin_id: int
    username: str
    is_sudo: bool
    users_limit: Optional[int] = None
    traffic_limit: Optional[int] = None
    oversell_allowed: bool = False
    allowed_inbounds: Optional[List[str]] = None
    quota_used_traffic: int = 0
    current_users_count: int = 0
    current_allocated_traffic: int = 0
    current_consumed_traffic: int = 0
    is_quota_exceeded: bool = False
    is_user_limit_exceeded: bool = False
    locked_users_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MarzyarMyLimitsResponse(BaseModel):
    username: str
    is_sudo: bool
    users_limit: Optional[int] = None
    traffic_limit: Optional[int] = None
    oversell_allowed: bool = False
    allowed_inbounds: Optional[List[str]] = None
    current_users_count: int = 0
    current_allocated_traffic: int = 0
    current_consumed_traffic: int = 0
    is_quota_exceeded: bool = False
    is_user_limit_exceeded: bool = False
    locked_users_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MarzyarLockedUserResponse(BaseModel):
    user_id: int
    username: str
    admin_username: str
    locked_at: datetime
    lock_reason: str

    model_config = ConfigDict(from_attributes=True)
