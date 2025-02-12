from .model import Model


class GuildConfig(Model):
    guild_id: int
    min_xp: int
    max_xp: int
    xp_boost: int
    custom_role_log_channel_id: int | None
    divider_role_id: int | None
