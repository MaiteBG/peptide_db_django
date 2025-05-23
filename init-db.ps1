# Requires PostgreSQL client tools (psql) to be installed
# Run this script using PowerShell (e.g., .\init-db.ps1)

# Load environment variables from .env file
$envVars = Get-Content ".env" | ForEach-Object {
    if ($_ -match "^\s*([^#=]+?)\s*=\s*(.+)\s*$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim('" ')
        [System.Environment]::SetEnvironmentVariable($key, $value)
    }
}

# Use the loaded environment variables
$superuser = $env:POSTGRES_SUPERUSER
$superpass = $env:POSTGRES_SUPERUSER_PASS
$adminUser = $env:POSTGRES_ADMIN
$adminPass = $env:POSTGRES_ADMIN_PASS
$normalUser = $env:POSTGRES_USER
$normalPass = $env:POSTGRES_USER_PASS
$dbName = $env:PEPTIDE_DB

Write-Host "Starting PostgreSQL initial setup..."

# Function to execute psql commands
function Run-PSQL($sql, $dbname = "postgres") {
    return & psql -U $superuser -d $dbname -h localhost -p 5432 -tAc $sql
}

# Set the password for psql authentication
$env:PGPASSWORD = $superpass

# Check if the admin role exists; if not, create it
$adminExists = Run-PSQL "SELECT 1 FROM pg_roles WHERE rolname='$adminUser'"
if (-not $adminExists) {
    Write-Host "Creating admin role..."
    Run-PSQL "CREATE ROLE $adminUser WITH LOGIN PASSWORD '$adminPass' CREATEDB CREATEROLE NOINHERIT;"
}

# Check if the regular user role exists; if not, create it
$userExists = Run-PSQL "SELECT 1 FROM pg_roles WHERE rolname='$normalUser'"
if (-not $userExists) {
    Write-Host "Creating regular user role..."
    Run-PSQL "CREATE ROLE $normalUser WITH LOGIN PASSWORD '$normalPass';"
}

# Check if the database exists; if not, create it
$dbExists = Run-PSQL "SELECT 1 FROM pg_database WHERE datname='$dbName'"
Write-Host "Checking database existence... -$dbName-"
if (-not $dbExists) {
    Write-Host "Creating database..."
    Run-PSQL "CREATE DATABASE $dbName OWNER $adminUser;"
}

# Grant necessary privileges
Write-Host "Granting privileges..."
$grantSql = @"
GRANT ALL PRIVILEGES ON DATABASE $dbName TO $adminUser;
GRANT CONNECT ON DATABASE $dbName TO $normalUser;
GRANT USAGE ON SCHEMA public TO $normalUser;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $normalUser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $normalUser;
"@
psql -U $superuser --dbname $dbName -h localhost -p 5432 -c $grantSql

Write-Host "PostgreSQL setup completed successfully."
