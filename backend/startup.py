#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Handles fresh database initialization and migrations.

CRITICAL: This script must NOT crash if DB is unavailable.
App must boot and respond to /health even without DB.
"""
import os
import sys

def init_database():
    """
    Initialize database - create tables if they don't exist.
    
    IMPORTANT: This is BEST EFFORT only.
    If DB is not ready, we log warning and continue.
    App will boot regardless.
    """
    print("🔧 Attempting database initialization (best effort)...")
    
    try:
        from app.db.session import engine, Base
        from sqlalchemy import inspect, text
        
        # Test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Import all models to register them with Base
        from app.db import models
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables or 'users' not in existing_tables:
            print("📦 Fresh database detected - creating all tables...")
            
            # Create ALL PostgreSQL ENUM types first (before tables)
            print("🔧 Creating ENUM types...")
            with engine.connect() as conn:
                # promotion_scope enum
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE promotion_scope AS ENUM ('project', 'village', 'house');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                # promotion_status enum
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE promotion_status AS ENUM ('active', 'expired', 'disabled');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                # credit_note_status enum
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE credit_note_status AS ENUM ('issued', 'applied');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                conn.commit()
            print("✅ ENUM types created!")
            
            Base.metadata.create_all(bind=engine)
            print("✅ Tables created successfully!")
            
            # Mark alembic as up-to-date (stamp to head)
            print("📌 Stamping alembic to head...")
            from alembic.config import Config
            from alembic import command
            
            alembic_cfg = Config("alembic.ini")
            command.stamp(alembic_cfg, "head")
            print("✅ Alembic stamped to head!")
        else:
            print(f"📋 Found {len(existing_tables)} existing tables")
            print("🔄 Running alembic upgrade...")
            
            from alembic.config import Config
            from alembic import command
            
            alembic_cfg = Config("alembic.ini")
            try:
                command.upgrade(alembic_cfg, "head")
                print("✅ Migrations completed!")
            except Exception as e:
                print(f"⚠️ Migration warning: {e}")
                print("Continuing with existing schema...")
                
    except Exception as e:
        # CRITICAL: Do NOT crash. Log and continue.
        print(f"⚠️ DATABASE INIT SKIPPED: {e}")
        print("⚠️ App will boot without DB initialization.")
        print("⚠️ DB operations may fail until database is ready.")
        # Do NOT raise - allow app to start


def run_production_seed():
    """Run production seed if enabled via ENV.
    Safety: only runs when RUN_PROD_SEED=true AND --seed flag is used,
    or when called from startup.py main block.
    Warns loudly if RUN_PROD_SEED is still set (should be removed after use).
    """
    import os
    run_seed = os.getenv("RUN_PROD_SEED", "").lower() == "true"
    if run_seed:
        print("⚠️" * 20)
        print("⚠️  WARNING: RUN_PROD_SEED is still set in environment!")
        print("⚠️  Remove it after initial setup to prevent accidental re-seeding.")
        print("⚠️" * 20)
    try:
        from prod_seed import run_production_seed as do_seed
        do_seed()
    except Exception as e:
        print(f"⚠️ Production seed skipped or failed: {e}")
        # Do NOT crash - seed is optional


if __name__ == "__main__":
    init_database()
    run_production_seed()
    print("🚀 Starting uvicorn...")
