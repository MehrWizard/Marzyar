from datetime import datetime

from app import logger, scheduler, xray
from app.db import crud, GetDB, get_users
from app.models.user import UserDataLimitResetStrategy, UserStatus

reset_strategy_to_days = {
    UserDataLimitResetStrategy.day.value: 1,
    UserDataLimitResetStrategy.week.value: 7,
    UserDataLimitResetStrategy.month.value: 30,
    UserDataLimitResetStrategy.year.value: 365,
}


def reset_user_data_usage():
    now = datetime.utcnow()
    with GetDB() as db:
        for user in get_users(db,
                              status=[
                                  UserStatus.active,
                                  UserStatus.limited
                              ],
                              reset_strategy=[
                                  UserDataLimitResetStrategy.day.value,
                                  UserDataLimitResetStrategy.week.value,
                                  UserDataLimitResetStrategy.month.value,
                                  UserDataLimitResetStrategy.year.value,
                              ]):
            last_reset_time = user.last_traffic_reset_time
            num_days_to_reset = reset_strategy_to_days[user.data_limit_reset_strategy]

            if not (now - last_reset_time).days >= num_days_to_reset:
                continue

            old_status = user.status
            crud.reset_user_data_usage(db, user)
            # make user active in xray if they were previously limited and are now active
            if old_status == UserStatus.limited and user.status == UserStatus.active:
                xray.operations.add_user(user)

            logger.info(f"User data usage reset for User \"{user.username}\"")

        try:
            from app.marzyar.quota import audit_admin_quotas
            audit_admin_quotas(db)
        except Exception:
            pass


scheduler.add_job(reset_user_data_usage, 'interval', coalesce=True, hours=1)
