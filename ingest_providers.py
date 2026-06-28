import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "providers.db")
NPI_CSV_FILENAME = "npidata_pfile_20260601-20260607.csv"

def process_npi_file(npi_csv, db_path=DB_PATH):
    if not os.path.exists(npi_csv):
        print(f"[!] Targeted data file '{npi_csv}' not found.")
        return

    print(f"[*] Processing data stream from {npi_csv}...")
    
    # Isolate strictly mandatory indices to stay light on resources
    columns_to_load = [
        'NPI', 'Entity Type Code', 'Provider First Name', 'Provider Last Name (Legal Name)',
        'Provider Organization Name (Legal Business Name)', 'Provider Enumeration Date', 
        'Last Update Date', 'NPI Deactivation Reason Code',
        'Provider First Line Business Mailing Address', 'Provider Second Line Business Mailing Address',
        'Provider Business Mailing Address City Name', 'Provider Business Mailing Address State Name',
        'Provider Business Mailing Address Postal Code', 'Provider Business Mailing Address Telephone Number',
        'Provider License Number State Code_1', 'Provider Taxonomy Code_1'
    ]
    
    chunk_size = 5000
    conn = sqlite3.connect(db_path)
    
    try:
        for chunk in pd.read_csv(npi_csv, usecols=columns_to_load, chunksize=chunk_size, dtype=str):
            
            # --- 1. POPULATE PROVIDERS TABLE ---
            providers_df = chunk[[
                'NPI', 'Entity Type Code', 'Provider First Name', 
                'Provider Last Name (Legal Name)', 'Provider Organization Name (Legal Business Name)',
                'Provider Enumeration Date', 'Last Update Date', 'NPI Deactivation Reason Code'
            ]].copy()
            
            providers_df = providers_df.rename(columns={
                'NPI': 'npi', 'Entity Type Code': 'provider_type', 'Provider First Name': 'first_name',
                'Provider Last Name (Legal Name)': 'last_name', 
                'Provider Organization Name (Legal Business Name)': 'organization_name',
                'Provider Enumeration Date': 'enumeration_date', 'Last Update Date': 'last_updated'
            })
            
            providers_df['status'] = providers_df['NPI Deactivation Reason Code'].apply(
                lambda x: 'Inactive' if pd.notna(x) else 'Active'
            )
            providers_df = providers_df.drop(columns=['NPI Deactivation Reason Code'])
            providers_df.to_sql('providers', conn, if_exists='append', index=False)
            
            # --- 2. POPULATE ADDRESSES TABLE ---
            address_df = chunk[[
                'NPI', 'Provider First Line Business Mailing Address', 'Provider Second Line Business Mailing Address',
                'Provider Business Mailing Address City Name', 'Provider Business Mailing Address State Name',
                'Provider Business Mailing Address Postal Code', 'Provider Business Mailing Address Telephone Number'
            ]].copy()
            
            address_df = address_df.rename(columns={
                'NPI': 'npi',
                'Provider First Line Business Mailing Address': 'address_line_1',
                'Provider Second Line Business Mailing Address': 'address_line_2',
                'Provider Business Mailing Address City Name': 'city',
                'Provider Business Mailing Address State Name': 'state',
                'Provider Business Mailing Address Postal Code': 'postal_code',
                'Provider Business Mailing Address Telephone Number': 'phone'
            })
            address_df['address_type'] = 'Mailing'
            address_df.to_sql('addresses', conn, if_exists='append', index=False)
            
            # --- 3. POPULATE PROVIDER TAXONOMIES JOIN TABLE ---
            tax_df = chunk[['NPI', 'Provider Taxonomy Code_1']].copy().dropna()
            tax_df = tax_df.rename(columns={'NPI': 'npi', 'Provider Taxonomy Code_1': 'taxonomy_code'})
            tax_df['is_primary'] = 1
            tax_df.to_sql('provider_taxonomies', conn, if_exists='append', index=False)
            
            print(f"[+] Loaded transaction chunk sequence containing {len(chunk)} providers.")
            
    except Exception as e:
        print(f"[!] Processing exception triggered: {e}")
    finally:
        conn.close()
        print("[*] Stream complete. Database finalized.")

if __name__ == "__main__":
    npi_csv_path = os.path.join(DATA_DIR, NPI_CSV_FILENAME)
    process_npi_file(npi_csv_path)