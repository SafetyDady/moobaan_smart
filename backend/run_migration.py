#!/usr/bin/env python3
"""Run Alembic migrations"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command

# Create Alembic configuration
alembic_cfg = Config("alembic.ini")

# Run upgrade to head
print("Running database migrations...")
command.upgrade(alembic_cfg, "head")
print("✅ Migrations completed successfully!")
