#!/bin/bash
set -e

echo "Starting PostgreSQL initial setup..."

# Check if the admin role exists, if not, create it with CREATEDB and CREATEROLE but NOT SUPERUSER
psql -U "$POSTGRES_SUPERUSER" -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_ADMIN'" | grep -q 1 || \
psql -U "$POSTGRES_SUPERUSER" -d postgres -c "CREATE ROLE $POSTGRES_ADMIN WITH LOGIN PASSWORD '$POSTGRES_ADMIN_PASS';"


# Check if the regular user exists, if not, create it (no special privileges)
psql -U "$POSTGRES_SUPERUSER" -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_RESTRICTED_USER'" | grep -q 1 || \
psql -U "$POSTGRES_SUPERUSER" -d postgres -c "CREATE ROLE $POSTGRES_RESTRICTED_USER WITH LOGIN PASSWORD '$POSTGRES_RESTRICTED_USER_PASS';"

# Check if the database exists, if not, create it owned by the admin user
psql -U "$POSTGRES_SUPERUSER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$PEPTIDE_DB'" | grep -q 1 || \
psql -U "$POSTGRES_SUPERUSER" -d postgres -c "CREATE DATABASE $PEPTIDE_DB OWNER $POSTGRES_ADMIN;"


# Dar permisos sobre $PEPTIDE_DB (no sobre postgres) para admin y user
psql -U "$POSTGRES_SUPERUSER" --dbname "$PEPTIDE_DB" <<-EOSQL
    -- Admin user gets all privileges on the peptide database
    GRANT ALL PRIVILEGES ON DATABASE $PEPTIDE_DB TO $POSTGRES_ADMIN;

    -- Regular user can connect and read data from public schema
    GRANT CONNECT ON DATABASE $PEPTIDE_DB TO $POSTGRES_RESTRICTED_USER;
    GRANT USAGE ON SCHEMA public TO $POSTGRES_RESTRICTED_USER;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO $POSTGRES_RESTRICTED_USER;

    -- Ensure future tables in public schema are readable by regular user
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $POSTGRES_RESTRICTED_USER;
EOSQL

echo "PostgreSQL setup for $PEPTIDE_DB completed successfully."


