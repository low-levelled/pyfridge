#!/bin/bash
# Creates the pyfridge database and runs schema + seed
# Usage: ./scripts/setup_db.sh

set -e

DB_NAME="${DB_NAME:-pyfridge}"
DB_USER="${DB_USER:-${USER:-$(whoami)}}"

echo "Creating database '$DB_NAME'..."
createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null || echo "(database already exists, continuing)"

echo "Running schema..."
psql -U "$DB_USER" -d "$DB_NAME" -f sql/schema.sql

echo "Running seed data..."
psql -U "$DB_USER" -d "$DB_NAME" -f sql/seed.sql

echo "Done. Run: pyfridge deck"
