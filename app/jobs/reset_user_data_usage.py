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
            if old_status == UserStatus.limited and user.status == UserStatus.active and not user.is_locked:
                xray.operations.add_user(user)

            logger.info(f"User data usage reset for User \"{user.username}\"")

        # Also reset data usage for locked users whose periodic reset interval has elapsed
        try:
            from app.marzyar.crud import get_locked_users
            for lock, user, admin in get_locked_users(db):
                try:
                    # Skip locked users whose original status was expired or disabled
                    if lock.original_status in ('expired', 'disabled'):
                        continue
                    strategy_val = user.data_limit_reset_strategy.value if hasattr(user.data_limit_reset_strategy, 'value') else user.data_limit_reset_strategy
                    if strategy_val and strategy_val in reset_strategy_to_days:
                        last_reset_time = user.last_traffic_reset_time
                        num_days_to_reset = reset_strategy_to_days[strategy_val]
                        if (now - last_reset_time).days >= num_days_to_reset:
                            crud.reset_user_data_usage(db, user)
                            logger.info(f"Locked user data usage reset for User \"{user.username}\"")
                except Exception as e:
                    logger.error(f"[Marzyar] Error resetting locked user \"{user.username}\": {e}")
        except Exception as e:
            logger.error(f"[Marzyar] Error during locked users periodic data reset: {e}")

        try:
            from app.marzyar.quota import audit_admin_quotas
            audit_admin_quotas(db)
        except Exception:
            pass


scheduler.add_job(reset_user_data_usage, 'interval', coalesce=True, hours=1)
