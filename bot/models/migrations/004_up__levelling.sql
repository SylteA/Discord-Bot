CREATE TABLE IF NOT EXISTS levelling_users
(
    id                 BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    guild_id           BIGINT NOT NULL,
    user_id            BIGINT NOT NULL,
    total_xp           INT NOT NULL DEFAULT 0,
    last_msg           BIGINT NOT NULL DEFAULT create_snowflake(),
    CONSTRAINT levelling_users_guild_id_user_id_key UNIQUE (guild_id, user_id)
);


CREATE TABLE IF NOT EXISTS custom_roles
(
    id          BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    guild_id    BIGINT NOT NULL,
    role_id     BIGINT NOT NULL,
    name        VARCHAR NOT NULL,
    color       VARCHAR NOT NULL,
    CONSTRAINT custom_roles_role_id UNIQUE (role_id),
    CONSTRAINT custom_roles_guild_id_role_id UNIQUE (guild_id, role_id)
);

CREATE TABLE IF NOT EXISTS levelling_roles
(
    id          SERIAL PRIMARY KEY DEFAULT create_snowflake(),
    required_xp INTEGER NOT NULL,
    guild_id    BIGINT NOT NULL,
    role_id     BIGINT NOT NULL REFERENCES custom_roles(role_id),
    CONSTRAINT levelling_roles_guild_id_role_id_key UNIQUE (guild_id, role_id)
);

CREATE TABLE IF NOT EXISTS persisted_roles
(
    id                 SERIAL PRIMARY KEY DEFAULT create_snowflake(),
    guild_id           BIGINT NOT NULL,
    user_id            BIGINT NOT NULL,
    role_id            BIGINT NOT NULL REFERENCES custom_roles(role_id),
    CONSTRAINT persisted_roles_guild_id_role_id_user_id__key UNIQUE (guild_id, role_id, user_id)
);


CREATE TABLE IF NOT EXISTS levelling_ignored_channels
(
    id          SERIAL PRIMARY KEY DEFAULT create_snowflake(),
    guild_id    BIGINT NOT NULL,
    channel_id  BIGINT NOT NULL,
    CONSTRAINT levelling_ignored_channels_guild_id_and_channel_id_key UNIQUE (guild_id, channel_id)
);
