CREATE TABLE IF NOT EXISTS migrations
(
    id        SERIAL NOT NULL,
    version   SMALLINT NOT NULL,
    direction TEXT NOT NULL,
    name      TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    PRIMARY KEY (id)
)
