CREATE EXTENSION IF NOT EXISTS pg_trgm;

ALTER TABLE tags DROP CONSTRAINT tags_pkey;
ALTER TABLE tags ADD COLUMN id SERIAL PRIMARY KEY;

ALTER TABLE tags RENAME COLUMN text TO content;
ALTER TABLE tags RENAME COLUMN creator_id TO author_id;
CREATE INDEX idx_author_guild ON tags (author_id, guild_id);

ALTER TABLE tags ALTER COLUMN created_at SET DEFAULT now();

ALTER TABLE tags ADD CONSTRAINT unique_name_guild UNIQUE (name, guild_id);
CREATE INDEX idx_name_guild ON tags (name, guild_id);
