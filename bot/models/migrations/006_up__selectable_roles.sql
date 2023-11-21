CREATE TABLE IF NOT EXISTS selectable_roles (
    guild_id           BIGINT NOT NULL,
    role_id            BIGINT NOT NULL,
    role_name          VARCHAR NOT NULL,
    PRIMARY KEY (guild_id, role_id)
);
