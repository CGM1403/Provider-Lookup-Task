import pandas as pd
import sqlite3
import os

def ingest_taxonomy_mapping(csv_path, db_path="providers.db"):
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
    ingest_taxonomy_mapping("nucc_taxonomy.csv")