def get_admins() -> list[int]:
    users = [305636851, 62863141, 360880304, 317914529]
    return list(users)


def is_admin(user_id: int) -> bool:
    return user_id in get_admins()
