#!/usr/bin/env python3
"""
Production Seed Script for Railway

PURPOSE:
- Create initial super_admin user for first-time setup
- Optionally create a sample house
- Safe for production (idempotent, ENV-controlled)

SECURITY:
- Controlled by RUN_PROD_SEED=true environment variable
- Admin credentials from environment (not hardcoded)
- Runs once only - skips if admin already exists
- Never creates residents (admin creates them via UI)

USAGE (Railway):
1. Set environment variables:
   - RUN_PROD_SEED=true
   - PROD_ADMIN_EMAIL=admin@yourcompany.com
   - PROD_ADMIN_PASSWORD=YourSecurePassword123!
   - PROD_ADMIN_NAME=System Administrator (optional)
   - PROD_CREATE_SAMPLE_HOUSE=true (optional)

2. Deploy - seed runs automatically on startup
3. Remove RUN_PROD_SEED after successful seed
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def should_run_seed() -> bool:
    """Check if seed should run based on ENV"""
    return os.getenv("RUN_PROD_SEED", "").lower() == "true"


def run_production_seed():
    """
    Run production seed - creates super_admin and optionally a house.
    
    Returns:
        bool: True if seed ran successfully or was skipped safely
    """
    if not should_run_seed():
        logger.info("⏭️  RUN_PROD_SEED not set - skipping seed")
        return True
    
    logger.info("=" * 60)
    logger.info("🌱 PRODUCTION SEED STARTING")
    logger.info("=" * 60)
    
    # Get credentials from ENV (required)
    admin_email = os.getenv("PROD_ADMIN_EMAIL")
    admin_password = os.getenv("PROD_ADMIN_PASSWORD")
    admin_name = os.getenv("PROD_ADMIN_NAME", "System Administrator")
    admin_phone = os.getenv("PROD_ADMIN_PHONE", "0800000000")
    create_house = os.getenv("PROD_CREATE_SAMPLE_HOUSE", "").lower() == "true"
    
    # Validate required ENV
    if not admin_email or not admin_password:
        logger.error("❌ PROD_ADMIN_EMAIL and PROD_ADMIN_PASSWORD are required!")
        logger.error("   Set these environment variables and redeploy.")
        return False
    
    if len(admin_password) < 8:
        logger.error("❌ PROD_ADMIN_PASSWORD must be at least 8 characters!")
        return False
    
    try:
        # Import here to avoid circular imports and allow DB to initialize first
        from sqlalchemy.orm import Session
        from sqlalchemy import text
        from app.db.session import engine
        from app.db.models.user import User
        from app.db.models.house import House
        from app.core.auth import get_password_hash
        
        with Session(engine) as db:
            # Check if super_admin already exists
            existing_admin = db.query(User).filter(
                (User.email == admin_email) | (User.role == "super_admin")
            ).first()
            
            if existing_admin:
                logger.info(f"✅ Admin already exists: {existing_admin.email}")
                logger.info("⏭️  Skipping seed (idempotent)")
                return True
            
            # Create super_admin
            logger.info(f"📝 Creating super_admin: {admin_email}")
            
            admin_user = User(
                email=admin_email,
                phone=admin_phone,
                full_name=admin_name,
                hashed_password=get_password_hash(admin_password),
                role="super_admin",
                is_active=True
            )
            db.add(admin_user)
            db.flush()  # Get the ID
            
            logger.info(f"✅ Super Admin created: ID={admin_user.id}, Email={admin_email}")
            
            # Optionally create sample house
            if create_house:
                existing_house = db.query(House).first()
                if existing_house:
                    logger.info(f"✅ House already exists: {existing_house.house_number}")
                else:
                    logger.info("🏠 Creating sample house...")
                    sample_house = House(
                        house_number="A-001",
                        address="1 Sample Street",
                        village_name="Smart Village",
                        is_active=True
                    )
                    db.add(sample_house)
                    db.flush()
                    logger.info(f"✅ Sample house created: ID={sample_house.id}")
            
            db.commit()
            
            logger.info("=" * 60)
            logger.info("🎉 PRODUCTION SEED COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("")
            logger.info("⚠️  IMPORTANT: Remove RUN_PROD_SEED from environment variables!")
            logger.info("⚠️  This prevents accidental re-seeding on future deploys.")
            logger.info("")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ SEED FAILED: {e}")
        logger.exception("Full traceback:")
        return False


if __name__ == "__main__":
    # Allow running directly for testing
    success = run_production_seed()
    sys.exit(0 if success else 1)
