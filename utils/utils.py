import os

__admins_ids = set(map(int, os.environ['ADMIN_IDS'].split(';')))


def get_admins() -> set[int]:
    return __admins_ids


def is_admin(user_id: int) -> bool:
    return user_id in get_admins()
