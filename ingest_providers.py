import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "providers.db")
NPI_CSV_FILENAME = "npidata_pfile_20260601-20260607.csv"

def process_npi_file(npi_csv, db_path=DB_PATH):
    if not os.path.exists(npi_csv):
        print(f"[!] Targeted data file '{npi_csv}' not found. Please verify the filename and that it's in the 'data' directory.")
        return

    print(f"[*] Processing data stream from {npi_csv}...")
    
    # Target keywords we want to loosely capture out of the hundreds of columns
    target_keywords = [
        'NPI', 'Entity Type Code', 'Provider First Name', 'Provider Last Name (Legal Name)',
        'Provider Organization Name (Legal Business Name)', 'Provider Enumeration Date', 
        'Last Update Date', 'NPI Deactivation Reason Code',
        'Provider First Line Business Mailing Address', 'Provider Second Line Business Mailing Address',
        'Provider Business Mailing Address City Name', 'Provider Business Mailing Address State Name',
        'Provider Business Mailing Address Postal Code', 'Provider Business Mailing Address Telephone Number',
        'Provider Taxonomy Code_1'
    ]
    
    # Flexible matching function: permits reading regardless of spacing variations
    def col_matcher(col_name):
        return any(keyword.strip().lower() in col_name.strip().lower() for keyword in target_keywords)

    chunk_size = 5000
    conn = sqlite3.connect(db_path)
    
    try:
        # Use the column matcher function for reading chunks safely
        for chunk in pd.read_csv(npi_csv, usecols=col_matcher, chunksize=chunk_size, dtype=str):
            
            # Dynamically pull the exact taxonomy column name found in this chunk
            tax_col = [c for c in chunk.columns if 'taxonomy code_1' in c.lower()]
            tax_col_name = tax_col[0] if tax_col else None

            # --- 1. POPULATE PROVIDERS TABLE ---
            providers_df = chunk[[
                c for c in chunk.columns if any(k in c for k in ['NPI', 'Entity Type', 'First Name', 'Last Name', 'Organization Name', 'Enumeration Date', 'Last Update Date', 'Deactivation Reason'])
            ]].copy()
            
            # Lowercase for dependable mapping mutations
            providers_df.columns = [c.lower() for c in providers_df.columns]
            providers_df = providers_df.rename(columns={
                'npi': 'npi', 'entity type code': 'provider_type', 'provider first name': 'first_name',
                'provider last name (legal name)': 'last_name', 
                'provider organization name (legal business name)': 'organization_name',
                'provider enumeration date': 'enumeration_date', 'last update date': 'last_updated'
            })
            
            status_col = [c for c in providers_df.columns if 'deactivation' in c]
            if status_col:
                providers_df['status'] = providers_df[status_col[0]].apply(
                    lambda x: 'Inactive' if pd.notna(x) else 'Active'
                )
                providers_df = providers_df.drop(columns=[status_col[0]])
            else:
                providers_df['status'] = 'Active'

            # Keep only explicit schema elements
            providers_schema = ['npi', 'provider_type', 'first_name', 'last_name', 'organization_name', 'enumeration_date', 'last_updated', 'status']
            providers_df = providers_df[[c for c in providers_df.columns if c in providers_schema]]
            providers_df.to_sql('providers', conn, if_exists='append', index=False)
            
            # --- 2. POPULATE ADDRESSES TABLE ---
            address_df = chunk[[
                c for c in chunk.columns if any(k in c for k in ['NPI', 'First Line Business', 'Second Line Business', 'City Name', 'State Name', 'Postal Code', 'Telephone Number'])
            ]].copy()
            
            address_df.columns = [c.lower() for c in address_df.columns]
            address_df = address_df.rename(columns={
                'npi': 'npi',
                'provider first line business mailing address': 'address_line_1',
                'provider second line business mailing address': 'address_line_2',
                'provider business mailing address city name': 'city',
                'provider business mailing address state name': 'state',
                'provider business mailing address postal code': 'postal_code',
                'provider business mailing address telephone number': 'phone'
            })
            address_df['address_type'] = 'Mailing'
            
            address_schema = ['npi', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'phone', 'address_type']
            address_df = address_df[[c for c in address_df.columns if c in address_schema]]
            address_df.to_sql('addresses', conn, if_exists='append', index=False)
            
            # --- 3. POPULATE PROVIDER TAXONOMIES JOIN TABLE ---
            if tax_col_name:
                tax_df = chunk[['NPI', tax_col_name]].copy().dropna()
                tax_df.columns = ['npi', 'taxonomy_code']
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