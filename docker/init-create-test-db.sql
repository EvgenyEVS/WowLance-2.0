-- Runs only on first volume init (empty data dir).
-- For an existing volume, pytest conftest also ensures wowlance_test exists.
CREATE DATABASE wowlance_test;
