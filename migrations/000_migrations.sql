CREATE TABLE IF NOT EXISTS migrations
(
    id        SERIAL,
    version   SMALLINT,
    direction TEXT,
    name      TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
)
