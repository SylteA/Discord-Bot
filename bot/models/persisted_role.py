from .model import Model


class PersistedRole(Model):
    id: int
    guild_id: int
    user_id: int
    role_id: int
