#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Handles fresh database initialization and migrations.
"""
import os
import sys

def init_database():
    """Initialize database - create tables if they don't exist."""
    print("🔧 Checking database...")
    
    from app.db.session import engine, Base
    from sqlalchemy import inspect, text
    
    # Import all models to register them with Base
    # This imports everything from app/db/models/__init__.py
    from app.db import models
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables or 'users' not in existing_tables:
        print("📦 Fresh database detected - creating all tables...")
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

if __name__ == "__main__":
    init_database()
    print("🚀 Starting uvicorn...")
