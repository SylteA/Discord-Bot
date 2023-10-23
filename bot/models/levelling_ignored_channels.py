from .model import Model


class IgnoredChannel(Model):
    id: int
    guild_id: int
    channel_id: int
