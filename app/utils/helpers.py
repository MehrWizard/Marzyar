import json
from datetime import datetime as dt, timezone
from uuid import UUID


def calculate_usage_percent(used_traffic: int, data_limit: int) -> float:
    if not data_limit or data_limit <= 0:
        return 0.0
    return (used_traffic * 100) / data_limit


def calculate_expiration_days(expire: int) -> int:
    if not expire:
        return 0
    return (dt.fromtimestamp(expire, timezone.utc) - dt.now(timezone.utc)).days


def yml_uuid_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return super().default(self, obj)
