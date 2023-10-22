CREATE SEQUENCE IF NOT EXISTS global_snowflake_id_seq;

CREATE OR REPLACE FUNCTION create_snowflake(shard_id INT DEFAULT 1)
    RETURNS bigint
    LANGUAGE 'plpgsql'
AS $$
DECLARE
    our_epoch bigint := 1609459200;
    seq_id bigint;
    now_millis bigint;
    result bigint:= 0;
BEGIN
    SELECT nextval('global_snowflake_id_seq') % 1024 INTO seq_id;

    SELECT FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000) INTO now_millis;
    result := (now_millis - our_epoch) << 22;
    result := result | (shard_id << 9);
    result := result | (seq_id);
	return result;
END;
$$;

CREATE OR REPLACE FUNCTION snowflake_to_timestamp(flake BIGINT)
    RETURNS TIMESTAMP
    LANGUAGE 'plpgsql'
AS $BODY$
DECLARE
    our_epoch BIGINT := 1609459200;
BEGIN
    RETURN to_timestamp(((flake >> 22) + our_epoch) / 1000);
END;
$BODY$;
