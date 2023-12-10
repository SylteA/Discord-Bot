CREATE TABLE IF NOT EXISTS guild_configs
(
    guild_id                    BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    min_xp                      INT NOT NULL DEFAULT 15,
    max_xp                      INT NOT NULL DEFAULT 25,
    xp_boost                    INT NOT NULL DEFAULT 1,
    custom_role_log_channel_id  BIGINT,
    divider_role_id             BIGINT
);


ALTER TABLE migrations ALTER COLUMN id SET NOT NULL;
ALTER TABLE migrations ALTER COLUMN version SET NOT NULL;
ALTER TABLE migrations ALTER COLUMN direction SET NOT NULL;
ALTER TABLE migrations ALTER COLUMN name SET NOT NULL;
ALTER TABLE migrations ALTER COLUMN timestamp SET NOT NULL;
ALTER TABLE migrations ADD PRIMARY KEY (id);
