import sqlite3
import os

def check_db(db_path):
    print("Checking", db_path)
    if not os.path.exists(db_path):
        print("File does not exist")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        tables = [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("  Tables:", tables)
        for t in tables:
            cnt = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"    Table {t}: {cnt} rows")
            if t == 'product_performance' and cnt > 0:
                print("    Sample product_ids:", cursor.execute("SELECT DISTINCT product_id FROM product_performance").fetchall())
    except Exception as e:
        print("  Error:", str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    check_db("data/historical_repository.db")
    check_db("data/test_historical_repository.db")
