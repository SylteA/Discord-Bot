from .model import Model


class LevellingRole(Model):
    id: int
    required_xp: int
    guild_id: int
    role_id: int
