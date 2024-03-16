CREATE TABLE IF NOT EXISTS command_usage
(
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT,
    interaction_id BIGINT PRIMARY KEY,
    command_id BIGINT NOT NULL,
    command_name TEXT NOT NULL,
    options JSON NOT NULL
)
