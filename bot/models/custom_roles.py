from .model import Model


class CustomRoles(Model):
    id: int
    guild_id: int
    role_id: int
    name: str
    color: str
