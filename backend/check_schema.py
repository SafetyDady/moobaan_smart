#!/usr/bin/env python
"""Check current database schema state"""
import psycopg

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5432/moobaan_smart")
cursor = conn.cursor()

# Check tables
cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")
tables = [r[0] for r in cursor.fetchall()]
print("All tables:")
for t in tables:
    if 'resident' in t or 'export' in t or 'user' in t or 'alembic' in t:
        print(f"  * {t}")
    else:
        print(f"    {t}")

# Check users columns
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'users'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cursor.fetchall()]
print(f"\nUsers table columns: {cols}")
print(f"  Has 'username'? {'username' in cols}")

# Check alembic versions
cursor.execute("SELECT version_num FROM alembic_version")
versions = [r[0] for r in cursor.fetchall()]
print(f"\nAlembic versions in DB: {versions}")

conn.close()
