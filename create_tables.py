import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "providers.db")

def init_database(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    print(f"[*] Initializing database structure at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Providers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        npi TEXT PRIMARY KEY,
        provider_type INTEGER,
        first_name TEXT,
        last_name TEXT,
        organization_name TEXT,
        enumeration_date TEXT,
        last_updated TEXT,
        status TEXT
    );
    """)
    
    # 2. Addresses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npi TEXT,
        address_type TEXT,
        address_line_1 TEXT,
        address_line_2 TEXT,
        city TEXT,
        state TEXT,
        postal_code TEXT,
        phone TEXT,
        FOREIGN KEY (npi) REFERENCES providers(npi)
    );
    """)
    
    # 3. Taxonomies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS taxonomies (
        code TEXT PRIMARY KEY,
        grouping TEXT,
        classification TEXT,
        specialization TEXT
    );
    """)

    # 4. Provider Taxonomies (Junction Table)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS provider_taxonomies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npi TEXT,
        taxonomy_code TEXT,
        is_primary INTEGER,
        FOREIGN KEY (npi) REFERENCES providers(npi),
        FOREIGN KEY (taxonomy_code) REFERENCES taxonomies(code)
    );
    """)
    
    conn.commit()
    conn.close()
    print("[+] Database tables engineered and verified successfully.")

if __name__ == "__main__":
    init_database()