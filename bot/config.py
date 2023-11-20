import json
import logging

from pydantic import BaseModel, BaseSettings, PostgresDsn, ValidationError, validator

log = logging.getLogger(__name__)


class AoC(BaseModel):
    channel_id: int
    role_id: int
    session_cookie: str


class Bot(BaseModel):
    commands_channels_ids: list[int]
    games_channel_id: int  # #bot-games
    token: str

    @validator("commands_channels_ids", pre=True)
    def val_func(cls, v):
        return json.loads(v)


class Challenges(BaseModel):
    channel_id: int
    discussion_channel_id: int
    host_helper_role_id: int
    host_role_id: int
    info_channel_id: int
    participant_role_id: int
    submissions_channel_id: int
    submitted_role_id: int
    submit_channel_id: int
    winner_role_id: int


class CoC(BaseModel):
    channel_id: int
    message_id: int
    role_id: int


class Guild(BaseModel):
    id: int
    welcomes_channel_id: int


class Moderation(BaseModel):
    admin_roles_ids: list[int]
    staff_role_id: int

    @validator("admin_roles_ids", pre=True)
    def val_func(cls, v):
        return json.loads(v)


class Postgres(BaseModel):
    max_pool_connections: int
    min_pool_connections: int
    uri: PostgresDsn


class Tags(BaseModel):
    log_channel_id: int
    required_role_id: int  # [lvl 30] Engineer


class Timathon(BaseModel):
    channel_id: int
    participant_role_id: int


class Hastebin(BaseModel):
    base_url: str


class ErrorHandling(BaseModel):
    webhook_url: str


class CustomRoles(BaseModel):
    log_channel_id: int
    divider_role_id: int


class YouTube(BaseModel):
    channel_id: str

    text_channel_id: int
    role_id: int


class Settings(BaseSettings):
    aoc: AoC
    bot: Bot
    challenges: Challenges
    coc: CoC
    postgres: Postgres
    guild: Guild
    moderation: Moderation
    tags: Tags
    timathon: Timathon
    hastebin: Hastebin
    errors: ErrorHandling
    custom_roles: CustomRoles
    youtube: YouTube

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


try:
    settings = Settings()
except ValidationError as e:
    log.error("Damn you messed up the configuration\n" + str(e))
    exit(1)
