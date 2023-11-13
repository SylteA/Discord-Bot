ALTER TABLE custom_roles DROP COLUMN user_id;

BEGIN;
ALTER TABLE custom_roles ADD COLUMN old_color VARCHAR NOT NULL;
UPDATE custom_roles SET old_color = CAST(color AS VARCHAR);
ALTER TABLE custom_roles DROP COLUMN color;
ALTER TABLE custom_roles RENAME COLUMN old_color TO color;
COMMIT;
