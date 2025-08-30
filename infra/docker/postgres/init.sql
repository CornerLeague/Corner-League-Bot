-- Initialize the sports database
-- This script runs when the PostgreSQL container starts for the first time

-- The database and user are already created by environment variables
-- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
-- This file can contain additional setup if needed

-- Grant all privileges to the sports_user on the sportsdb database
GRANT ALL PRIVILEGES ON DATABASE sportsdb TO sports_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sports_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sports_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO sports_user;
