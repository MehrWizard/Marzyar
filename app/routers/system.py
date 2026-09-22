from typing import Dict, List, Union

from fastapi import APIRouter, Depends, HTTPException

from app import __version__, xray
from app.db import Session, crud, get_db
from app.models.admin import Admin
from app.models.proxy import ProxyHost, ProxyInbound, ProxyTypes
from app.models.system import SystemStats
from app.models.user import UserStatus
from app.utils import responses
from app.utils.system import cpu_usage, memory_usage, realtime_bandwidth

router = APIRouter(tags=["System"], prefix="/api", responses={401: responses._401})


@router.get("/version")
def get_version_info():
    """Retrieve the application version."""
    return {"version": __version__}


@router.get("/system", response_model=SystemStats)
def get_system_stats(
    db: Session = Depends(get_db), admin: Admin = Depends(Admin.get_current)
):
    """Fetch system stats including memory, CPU, and user metrics."""
    mem = memory_usage()
    cpu = cpu_usage()
    system = crud.get_system_usage(db)
    dbadmin: Union[Admin, None] = crud.get_admin(db, admin.username)

    status_counts = crud.get_users_status_counts(
        db, admin=dbadmin if not admin.is_sudo else None
    )
    users_active = status_counts.get(UserStatus.active, 0)
    users_disabled = status_counts.get(UserStatus.disabled, 0)
    users_on_hold = status_counts.get(UserStatus.on_hold, 0)
    users_expired = status_counts.get(UserStatus.expired, 0)
    users_limited = status_counts.get(UserStatus.limited, 0)
    total_user = sum(status_counts.values())
    online_users = crud.count_online_users(
        db, seconds=60, admin=dbadmin if not admin.is_sudo else None
    )
    realtime_bandwidth_stats = realtime_bandwidth()

    users_limit = None
    traffic_limit = None
    if not admin.is_sudo and dbadmin:
        try:
            from app.marzyar import crud as marzyar_crud
            admin_settings = marzyar_crud.get_admin_settings(db, dbadmin.id)
            if admin_settings:
                users_limit = admin_settings.users_limit
                traffic_limit = admin_settings.traffic_limit
            consumed = marzyar_crud.get_admin_total_consumed_traffic(db, dbadmin.id, admin_settings)
            incoming_bandwidth = 0
            outgoing_bandwidth = consumed
        except Exception:
            incoming_bandwidth = 0
            outgoing_bandwidth = dbadmin.users_usage
    else:
        incoming_bandwidth = system.uplink if system else 0
        outgoing_bandwidth = system.downlink if system else 0

    return SystemStats(
        version=__version__,
        mem_total=mem.total,
        mem_used=mem.used,
        cpu_cores=cpu.cores,
        cpu_usage=cpu.percent,
        total_user=total_user,
        online_users=online_users,
        users_active=users_active,
        users_disabled=users_disabled,
        users_expired=users_expired,
        users_limited=users_limited,
        users_on_hold=users_on_hold,
        incoming_bandwidth=incoming_bandwidth,
        outgoing_bandwidth=outgoing_bandwidth,
        incoming_bandwidth_speed=realtime_bandwidth_stats.incoming_bytes,
        outgoing_bandwidth_speed=realtime_bandwidth_stats.outgoing_bytes,
        users_limit=users_limit,
        traffic_limit=traffic_limit,
    )


@router.get("/inbounds", response_model=Dict[ProxyTypes, List[ProxyInbound]])
def get_inbounds(
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
):
    """Retrieve inbound configurations grouped by protocol (filtered by allowed inbounds for resellers)."""
    inbounds = xray.config.inbounds_by_protocol
    if admin.is_sudo:
        return inbounds

    try:
        from app.marzyar import crud as marzyar_crud
        admin_id = marzyar_crud.get_admin_id(db, admin)
        if admin_id:
            settings = marzyar_crud.get_admin_settings(db, admin_id)
            if settings and settings.allowed_inbounds:
                allowed = set(settings.allowed_inbounds)
                filtered = {}
                for proto, inb_list in inbounds.items():
                    matching = [i for i in inb_list if i.get("tag") in allowed]
                    if matching:
                        filtered[proto] = matching
                return filtered
    except Exception:
        pass

    return inbounds


@router.get(
    "/hosts", response_model=Dict[str, List[ProxyHost]], responses={403: responses._403}
)
def get_hosts(
    db: Session = Depends(get_db), admin: Admin = Depends(Admin.check_sudo_admin)
):
    """Get a list of proxy hosts grouped by inbound tag."""
    hosts = {tag: crud.get_hosts(db, tag) for tag in xray.config.inbounds_by_tag}
    return hosts


@router.put(
    "/hosts", response_model=Dict[str, List[ProxyHost]], responses={403: responses._403}
)
def modify_hosts(
    modified_hosts: Dict[str, List[ProxyHost]],
    db: Session = Depends(get_db),
    admin: Admin = Depends(Admin.check_sudo_admin),
):
    """Modify proxy hosts and update the configuration."""
    for inbound_tag in modified_hosts:
        if inbound_tag not in xray.config.inbounds_by_tag:
            raise HTTPException(
                status_code=400, detail=f"Inbound {inbound_tag} doesn't exist"
            )

    for inbound_tag, hosts in modified_hosts.items():
        crud.update_hosts(db, inbound_tag, hosts)

    xray.hosts.update()

    return {tag: crud.get_hosts(db, tag) for tag in xray.config.inbounds_by_tag}
