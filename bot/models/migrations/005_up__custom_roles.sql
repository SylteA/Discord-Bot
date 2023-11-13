ALTER TABLE custom_roles ADD COLUMN user_id BIGINT;


-- Create a temporary column `new_color` and update the table with the values from this table.
-- Drop the old color column, then rename the new one and set it to non-nullable.
BEGIN;
ALTER TABLE custom_roles ADD COLUMN new_color INTEGER;
UPDATE custom_roles SET new_color = CAST(color AS INTEGER);
ALTER TABLE custom_roles DROP COLUMN color;
ALTER TABLE custom_roles RENAME COLUMN new_color TO color;
ALTER TABLE custom_roles ALTER COLUMN color SET NOT NULL;
COMMIT;
