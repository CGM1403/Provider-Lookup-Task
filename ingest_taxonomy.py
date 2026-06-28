import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "providers.db")
TAXONOMY_CSV_FILENAME = "nucc_taxonomy.csv"

def ingest_taxonomy_mapping(csv_path, db_path=DB_PATH):
    if not os.path.exists(csv_path):
        print(f"[!] Target taxonomy file '{csv_path}' not found. Please verify placement.")
        return

    print(f"[*] Extracting metadata mappings from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Map raw headers to database schemas
    df_cleaned = df[['Code', 'Grouping', 'Classification', 'Specialization']].rename(
        columns={
            'Code': 'code',
            'Grouping': 'grouping',
            'Classification': 'classification',
            'Specialization': 'specialization'
        }
    )
    
    conn = sqlite3.connect(db_path)
    df_cleaned.to_sql('taxonomies', conn, if_exists='append', index=False)
    conn.close()
    print("[+] Taxonomy table hydration finalized.")

if __name__ == "__main__":
    # Ensure you drop your nucc cross-reference csv naming here
    taxonomy_csv_path = os.path.join(DATA_DIR, TAXONOMY_CSV_FILENAME)
    ingest_taxonomy_mapping(taxonomy_csv_path)