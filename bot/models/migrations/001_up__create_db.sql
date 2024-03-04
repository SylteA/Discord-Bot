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
)
