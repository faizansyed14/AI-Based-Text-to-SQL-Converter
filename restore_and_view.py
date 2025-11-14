#!/usr/bin/env python3
"""
Automated script to restore .bak file and view data
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, shell=False):
    """Run a command and return result"""
    if shell:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def main():
    backup_file = "VikasAI.Bak"
    container_name = "sqlserver_restore"
    sa_password = "YourStrong@Passw0rd"
    db_name = "VikasAI"
    
    print("="*60)
    print("Automated .bak File Restore and Data Viewer")
    print("="*60)
    
    # Check if backup exists
    if not Path(backup_file).exists():
        print(f"\nError: {backup_file} not found in current directory")
        return
    
    print(f"\nBackup file: {backup_file}")
    print(f"Size: {Path(backup_file).stat().st_size / (1024*1024):.2f} MB")
    
    # Step 1: Check/Start SQL Server container
    print("\n" + "-"*60)
    print("Step 1: Starting SQL Server container...")
    print("-"*60)
    
    # Check if container exists
    success, stdout, stderr = run_command(f"docker ps -a -q -f name={container_name}", shell=True)
    container_exists = bool(stdout.strip())
    
    if container_exists:
        print(f"Container '{container_name}' exists. Starting it...")
        success, stdout, stderr = run_command(f"docker start {container_name}", shell=True)
        if not success:
            print(f"Error starting container: {stderr}")
            return
    else:
        print("Creating new SQL Server container...")
        docker_cmd = [
            'docker', 'run', '-e', 'ACCEPT_EULA=Y',
            '-e', f'SA_PASSWORD={sa_password}',
            '-p', '1433:1433',
            '--name', container_name,
            '-d',
            'mcr.microsoft.com/mssql/server:2019-latest'
        ]
        success, stdout, stderr = run_command(docker_cmd)
        if not success:
            print(f"Error creating container: {stderr}")
            return
        print("Container created. Waiting for SQL Server to start (30 seconds)...")
        time.sleep(30)
    
    print("[OK] SQL Server container is running")
    
    # Step 2: Copy backup file
    print("\n" + "-"*60)
    print("Step 2: Copying backup file to container...")
    print("-"*60)
    
    success, stdout, stderr = run_command(f"docker cp {backup_file} {container_name}:/var/opt/mssql/backup.bak", shell=True)
    if not success:
        print(f"Error copying file: {stderr}")
        return
    print("[OK] Backup file copied")
    
    # Step 3: Get backup info and restore
    print("\n" + "-"*60)
    print("Step 3: Restoring database...")
    print("-"*60)
    
    # First, try to get file list
    # Try different sqlcmd paths (SQL Server 2019 vs 2022)
    sqlcmd_path = '/opt/mssql-tools18/bin/sqlcmd'  # SQL Server 2022 path
    # Check if it exists, if not try older path
    check_cmd = f"docker exec {container_name} test -f {sqlcmd_path}"
    success, _, _ = run_command(check_cmd, shell=True)
    if not success:
        sqlcmd_path = '/opt/mssql-tools/bin/sqlcmd'  # SQL Server 2019 path
    
    sql_cmd = "RESTORE FILELISTONLY FROM DISK='/var/opt/mssql/backup.bak'"
    docker_cmd = f"""docker exec {container_name} {sqlcmd_path} -S localhost -U sa -P '{sa_password}' -C -Q "{sql_cmd}" """
    
    success, stdout, stderr = run_command(docker_cmd, shell=True)
    print("Backup file information:")
    print(stdout)
    
    # Try restore without MOVE first (simpler)
    print(f"\nRestoring as '{db_name}'...")
    sql_cmd = f"RESTORE DATABASE [{db_name}] FROM DISK='/var/opt/mssql/backup.bak' WITH REPLACE"
    docker_cmd = f"""docker exec {container_name} {sqlcmd_path} -S localhost -U sa -P '{sa_password}' -C -Q "{sql_cmd}" """
    
    success, stdout, stderr = run_command(docker_cmd, shell=True)
    if success:
        print(f"[OK] Database '{db_name}' restored successfully!")
    else:
        print(f"Restore attempt output: {stdout}")
        print(f"Error: {stderr}")
        print("\nTrying alternative restore method...")
        # Try with different database name
        db_name = "RestoredDB"
        sql_cmd = f"RESTORE DATABASE [{db_name}] FROM DISK='/var/opt/mssql/backup.bak' WITH REPLACE"
        docker_cmd = f"""docker exec {container_name} {sqlcmd_path} -S localhost -U sa -P '{sa_password}' -C -Q "{sql_cmd}" """
        success, stdout, stderr = run_command(docker_cmd, shell=True)
        if success:
            print(f"[OK] Database '{db_name}' restored successfully!")
        else:
            print(f"Restore failed. Error: {stderr}")
            print("You may need to restore manually. See RESTORE_BAK_GUIDE.md")
            return
    
    # Step 4: View data
    print("\n" + "-"*60)
    print("Step 4: Viewing database data...")
    print("-"*60)
    
    # Install pymssql if needed
    try:
        import pymssql
    except ImportError:
        print("Installing pymssql...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pymssql'], check=True)
        import pymssql
    
    # Wait a moment for database to be ready
    time.sleep(5)
    
    try:
        conn = pymssql.connect(server='localhost', user='sa', password=sa_password, database=db_name)
        cursor = conn.cursor()
        
        # List tables
        print("\nTables in database:")
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        if not tables:
            print("  No tables found")
        else:
            for schema, table in tables:
                print(f"  {schema}.{table}")
            
            # Show sample data
            print("\n" + "-"*60)
            print("Sample Data (first 3 rows from each table):")
            print("-"*60)
            
            for schema, table in tables[:10]:  # Limit to first 10 tables
                full_table_name = f"[{schema}].[{table}]" if schema else f"[{table}]"
                try:
                    cursor.execute(f"SELECT TOP 3 * FROM {full_table_name}")
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    print(f"\n{table}:")
                    print(f"  Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                    for i, row in enumerate(rows, 1):
                        row_str = str(row[:5]) + ('...' if len(row) > 5 else '')
                        print(f"  Row {i}: {row_str}")
                except Exception as e:
                    print(f"\n{table}: Error - {str(e)[:50]}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("SUCCESS! Database restored and data viewed.")
        print("="*60)
        print(f"\nConnection details:")
        print(f"  Server: localhost,1433")
        print(f"  Database: {db_name}")
        print(f"  Username: sa")
        print(f"  Password: {sa_password}")
        print("\nYou can now query the database using:")
        print("  - Python with pymssql")
        print("  - SQL Server Management Studio")
        print("  - Azure Data Studio")
        print("  - Or run: python view_bak_data.py")
        
    except Exception as e:
        print(f"\nError viewing data: {e}")
        print("\nDatabase was restored but there was an error viewing data.")
        print("You can connect manually using the connection details above.")

if __name__ == "__main__":
    main()

