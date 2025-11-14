#!/usr/bin/env python3
"""
View data from restored VikasAI database
"""

import subprocess
import sys

def run_sql_query(query, database='VikasAI'):
    """Run a SQL query and return output"""
    cmd = f"""docker exec sqlserver_restore /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -C -d {database} -Q "{query}" """
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def main():
    print("="*80)
    print("VIKASAI DATABASE - DATA VIEWER")
    print("="*80)
    
    # List all tables
    print("\n" + "-"*80)
    print("TABLES IN DATABASE:")
    print("-"*80)
    tables_query = """
    SELECT TABLE_SCHEMA, TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
    """
    output = run_sql_query(tables_query)
    print(output)
    
    # Get table names
    lines = output.strip().split('\n')
    tables = []
    for line in lines[2:-1]:  # Skip header and footer
        if '----' in line or not line.strip():
            continue
        parts = [p.strip() for p in line.split() if p.strip()]
        if len(parts) >= 2:
            schema = parts[0]
            table = parts[1]
            tables.append((schema, table))
    
    # Show sample data from each table
    print("\n" + "="*80)
    print("SAMPLE DATA FROM TABLES (First 5 rows):")
    print("="*80)
    
    for schema, table in tables[:20]:  # Limit to first 20 tables
        full_table = f"[{schema}].[{table}]" if schema else f"[{table}]"
        print(f"\n{'='*80}")
        print(f"TABLE: {full_table}")
        print('='*80)
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {full_table}"
        count_output = run_sql_query(count_query)
        print(f"Total Rows: {count_output.split()[-2] if len(count_output.split()) > 1 else 'N/A'}")
        
        # Get sample data
        sample_query = f"SELECT TOP 5 * FROM {full_table}"
        sample_output = run_sql_query(sample_query)
        print("\nSample Data:")
        print(sample_output)
        
        if len(tables) > 20 and tables.index((schema, table)) == 19:
            print(f"\n... and {len(tables) - 20} more tables (showing first 20)")
            break
    
    print("\n" + "="*80)
    print("To query specific tables, use:")
    print("  docker exec sqlserver_restore /opt/mssql-tools18/bin/sqlcmd")
    print("    -S localhost -U sa -P 'YourStrong@Passw0rd' -C -d VikasAI")
    print("    -Q \"SELECT * FROM [schema].[table]\"")
    print("="*80)

if __name__ == "__main__":
    main()

