CREATE TABLE IF NOT EXISTS levelling_users
(
    id                 SERIAL PRIMARY KEY,
    guild_id           BIGINT,
    user_id            BIGINT,
    total_xp           INT DEFAULT 0,
    last_msg           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT levelling_roles_guild_id_and_user_id_key UNIQUE (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS custom_roles
(
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT,
    role_id     BIGINT UNIQUE,
    name        VARCHAR,
    color       VARCHAR
);

CREATE TABLE IF NOT EXISTS persisted_roles
(
    id                 SERIAL PRIMARY KEY,
    guild_id           BIGINT,
    user_id            BIGINT,
    role_id            BIGINT,
    CONSTRAINT persisted_roles_role_id_fkey FOREIGN KEY(role_id) REFERENCES custom_roles(role_id),
    CONSTRAINT persisted_roles_guild_id_and_user_id_and_role_id_key UNIQUE (guild_id, user_id, role_id)
);


CREATE TABLE IF NOT EXISTS levelling_ignored_channels
(
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT,
    channel_id  BIGINT,
    CONSTRAINT levelling_ignored_channels_guild_id_and_channel_id_key UNIQUE (guild_id, channel_id)

);

CREATE TABLE IF NOT EXISTS levelling_roles
(
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT,
    role_id     BIGINT,
    level       INT,
    CONSTRAINT levelling_roles_role_id_fkey FOREIGN KEY(role_id) REFERENCES custom_roles(role_id),
    CONSTRAINT levelling_roles_guild_id_and_role_id_key UNIQUE (guild_id, role_id)
);
