CREATE TABLE IF NOT EXISTS messages
(
    created_at DATE,
    content    VARCHAR,
    message_id BIGINT,
    channel_id BIGINT,
    guild_id   BIGINT,
    author_id  BIGINT
);

CREATE TABLE IF NOT EXISTS users
(
    id            BIGINT PRIMARY KEY,
    commands_used INT,
    joined_at     TIMESTAMP,
    messages_sent INT
);

CREATE TABLE IF NOT EXISTS reps
(
    rep_id     BIGINT,
    user_id    BIGINT,
    author_id  BIGINT,
    repped_at  TIMESTAMP,
    extra_info TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS gconfigs
(
    guild_id           BIGINT PRIMARY KEY,
    blacklist_urls     CHARACTER VARYING[],
    whitelist_channels BIGINT[],
    reasons            JSON,
    enabled            BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS tags
(
    guild_id   BIGINT,
    creator_id BIGINT,
    text       VARCHAR,
    name       VARCHAR PRIMARY KEY,
    uses       INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS polls
(
    guild_id    BIGINT,
    author_id   BIGINT,
    description VARCHAR,
    options     JSON,
    replies     JSON,
    created_at  TIMESTAMP,
    channel_id  BIGINT,
    message_id  BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS levels
(
    guild_id           BIGINT,
    user_id            BIGINT,
    total_xp           INT DEFAULT 0,
    last_msg           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_user PRIMARY KEY(guild_id,user_id)
);

CREATE TABLE IF NOT EXISTS roles
(
    role_id     BIGINT PRIMARY KEY,
    guild_id    BIGINT,
    name        VARCHAR,
    color       VARCHAR
);

CREATE TABLE IF NOT EXISTS persistent_roles
(
    id                 SERIAL PRIMARY KEY,
    guild_id           BIGINT,
    user_id            BIGINT,
    role_id            BIGINT,
    CONSTRAINT fk_roles FOREIGN KEY(role_id) REFERENCES roles(role_id),
    CONSTRAINT unique_guild_user_role UNIQUE (guild_id, user_id, role_id)
);


CREATE TABLE IF NOT EXISTS ignored_channels
(
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT,
    channel_id  BIGINT,
    CONSTRAINT unique_ignored_channel UNIQUE (guild_id, channel_id)

);

CREATE TABLE IF NOT EXISTS levelling_roles
(
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT,
    role_id     BIGINT,
    level       INT,
    CONSTRAINT fk_levelling_roles FOREIGN KEY(role_id) REFERENCES roles(role_id)
);
