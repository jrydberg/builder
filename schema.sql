CREATE TABLE build (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       app VARCHAR(255),
       name VARCHAR(255),
       image VARCHAR(255),
       pstable VARCHAR(65535),
       timestamp DATETIME
);
CREATE UNIQUE INDEX app_name_idx ON build(app, name);
CREATE INDEX app_idx ON build(app);
