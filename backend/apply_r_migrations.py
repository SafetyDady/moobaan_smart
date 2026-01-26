#!/usr/bin/env python
"""Apply missing R.2 and R.3 migrations manually"""
import psycopg

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5432/moobaan_smart")
cursor = conn.cursor()

# --- R.2: Add username column and modify users table ---
print("Applying R.2 migration...")

# Make email nullable (might already be)
cursor.execute("""
    ALTER TABLE users ALTER COLUMN email DROP NOT NULL
""")

# Make hashed_password nullable (might already be)
cursor.execute("""
    ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL
""")

# Add username column if not exists
cursor.execute("""
    ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100)
""")

# Create unique index on phone (if not exists)
try:
    cursor.execute("""
        CREATE UNIQUE INDEX ix_users_phone_unique 
        ON users (phone) 
        WHERE phone IS NOT NULL
    """)
except Exception as e:
    if "already exists" in str(e):
        print("  Phone index already exists, skipping")
    else:
        raise

# Populate username for existing users
cursor.execute("""
    UPDATE users 
    SET username = COALESCE(full_name, email)
    WHERE username IS NULL
""")

print("  R.2 applied successfully")

# --- R.3: Create resident_house_audit_logs table ---
print("Applying R.3 migration...")

# Check if table exists
cursor.execute("""
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'resident_house_audit_logs'
    )
""")
if cursor.fetchone()[0]:
    print("  Table already exists, skipping")
else:
    cursor.execute("""
        CREATE TABLE resident_house_audit_logs (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            house_id INTEGER REFERENCES houses(id),
            from_house_id INTEGER REFERENCES houses(id),
            to_house_id INTEGER REFERENCES houses(id),
            house_code VARCHAR(50),
            from_house_code VARCHAR(50),
            to_house_code VARCHAR(50),
            ip_address VARCHAR(50),
            user_agent VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    cursor.execute("CREATE INDEX ix_resident_house_audit_logs_user_id ON resident_house_audit_logs (user_id)")
    cursor.execute("CREATE INDEX ix_resident_house_audit_logs_event_type ON resident_house_audit_logs (event_type)")
    cursor.execute("CREATE INDEX ix_resident_house_audit_logs_created_at ON resident_house_audit_logs (created_at)")
    print("  R.3 table created successfully")

# --- Update alembic version to include R.3 ---
print("Updating alembic_version...")
cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('r3_resident_house_audit')")

conn.commit()
print("\nAll migrations applied and committed!")
conn.close()
