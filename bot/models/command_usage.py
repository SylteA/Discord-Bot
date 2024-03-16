from .model import Model


class CommandUsage(Model):
    user_id: int
    guild_id: int
    channel_id: int | None
    interaction_id: int
    command_id: int
    command_name: str
    options: dict
