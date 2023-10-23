DROP FUNCTION IF EXISTS snowflake_to_timestamp(flake bigint);
DROP FUNCTION IF EXISTS create_snowflake(shard_id integer);
DROP SEQUENCE IF EXISTS global_snowflake_id_seq;
