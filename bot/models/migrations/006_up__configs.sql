CREATE TABLE IF NOT EXISTS guild_configs
(
    guild_id                    BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    min_xp                      INT NOT NULL DEFAULT 15,
    max_xp                      INT NOT NULL DEFAULT 25,
    xp_boost                    INT NOT NULL DEFAULT 1,
    custom_role_log_channel_id  BIGINT,
    divider_role_id             BIGINT,
);
