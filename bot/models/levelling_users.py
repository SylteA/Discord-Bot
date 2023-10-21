from .model import Model


class LevellingUser(Model):
    id: int
    guild_id: int
    user_id: int
    total_xp: int
