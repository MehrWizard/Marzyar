from typing import Optional, Union

import typer
from decouple import UndefinedValueError, config
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.db import GetDB, crud
from app.db.models import Admin, User
from app.models.admin import AdminCreate, AdminPartialModify
from app.utils.system import readable_size

from . import utils

app = typer.Typer(no_args_is_help=True)


def validate_telegram_id(value: Union[int, str]) -> Union[int, None]:
    if not value:
        return 0
    if not isinstance(value, int) and not value.isdigit():
        raise typer.BadParameter("Telegram ID must be an integer.")
    if int(value) < 0:
        raise typer.BadParameter("Telegram ID must be a positive integer.")
    return value


def validate_discord_webhook(value: str) -> Union[str, None]:
    if not value or value == "0":
        return ""
    if not value.startswith("https://discord.com/api/webhooks/"):
        utils.error("Discord webhook must start with 'https://discord.com/api/webhooks/'")
    return value


def calculate_admin_usage(admin_id: int) -> str:
    with GetDB() as db:
        usage = db.query(func.sum(User.used_traffic)).filter_by(admin_id=admin_id).first()[0]
        return readable_size(int(usage or 0))


def calculate_admin_reseted_usage(admin_id: int) -> str:
    with GetDB() as db:
        usage = db.query(func.sum(User.reseted_usage)).filter_by(admin_id=admin_id).scalar()
        return readable_size(int(usage or 0))


@app.command(name="list")
def list_admins(
    offset: Optional[int] = typer.Option(None, *utils.FLAGS["offset"]),
    limit: Optional[int] = typer.Option(None, *utils.FLAGS["limit"]),
    username: Optional[str] = typer.Option(None, *utils.FLAGS["username"], help="Search by username"),
):
    """Displays a table of admins with Marzyar reseller limits and quotas"""
    with GetDB() as db:
        admins: list[Admin] = crud.get_admins(db, offset=offset, limit=limit, username=username)
        from app.marzyar import crud as marzyar_crud
        rows = []
        for admin in admins:
            s = marzyar_crud.get_admin_settings(db, admin.id)
            u_count = marzyar_crud.get_admin_user_count(db, admin.id)
            u_str = f"{u_count}/{s.users_limit}" if (s and s.users_limit is not None) else str(u_count)
            t_limit_str = readable_size(s.traffic_limit) if (s and s.traffic_limit is not None) else "Unlimited"
            consumed_str = readable_size(marzyar_crud.get_admin_total_consumed_traffic(db, admin.id, s)) if s else readable_size(admin.users_usage)
            oversell_str = ("Yes" if s.oversell_allowed else "No") if s else "N/A"
            locked_count = len(marzyar_crud.get_locked_user_ids_for_admin(db, admin.id)) if s else 0
            inbounds_str = ", ".join(s.allowed_inbounds) if (s and s.allowed_inbounds) else "All"
            rows.append((
                str(admin.username),
                u_str,
                t_limit_str,
                consumed_str,
                oversell_str,
                str(locked_count),
                inbounds_str,
                "✔️" if admin.is_sudo else "✖️",
                utils.readable_datetime(admin.created_at),
            ))

        utils.print_table(
            table=Table("Username", "Users", "Quota Limit", "Consumed", "Oversell", "Locked", "Inbounds", "Is Sudo", "Created at"),
            rows=rows
        )


@app.command(name="delete")
def delete_admin(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help="Skips confirmations")
):
    """
    Deletes the specified admin

    Confirmations can be skipped using `--yes/-y` option.
    """
    with GetDB() as db:
        admin: Union[Admin, None] = crud.get_admin(db, username=username)
        if not admin:
            utils.error(f"There's no admin with username \"{username}\"!")

        if yes_to_all or typer.confirm(f'Are you sure about deleting "{username}"?', default=False):
            crud.remove_admin(db, admin)
            utils.success(f'"{username}" deleted successfully.')
        else:
            utils.error("Operation aborted!")


@app.command(name="create")
def create_admin(
    username: str = typer.Option(..., *utils.FLAGS["username"], show_default=False, prompt=True),
    is_sudo: bool = typer.Option(False, *utils.FLAGS["is_sudo"], prompt=True),
    password: str = typer.Option(..., prompt=True, confirmation_prompt=True,
                                 hide_input=True, hidden=True, envvar=utils.PASSWORD_ENVIRON_NAME),
    telegram_id: str = typer.Option('', *utils.FLAGS["telegram_id"], prompt="Telegram ID",
                                    show_default=False, callback=validate_telegram_id),
    discord_webhook: str = typer.Option('', *utils.FLAGS["discord_webhook"], prompt=True,
                                        show_default=False, callback=validate_discord_webhook),
):
    """
    Creates an admin

    Password can also be set using the `MARZBAN_ADMIN_PASSWORD` environment variable for non-interactive usages.
    """
    with GetDB() as db:
        try:
            crud.create_admin(db, AdminCreate(username=username,
                                              password=password,
                                              is_sudo=is_sudo,
                                              telegram_id=telegram_id,
                                              discord_webhook=discord_webhook))
            utils.success(f'Admin "{username}" created successfully.')
        except IntegrityError:
            utils.error(f'Admin "{username}" already exists!')


@app.command(name="update")
def update_admin(username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True, show_default=False)):
    """
    Updates the specified admin

    NOTE: This command CAN NOT be used non-interactively.
    """

    def _get_modify_model(admin: Admin):
        Console().print(
            Panel(f'Editing "{username}". Just press "Enter" to leave each field unchanged.')
        )

        is_sudo: bool = typer.confirm("Is sudo", default=admin.is_sudo)
        new_password: Union[str, None] = typer.prompt(
            "New password",
            default="",
            show_default=False,
            confirmation_prompt=True,
            hide_input=True
        ) or None

        telegram_id: str = typer.prompt("Telegram ID (Enter 0 to clear current value)",
                                        default=admin.telegram_id or "")
        telegram_id = validate_telegram_id(telegram_id)

        discord_webhook: str = typer.prompt("Discord webhook (Enter 0 to clear current value)",
                                            default=admin.discord_webhook or "")
        discord_webhook = validate_discord_webhook(discord_webhook)

        return AdminPartialModify(
            is_sudo=is_sudo,
            password=new_password,
            telegram_id=telegram_id,
            discord_webhook=discord_webhook
        )

    with GetDB() as db:
        admin: Union[Admin, None] = crud.get_admin(db, username=username)
        if not admin:
            utils.error(f"There's no admin with username \"{username}\"!")

        crud.partial_update_admin(db, admin, _get_modify_model(admin))
        utils.success(f'Admin "{username}" updated successfully.')


@app.command(name="import-from-env")
def import_from_env(yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help="Skips confirmations")):
    """
    Imports the sudo admin from env

    Confirmations can be skipped using `--yes/-y` option.

    What does it do?
      - Creates a sudo admin according to `SUDO_USERNAME` and `SUDO_PASSWORD`.
      - Links any user which doesn't have an `admin_id` to the imported sudo admin.
    """
    try:
        username, password = config("SUDO_USERNAME"), config("SUDO_PASSWORD")
    except UndefinedValueError:
        utils.error(
            "Unable to get SUDO_USERNAME and/or SUDO_PASSWORD.\n"
            "Make sure you have set them in the env file or as environment variables."
        )

    if not (username and password):
        utils.error("Unable to retrieve username and password.\n"
                    "Make sure both SUDO_USERNAME and SUDO_PASSWORD are set.")

    with GetDB() as db:
        admin: Union[None, Admin] = None

        # If env admin already exists
        if current_admin := crud.get_admin(db, username=username):
            if not yes_to_all and not typer.confirm(
                f'Admin "{username}" already exists. Do you want to sync it with env?', default=None
            ):
                utils.error("Aborted.")

            admin = crud.partial_update_admin(
                db,
                current_admin,
                AdminPartialModify(password=password, is_sudo=True)
            )
        # If env admin does not exist yet
        else:
            admin = crud.create_admin(db, AdminCreate(
                username=username,
                password=password,
                is_sudo=True
            ))

        updated_user_count = db.query(User).filter_by(admin_id=None).update({"admin_id": admin.id})
        db.commit()

        utils.success(
            f'Admin "{username}" imported successfully.\n'
            f"{updated_user_count} users' admin_id set to the {username}'s id.\n"
            'You must delete SUDO_USERNAME and SUDO_PASSWORD from your env file now.'
        )


@app.command(name="set-quota")
def set_quota(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    traffic_limit_gb: Optional[float] = typer.Option(None, "--traffic-limit", "-t", help="Traffic limit in GB (0 to remove limit)"),
    users_limit: Optional[int] = typer.Option(None, "--users-limit", "-u", help="Users count limit (0 to remove limit)"),
    oversell: Optional[bool] = typer.Option(None, "--oversell/--no-oversell", help="Allow or disallow overselling"),
    inbounds: Optional[str] = typer.Option(None, "--inbounds", "-i", help="Comma-separated list of allowed inbound tags (pass 'all' to allow all)"),
):
    """
    Configure Marzyar reseller limits and quota for an admin.
    """
    with GetDB() as db:
        admin: Union[Admin, None] = crud.get_admin(db, username=username)
        if not admin:
            utils.error(f'There\'s no admin with username "{username}"!')

        from app.marzyar import crud as marzyar_crud
        from app.marzyar import quota as marzyar_quota
        from app.marzyar.schemas import MarzyarAdminSettingsModify

        modify_data = {}
        if traffic_limit_gb is not None:
            if traffic_limit_gb <= 0:
                modify_data["traffic_limit"] = None
            else:
                modify_data["traffic_limit"] = int(traffic_limit_gb * 1073741824)

        if users_limit is not None:
            if users_limit <= 0:
                modify_data["users_limit"] = None
            else:
                modify_data["users_limit"] = users_limit

        if oversell is not None:
            modify_data["oversell_allowed"] = oversell

        if inbounds is not None:
            if inbounds.strip().lower() in ("all", "*", ""):
                modify_data["allowed_inbounds"] = None
            else:
                modify_data["allowed_inbounds"] = [tag.strip() for tag in inbounds.split(",") if tag.strip()]

        if not modify_data:
            utils.error("No settings provided to update. Specify --traffic-limit, --users-limit, --oversell, or --inbounds.")

        modify = MarzyarAdminSettingsModify(**modify_data)
        marzyar_crud.update_admin_settings(db, admin.id, modify)
        marzyar_quota.audit_admin_quotas(db)

        utils.success(f'Marzyar settings for "{username}" updated successfully.')


@app.command(name="reset-quota")
def reset_quota(
    username: str = typer.Option(..., *utils.FLAGS["username"], prompt=True),
    yes_to_all: bool = typer.Option(False, *utils.FLAGS["yes_to_all"], help="Skips confirmations"),
):
    """
    Reset an admin's consumed quota counter and unlock their users.
    """
    with GetDB() as db:
        admin: Union[Admin, None] = crud.get_admin(db, username=username)
        if not admin:
            utils.error(f'There\'s no admin with username "{username}"!')

        if not yes_to_all and not typer.confirm(
            f'Are you sure you want to reset consumed quota for "{username}"? All locked users will be unlocked.',
            default=False
        ):
            utils.error("Operation aborted!")

        from app.marzyar import crud as marzyar_crud
        from app.marzyar import quota as marzyar_quota

        marzyar_crud.reset_admin_quota_counter(db, admin.id)
        marzyar_quota.audit_admin_quotas(db)

        utils.success(f'Consumed quota for "{username}" reset successfully and users unlocked.')

