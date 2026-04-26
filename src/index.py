import sqlite3
import os
import json
import pandas as pd
from pathlib import Path

class Indexer:
    def __init__(self,db_path,description_path,directory):
        self.db_path = db_path
        self.description_path = description_path
        self.directory = directory

    def create_index(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        tables = cursor.execute('SELECT name FROM sqlite_master WHERE type="table";').fetchall()
        table_details = {}
        df = pd.DataFrame()
        for t in tables:
            csv_path = Path(self.description_path) / f"{t[0]}.csv"
            if csv_path.exists():
                df = pd.concat([df, pd.read_csv(csv_path)], ignore_index=True)
        if not df.empty:
            df['original_column_name'] = df['original_column_name'].str.strip()

        def get_description(col):
            """Safely look up value_description, returning None if not found."""
            match = df[df['original_column_name'] == col]
            if not match.empty:
                val = match['value_description'].values[0]
                return None if pd.isna(val) else str(val)
            return None
        for t in tables:
            fk = cursor.execute(f'PRAGMA foreign_key_list({t[0]});').fetchall()
            formatted_fks = [
                f"{t[0]}.{fk[3]} → {fk[2]}.{fk[4]}"
                for fk in fk
            ]
            table_details[t[0]] = {
                        "row_count" : cursor.execute(f'SELECT COUNT(*) from "{t[0]}"').fetchone()[0],
                        "columns" : cursor.execute(f'PRAGMA table_info({t[0]});').fetchall(),
                        "foreign_keys" : formatted_fks
            }
            table_details[t[0]]['sample_values'] = {}
            for c in table_details[t[0]]['columns']:
                col_name = f'"{c[1]}"'
                tbl_name = f'"{t[0]}"'
                if c[5] == 1:
                    table_details[t[0]]['sample_values'][c[1]] = {'value_description': get_description(c[1])}
                    continue
                if c[2] in ('TEXT', 'DATE'):
                    
                    distinct_count = cursor.execute(f'SELECT COUNT(DISTINCT {col_name}) FROM {tbl_name};').fetchone()[0]
                    total_count = cursor.execute(f'SELECT COUNT(*) FROM {tbl_name};').fetchone()[0]
                    
                    if total_count > 0 and distinct_count / total_count < 0.9:
                        values = cursor.execute(f'SELECT DISTINCT {col_name} FROM {tbl_name} LIMIT 15;').fetchall()
                        sample_values= []
                        for row in values:
                            sample_values.append(row[0])
                        table_details[t[0]]['sample_values'][c[1]] = {'sample_values': sample_values, 'value_description': get_description(c[1])}
                        continue
                        

                if c[2] in ('INTEGER','REAL'):
                    
                    MIN = cursor.execute(f'SELECT MIN({col_name}) FROM {tbl_name};').fetchone()[0]
                    MAX = cursor.execute(f'SELECT MAX({col_name}) FROM {tbl_name};').fetchone()[0]
                    AVG = cursor.execute(f'SELECT AVG({col_name}) FROM {tbl_name};').fetchone()[0]
                    table_details[t[0]]['sample_values'][c[1]] = {'sample_values': {'min': MIN, 'max': MAX, 'avg': AVG}, 'value_description': get_description(c[1])}

        conn.close()

        

        
        os.makedirs(self.directory,exist_ok=True)
        path = os.path.join(self.directory,'index.json')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(table_details, indent=4, ensure_ascii=False))
        
    

# Indexer("data/california_schools/california_schools.sqlite").create_index("index")


        