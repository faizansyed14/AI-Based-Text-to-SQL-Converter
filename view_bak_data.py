#!/usr/bin/env python3
"""
Script to restore .bak file and view its data
"""

import subprocess
import sys
import time
from pathlib import Path

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        # Check if Docker daemon is running
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def restore_backup():
    """Restore the backup file"""
    backup_file = "VikasAI.Bak"
    
    if not Path(backup_file).exists():
        print(f"Error: {backup_file} not found")
        return False
    
    print("="*60)
    print("Step 1: Restoring .bak file to SQL Server")
    print("="*60)
    
    restore_tool_path = Path(__file__).parent / 'files' / 'sql_restore_tool.py'
    if not restore_tool_path.exists():
        print(f"Error: sql_restore_tool.py not found")
        return False
    
    # Run restore tool non-interactively
    print("\nStarting SQL Server and restoring backup...")
    print("This may take a few minutes...\n")
    
    # We'll need to run this interactively or create an automated version
    print("Please run the restore tool manually:")
    print(f"  python files/sql_restore_tool.py {backup_file}")
    print("\nOr use the automated restore below...\n")
    
    return True

def view_database_data():
    """View data from restored database"""
    print("\n" + "="*60)
    print("Step 2: Viewing Database Data")
    print("="*60)
    
    try:
        import pymssql
    except ImportError:
        print("\nInstalling pymssql...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pymssql'], check=True)
        import pymssql
    
    # Connection details
    server = 'localhost'
    user = 'sa'
    password = 'YourStrong@Passw0rd'
    database = 'VikasAI'  # Try common names
    
    print(f"\nConnecting to SQL Server...")
    print(f"  Server: {server}")
    print(f"  Database: {database}")
    
    try:
        conn = pymssql.connect(server=server, user=user, password=password, database=database)
        cursor = conn.cursor()
        
        # List all tables
        print("\n" + "-"*60)
        print("Tables in database:")
        print("-"*60)
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        if not tables:
            print("No tables found. Trying to list all databases...")
            cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
            databases = cursor.fetchall()
            print("\nAvailable databases:")
            for db in databases:
                print(f"  - {db[0]}")
            conn.close()
            return
        
        for schema, table in tables:
            print(f"  {schema}.{table}")
        
        # Show data from first few tables
        print("\n" + "-"*60)
        print("Sample Data (first 5 rows from each table):")
        print("-"*60)
        
        for schema, table in tables[:5]:  # Limit to first 5 tables
            full_table_name = f"{schema}.{table}" if schema else table
            try:
                cursor.execute(f"SELECT TOP 5 * FROM [{schema}].[{table}]")
                rows = cursor.fetchall()
                
                if rows:
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    print(f"\n{table}:")
                    print(f"  Columns: {', '.join(columns)}")
                    print(f"  Rows: {len(rows)}")
                    for i, row in enumerate(rows, 1):
                        print(f"    Row {i}: {row}")
            except Exception as e:
                print(f"\n{table}: Error reading data - {e}")
        
        conn.close()
        print("\n" + "="*60)
        print("Data viewing complete!")
        print("="*60)
        
    except pymssql.Error as e:
        print(f"\nError connecting to database: {e}")
        print("\nPossible issues:")
        print("  1. SQL Server container is not running")
        print("  2. Database name is different (try 'RestoredDB' or check restore output)")
        print("  3. Password is incorrect")
        print("\nTo check running containers:")
        print("  docker ps")
        print("\nTo check SQL Server logs:")
        print("  docker logs sqlserver_restore")

def main():
    print("\n" + "="*60)
    print("SQL Server .bak File Data Viewer")
    print("="*60)
    
    if not check_docker():
        print("\nError: Docker is not installed or not running.")
        print("Please install Docker Desktop: https://www.docker.com/products/docker-desktop")
        return
    
    # Step 1: Restore backup
    if not restore_backup():
        return
    
    # Wait a bit for restore to complete
    print("\nWaiting for restore to complete...")
    print("After restore completes, press Enter to view data...")
    input()
    
    # Step 2: View data
    view_database_data()

if __name__ == "__main__":
    main()

