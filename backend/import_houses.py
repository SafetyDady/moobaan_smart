#!/usr/bin/env python3
"""
Import Houses from HomeList.xlsx into Production DB via API

Usage:
  1. Against Railway production:
     python import_houses.py --api https://moobaansmart-production.up.railway.app

  2. Against local development:
     python import_houses.py --api http://localhost:8000

  3. Dry-run (preview only, no changes):
     python import_houses.py --api https://moobaansmart-production.up.railway.app --dry-run

Admin credentials: Uses admin@moobaan.com / Admin123! by default
Override with --email and --password flags.
"""
import argparse
import sys
import json
import re
import requests
import openpyxl

# ─── Configuration ───────────────────────────────────────────────
EXCEL_FILE = r"C:\Users\sanch\OneDrive\MakMaiLeelawadee\HomeList.xlsx"
SHEET_NAME = "HomeList"

DEFAULT_EMAIL = "admin@moobaan.com"
DEFAULT_PASSWORD = "Admin123!"

# Owners marked as "ไม่พบรายชื่อผู้อยู่อาศัย" will get this status
VACANT_MARKER = "ไม่พบรายชื่อผู้อยู่อาศัย"
VACANT_STATUS = "VACANT"
ACTIVE_STATUS = "ACTIVE"


def load_excel(filepath: str, sheet_name: str) -> list[dict]:
    """Load house data from Excel file."""
    import shutil, tempfile, os

    # Copy file to temp to avoid OneDrive lock
    temp_path = os.path.join(tempfile.gettempdir(), "HomeList_import.xlsx")
    shutil.copy2(filepath, temp_path)

    wb = openpyxl.load_workbook(temp_path, data_only=True)
    ws = wb[sheet_name]

    houses = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        home_id = str(row[0]).strip() if row[0] else ""
        owner = str(row[1]).strip() if row[1] else ""

        # Clean non-breaking spaces
        owner = owner.replace("\xa0", " ").strip()

        if not home_id:
            continue

        # Validate house_code format
        if not re.match(r'^28/\d+$', home_id):
            print(f"  ⚠️  Row {row_idx}: Invalid house_code '{home_id}' — skipped")
            continue

        # Determine status
        if owner == VACANT_MARKER or not owner:
            status = VACANT_STATUS
            owner_name = "(ว่าง)"
        else:
            status = ACTIVE_STATUS
            owner_name = owner

        houses.append({
            "house_code": home_id,
            "owner_name": owner_name,
            "house_status": status,
        })

    os.remove(temp_path)
    print(f"📄 Loaded {len(houses)} houses from Excel")
    return houses


def login(session: requests.Session, api_base: str, email: str, password: str) -> bool:
    """Login to get auth cookie."""
    url = f"{api_base}/api/auth/login"
    resp = session.post(url, json={"email": email, "password": password})

    if resp.status_code == 200:
        print(f"✅ Login successful as {email}")
        return True
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return False


def get_existing_houses(session: requests.Session, api_base: str) -> dict:
    """Fetch existing houses and return a dict keyed by house_code."""
    url = f"{api_base}/api/houses"
    resp = session.get(url)

    if resp.status_code != 200:
        print(f"⚠️  Cannot fetch existing houses: {resp.status_code}")
        return {}

    houses = resp.json()
    return {h["house_code"]: h for h in houses}


def import_houses(
    session: requests.Session,
    api_base: str,
    houses: list[dict],
    existing: dict,
    dry_run: bool = False,
) -> dict:
    """Import houses via API. Returns summary stats."""
    stats = {
        "total": len(houses),
        "created": 0,
        "skipped_exists": 0,
        "updated": 0,
        "errors": 0,
        "error_details": [],
    }

    for i, house in enumerate(houses, 1):
        code = house["house_code"]
        prefix = f"  [{i:3d}/{len(houses)}] {code:8s}"

        if code in existing:
            ex = existing[code]
            # Check if owner_name needs update
            if ex["owner_name"] != house["owner_name"]:
                if dry_run:
                    print(f"{prefix} 🔄 WOULD UPDATE owner: '{ex['owner_name']}' → '{house['owner_name']}'")
                    stats["updated"] += 1
                else:
                    # Update existing house
                    url = f"{api_base}/api/houses/{ex['id']}"
                    resp = session.put(url, json={
                        "owner_name": house["owner_name"],
                        "house_status": house["house_status"],
                    })
                    if resp.status_code == 200:
                        print(f"{prefix} 🔄 Updated owner: '{ex['owner_name']}' → '{house['owner_name']}'")
                        stats["updated"] += 1
                    else:
                        print(f"{prefix} ❌ Update failed: {resp.status_code}")
                        stats["errors"] += 1
                        stats["error_details"].append(f"{code}: update failed {resp.status_code}")
            else:
                print(f"{prefix} ⏭️  Already exists (same owner)")
                stats["skipped_exists"] += 1
            continue

        # Create new house
        if dry_run:
            status_icon = "🏠" if house["house_status"] == ACTIVE_STATUS else "🚫"
            print(f"{prefix} {status_icon} WOULD CREATE: {house['owner_name']} [{house['house_status']}]")
            stats["created"] += 1
        else:
            url = f"{api_base}/api/houses"
            resp = session.post(url, json=house)

            if resp.status_code == 200:
                status_icon = "🏠" if house["house_status"] == ACTIVE_STATUS else "🚫"
                print(f"{prefix} {status_icon} Created: {house['owner_name']} [{house['house_status']}]")
                stats["created"] += 1
            elif resp.status_code == 400 and "already exists" in resp.text:
                print(f"{prefix} ⏭️  Already exists (race condition)")
                stats["skipped_exists"] += 1
            else:
                print(f"{prefix} ❌ Failed: {resp.status_code} {resp.text[:100]}")
                stats["errors"] += 1
                stats["error_details"].append(f"{code}: {resp.status_code} {resp.text[:80]}")

    return stats


def print_summary(stats: dict, dry_run: bool):
    """Print import summary."""
    mode = "DRY-RUN" if dry_run else "IMPORT"
    print()
    print("=" * 60)
    print(f"📊 {mode} SUMMARY")
    print("=" * 60)
    print(f"  Total houses in Excel : {stats['total']}")
    print(f"  ✅ Created            : {stats['created']}")
    print(f"  🔄 Updated            : {stats['updated']}")
    print(f"  ⏭️  Skipped (exists)   : {stats['skipped_exists']}")
    print(f"  ❌ Errors             : {stats['errors']}")

    if stats["error_details"]:
        print()
        print("  Error details:")
        for err in stats["error_details"]:
            print(f"    - {err}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Import houses from HomeList.xlsx")
    parser.add_argument("--api", required=True, help="API base URL (e.g., https://moobaansmart-production.up.railway.app)")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help="Admin email for login")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Admin password for login")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no changes made")
    parser.add_argument("--excel", default=EXCEL_FILE, help="Path to Excel file")

    args = parser.parse_args()

    print()
    print("🏘️  MooBaan Smart — House Import Tool")
    print("=" * 60)
    print(f"  API Target : {args.api}")
    print(f"  Excel File : {args.excel}")
    print(f"  Mode       : {'DRY-RUN (preview only)' if args.dry_run else '⚡ LIVE IMPORT'}")
    print("=" * 60)
    print()

    # Step 1: Load Excel
    houses = load_excel(args.excel, SHEET_NAME)
    if not houses:
        print("❌ No houses found in Excel file!")
        sys.exit(1)

    # Quick stats
    active_count = sum(1 for h in houses if h["house_status"] == ACTIVE_STATUS)
    vacant_count = sum(1 for h in houses if h["house_status"] == VACANT_STATUS)
    print(f"  📈 Active: {active_count}, Vacant: {vacant_count}")
    print()

    # Step 2: Login
    session = requests.Session()
    if not login(session, args.api, args.email, args.password):
        print("❌ Cannot proceed without login!")
        sys.exit(1)
    print()

    # Step 3: Get existing houses
    print("📋 Fetching existing houses from database...")
    existing = get_existing_houses(session, args.api)
    print(f"  Found {len(existing)} existing houses in DB")
    print()

    # Step 4: Import
    print("🚀 Starting import...")
    print("-" * 60)
    stats = import_houses(session, args.api, houses, existing, dry_run=args.dry_run)

    # Step 5: Summary
    print_summary(stats, args.dry_run)

    if args.dry_run:
        print()
        print("💡 This was a DRY-RUN. To actually import, run without --dry-run flag.")


if __name__ == "__main__":
    main()
