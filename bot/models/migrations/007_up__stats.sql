CREATE TABLE stats(
    id          BIGINT PRIMARY KEY DEFAULT create_snowflake(),
    guild_id    BIGINT NOT NULL,
    cmd_name    VARCHAR NOT NULL,
    uses        INT NOT NULL DEFAULT 1,
    CONSTRAINT stats_guild_id_cmd_name_key UNIQUE(guild_id, cmd_name)
);
