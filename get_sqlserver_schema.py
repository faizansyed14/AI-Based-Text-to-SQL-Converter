#!/usr/bin/env python3
"""
Get schema from SQL Server and format it for PostgreSQL/application use
"""

import subprocess
import json

def get_schema():
    """Get schema from SQL Server VikasAI database"""
    
    # Get all tables
    cmd = """docker exec sqlserver_restore /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -C -d VikasAI -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME" -h -1 -W"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    tables = []
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if line and 'TABLE_NAME' not in line and '---' not in line:
            tables.append(line)
    
    schema_info = {}
    
    for table in tables:
        # Get columns for each table
        cmd = f"""docker exec sqlserver_restore /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -C -d VikasAI -Q "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' ORDER BY ORDINAL_POSITION" -h -1 -W"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        columns = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if line and 'COLUMN_NAME' not in line and '---' not in line:
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) >= 2:
                    col_name = parts[0]
                    data_type = parts[1]
                    nullable = parts[2] if len(parts) > 2 else 'YES'
                    max_length = parts[3] if len(parts) > 3 else None
                    
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "nullable": nullable == 'YES',
                        "max_length": max_length
                    })
        
        if columns:
            schema_info[table] = columns
    
    return schema_info

if __name__ == "__main__":
    schema = get_schema()
    print(json.dumps(schema, indent=2))

