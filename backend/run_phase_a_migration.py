"""Run Phase A migration for Pay-in State Machine"""
from app.db.session import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        # Add new enum values
        try:
            conn.execute(text("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'DRAFT'"))
            conn.commit()
            print("Added DRAFT enum value")
        except Exception as e:
            print(f"DRAFT enum: {e}")
        
        try:
            conn.execute(text("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'SUBMITTED'"))
            conn.commit()
            print("Added SUBMITTED enum value")
        except Exception as e:
            print(f"SUBMITTED enum: {e}")
        
        try:
            conn.execute(text("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'REJECTED_NEEDS_FIX'"))
            conn.commit()
            print("Added REJECTED_NEEDS_FIX enum value")
        except Exception as e:
            print(f"REJECTED_NEEDS_FIX enum: {e}")
        
        # Create payinsource enum
        try:
            conn.execute(text("CREATE TYPE payinsource AS ENUM ('RESIDENT', 'ADMIN_CREATED', 'LINE_RECEIVED')"))
            conn.commit()
            print("Created payinsource enum")
        except Exception as e:
            print(f"payinsource enum: {e}")
        
        # Add columns one by one
        columns = [
            ("source", "payinsource DEFAULT 'RESIDENT'"),
            ("created_by_admin_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
            ("admin_note", "TEXT"),
            ("reference_bank_transaction_id", "UUID REFERENCES bank_transactions(id) ON DELETE SET NULL"),
            ("submitted_at", "TIMESTAMP WITH TIME ZONE"),
        ]
        
        for col_name, col_def in columns:
            try:
                conn.execute(text(f"ALTER TABLE payin_reports ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Column {col_name}: {e}")
        
        # Update existing records
        try:
            conn.execute(text("UPDATE payin_reports SET source = 'RESIDENT' WHERE source IS NULL"))
            conn.commit()
            print("Updated existing records with default source")
        except Exception as e:
            print(f"Update source: {e}")
        
        print("\nMigration completed!")

if __name__ == "__main__":
    run_migration()
