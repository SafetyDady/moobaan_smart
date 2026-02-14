"""
Diagnostic script to check timezone values in the database.
Run against local or production DB by setting DATABASE_URL.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import psycopg

db_url = os.environ.get("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
print(f"Connecting to: {db_url[:50]}...")

conn = psycopg.connect(db_url)
cur = conn.cursor()

# 1. Check session timezone
cur.execute("SHOW timezone")
tz = cur.fetchone()[0]
print(f"\n{'='*60}")
print(f"1. PostgreSQL session timezone: {tz}")
print(f"{'='*60}")

# 2. Check pay-in records for house 28/73
print(f"\n{'='*60}")
print(f"2. Pay-in records (house 28/73, amount=600)")
print(f"{'='*60}")
cur.execute("""
    SELECT p.id, p.transfer_date, p.transfer_hour, p.transfer_minute, 
           p.amount, p.status, h.house_code,
           p.transfer_date AT TIME ZONE 'UTC' as utc_time,
           p.transfer_date AT TIME ZONE 'Asia/Bangkok' as bkk_time
    FROM payin_reports p 
    JOIN houses h ON p.house_id = h.id
    WHERE h.house_code = '28/73' AND p.amount = 600
    ORDER BY p.id
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  PayIn #{r[0]}: transfer_date={r[1]}, hour={r[2]}, min={r[3]}, "
              f"amount={r[4]}, status={r[5]}, house={r[6]}")
        print(f"    → UTC: {r[7]}")
        print(f"    → BKK: {r[8]}")
        # Compute transfer_datetime as the matching code does
        if r[1] and r[2] is not None and r[3] is not None:
            computed = r[1].replace(hour=r[2], minute=r[3], second=0, microsecond=0)
            print(f"    → Computed transfer_datetime: {computed} (tzinfo={computed.tzinfo})")
else:
    print("  No records found for house 28/73 with amount 600")

# 2b. Check ALL payins
print(f"\n{'='*60}")
print(f"2b. ALL Pay-in records")
print(f"{'='*60}")
cur.execute("""
    SELECT p.id, p.transfer_date, p.transfer_hour, p.transfer_minute, 
           p.amount, p.status, h.house_code
    FROM payin_reports p 
    JOIN houses h ON p.house_id = h.id
    ORDER BY p.id
""")
rows = cur.fetchall()
for r in rows:
    print(f"  PayIn #{r[0]}: house={r[6]}, transfer_date={r[1]}, h={r[2]},m={r[3]}, "
          f"amt={r[4]}, status={r[5]}")

# 3. Check bank transactions with amount=600 around Jan 30
print(f"\n{'='*60}")
print(f"3. Bank transactions (credit=600, around Jan 30)")
print(f"{'='*60}")
cur.execute("""
    SELECT id, effective_at, credit, description, channel, matched_payin_id, posting_status,
           effective_at AT TIME ZONE 'UTC' as utc_time,
           effective_at AT TIME ZONE 'Asia/Bangkok' as bkk_time
    FROM bank_transactions 
    WHERE credit = 600 
    ORDER BY effective_at
""")
rows = cur.fetchall()
for r in rows:
    print(f"  BankTxn {str(r[0])[:8]}...: effective_at={r[1]}, credit={r[2]}, "
          f"matched={r[5]}, posting={r[6]}")
    print(f"    → UTC: {r[7]}")
    print(f"    → BKK: {r[8]}")
    print(f"    → desc: {r[3]}")

# 4. Direct comparison for 28/73 pay-in vs bank txns
print(f"\n{'='*60}")
print(f"4. MATCHING SIMULATION")
print(f"{'='*60}")
cur.execute("""
    SELECT p.id as payin_id, 
           p.transfer_date, p.transfer_hour, p.transfer_minute,
           bt.id as bank_txn_id, bt.effective_at,
           EXTRACT(EPOCH FROM (
               (p.transfer_date + (p.transfer_hour || ' hours')::interval + (p.transfer_minute || ' minutes')::interval)
               - bt.effective_at
           )) as diff_seconds,
           bt.matched_payin_id
    FROM payin_reports p
    JOIN houses h ON p.house_id = h.id
    CROSS JOIN bank_transactions bt
    WHERE h.house_code = '28/73' 
    AND p.amount = 600 
    AND bt.credit = 600
    ORDER BY ABS(EXTRACT(EPOCH FROM (
        (p.transfer_date + (p.transfer_hour || ' hours')::interval + (p.transfer_minute || ' minutes')::interval) 
        - bt.effective_at
    )))
    LIMIT 10
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        diff_secs = float(r[6]) if r[6] else 0
        diff_hrs = diff_secs / 3600
        match_ok = abs(diff_secs) <= 60
        already_matched = r[7] is not None
        print(f"  PayIn #{r[0]} vs BankTxn {str(r[4])[:8]}...")
        print(f"    PayIn time:  {r[1]} (h={r[2]}, m={r[3]})")
        print(f"    Bank time:   {r[5]}")
        print(f"    Diff: {diff_secs:.0f}s ({diff_hrs:.1f}h)")
        print(f"    Within ±60s? {'✅ YES' if match_ok else '❌ NO'}")
        print(f"    Already matched? {'⚠️ YES' if already_matched else '✅ NO (available)'}")
else:
    print("  No cross-join results found")

conn.close()
print(f"\n{'='*60}")
print("Done!")
