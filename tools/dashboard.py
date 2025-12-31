import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.storage.db import get_db

def show():
    conn = get_db()
    cur = conn.cursor()

    print("\nORDERS")
    for row in cur.execute("SELECT * FROM orders"):
        print(row)

    print("\nPAYMENTS")
    for row in cur.execute("SELECT * FROM payments"):
        print(row)

    print("\nSTOCK")
    for row in cur.execute("SELECT * FROM stock"):
        print(row)

    conn.close()

if __name__ == "__main__":
    show()