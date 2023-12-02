CREATE TABLE IF NOT EXISTS configs
(
    id                          BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    guild_id                    BIGINT NOT NULL,
    min_xp                      INT NOT NULL DEFAULT 15,
    max_xp                      INT NOT NULL DEFAULT 25,
    xp_boost                    INT NOT NULL DEFAULT 1,
    custom_role_log_channel_id  BIGINT,
);
