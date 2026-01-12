#!/bin/bash
# Quick setup script for local PostgreSQL database

# Create the database (assuming PostgreSQL is installed locally)
# You can also use pgAdmin or any PostgreSQL client

echo "Creating moobaan_smart database..."

# Option 1: If you have psql command line tool
# createdb moobaan_smart

# Option 2: Connect to existing PostgreSQL and run CREATE DATABASE
# psql -c "CREATE DATABASE moobaan_smart;"

echo "If you have PostgreSQL installed locally:"
echo "1. Run: createdb moobaan_smart"
echo "2. Or connect to PostgreSQL and run: CREATE DATABASE moobaan_smart;"
echo ""
echo "If you don't have PostgreSQL installed:"
echo "1. Install PostgreSQL 16"
echo "2. Or start Docker Desktop and run: docker-compose -f docker/docker-compose.yml up db -d"