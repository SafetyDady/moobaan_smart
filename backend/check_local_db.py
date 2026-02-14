import psycopg
try:
    conn = psycopg.connect('postgresql://postgres:postgres@localhost:5432/moobaan_smart')
    print('DB connected OK')
    cur = conn.cursor()
    cur.execute('SELECT version()')
    print(cur.fetchone()[0])
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    print(f'Tables: {len(tables)}')
    for t in tables:
        print(f'  - {t}')
    # Check alembic version
    cur.execute("SELECT version_num FROM alembic_version")
    versions = [r[0] for r in cur.fetchall()]
    print(f'Alembic version: {versions}')
    conn.close()
except Exception as e:
    print(f'Error: {e}')
