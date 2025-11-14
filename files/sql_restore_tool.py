#!/usr/bin/env python3
"""
SQL Server Backup Restore Tool
Reads SQL Server .bak files and provides restoration options
"""

import subprocess
import os
from pathlib import Path
import sys

class SQLServerRestoreTool:
    """Tool to restore SQL Server backups"""
    
    def __init__(self, backup_file):
        self.backup_file = Path(backup_file)
        self.container_name = "sqlserver_restore"
        
    def check_docker(self):
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def start_sql_server_container(self, sa_password="YourStrong@Passw0rd"):
        """Start SQL Server in Docker container"""
        print("\nStarting SQL Server 2019 container...")
        print("This may take a few minutes on first run (downloading image)...\n")
        
        # Check if container already exists
        check_cmd = f"docker ps -a -q -f name={self.container_name}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            print(f"Container '{self.container_name}' already exists. Starting it...")
            subprocess.run(f"docker start {self.container_name}", shell=True)
        else:
            # Create new container
            docker_cmd = [
                'docker', 'run', '-e', 'ACCEPT_EULA=Y',
                '-e', f'SA_PASSWORD={sa_password}',
                '-p', '1433:1433',
                '--name', self.container_name,
                '-d',
                'mcr.microsoft.com/mssql/server:2019-latest'
            ]
            
            result = subprocess.run(docker_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error starting container: {result.stderr}")
                return False
        
        print(f"✓ SQL Server container '{self.container_name}' is running")
        print(f"  Connection: localhost,1433")
        print(f"  Username: sa")
        print(f"  Password: {sa_password}")
        print("\nWaiting for SQL Server to be ready (30 seconds)...")
        
        import time
        time.sleep(30)
        
        return True
    
    def copy_backup_to_container(self):
        """Copy backup file to container"""
        print(f"\nCopying backup file to container...")
        
        cmd = f"docker cp {self.backup_file} {self.container_name}:/var/opt/mssql/backup.bak"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Backup file copied successfully")
            return True
        else:
            print(f"Error copying file: {result.stderr}")
            return False
    
    def get_backup_info(self):
        """Get information about the backup file"""
        print("\nGetting backup file information...")
        
        sql_cmd = """
        RESTORE FILELISTONLY 
        FROM DISK = '/var/opt/mssql/backup.bak'
        """
        
        docker_cmd = f"""docker exec {self.container_name} /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourStrong@Passw0rd' -Q "{sql_cmd}" """
        
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        
        return result.returncode == 0
    
    def get_logical_file_names(self, sa_password="YourStrong@Passw0rd"):
        """Get logical file names from backup to use in RESTORE command"""
        print("\nExtracting logical file names from backup...")
        
        sql_cmd = """
        RESTORE FILELISTONLY 
        FROM DISK = '/var/opt/mssql/backup.bak'
        """
        
        # Use -s flag for comma-separated output, easier to parse
        docker_cmd = f"""docker exec {self.container_name} /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{sa_password}' -s "," -h -1 -W -Q "{sql_cmd}" """
        
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error getting file list: {result.stderr}")
            print(f"Output: {result.stdout}")
            return None, None
        
        # Parse output to get logical names
        # Output format varies: could be comma, pipe, or tab separated
        lines = result.stdout.strip().split('\n')
        data_file = None
        log_file = None
        
        for line in lines:
            line = line.strip()
            if not line or 'LogicalName' in line or '---' in line:
                continue
            
            # Try different separators
            for separator in [',', '|', '\t']:
                if separator in line:
                    parts = [p.strip() for p in line.split(separator)]
                    if len(parts) >= 3:
                        logical_name = parts[0]
                        file_type = parts[2] if len(parts) > 2 else None
                        
                        if file_type == 'D' or (file_type and 'D' in str(file_type)):  # Data file
                            data_file = logical_name
                        elif file_type == 'L' or (file_type and 'L' in str(file_type)):  # Log file
                            log_file = logical_name
                    break
        
        # If parsing failed, try a simpler approach - just get first two non-empty lines
        if not data_file or not log_file:
            print("  Warning: Could not parse file list automatically. Trying alternative method...")
            # Try without separator flag
            docker_cmd2 = f"""docker exec {self.container_name} /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{sa_password}' -h -1 -W -Q "{sql_cmd}" """
            result2 = subprocess.run(docker_cmd2, shell=True, capture_output=True, text=True)
            if result2.returncode == 0:
                # Look for patterns in the output
                output = result2.stdout
                # This is a fallback - we'll let SQL Server handle it
                print("  Will attempt restore without explicit file names")
        
        print(f"  Data file: {data_file}")
        print(f"  Log file: {log_file}")
        
        return data_file, log_file
    
    def restore_database(self, new_db_name="RestoredDB", sa_password="YourStrong@Passw0rd"):
        """Restore the database"""
        print(f"\nRestoring database as '{new_db_name}'...")
        
        # Get logical file names from backup
        data_file, log_file = self.get_logical_file_names(sa_password)
        
        if not data_file or not log_file:
            print("Warning: Could not determine logical file names. Attempting restore with auto-detection...")
            # Try restore without MOVE - SQL Server will use default names
            sql_cmd = f"""
            RESTORE DATABASE [{new_db_name}]
            FROM DISK = '/var/opt/mssql/backup.bak'
            WITH REPLACE
            """
        else:
            # Use the logical file names from the backup
        sql_cmd = f"""
        RESTORE DATABASE [{new_db_name}]
        FROM DISK = '/var/opt/mssql/backup.bak'
        WITH REPLACE,
            MOVE '{data_file}' TO '/var/opt/mssql/data/{new_db_name}.mdf',
            MOVE '{log_file}' TO '/var/opt/mssql/data/{new_db_name}_log.ldf'
        """
        
        docker_cmd = f"""docker exec {self.container_name} /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P '{sa_password}' -Q "{sql_cmd}" """
        
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Database restored successfully as '{new_db_name}'")
            print("\nYou can now connect to it using:")
            print("  Server: localhost,1433")
            print("  Database: " + new_db_name)
            print("  Username: sa")
            print(f"  Password: {sa_password}")
            return True
        else:
            print(f"Error during restore: {result.stderr}")
            print(result.stdout)
            return False
    
    def generate_connection_script(self):
        """Generate Python script to connect to restored database"""
        script = """
import pymssql

# Connection details
server = 'localhost'
database = 'RestoredDB'
username = 'sa'
password = 'YourStrong@Passw0rd'

# Connect and query
try:
    conn = pymssql.connect(server=server, user=username, 
                          password=password, database=database)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute(\"\"\"
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    \"\"\")
    
    print("Tables in database:")
    for row in cursor:
        print(f"  {row[0]}.{row[1]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
"""
        
        with open('/home/claude/connect_to_db.py', 'w') as f:
            f.write(script)
        
        print("\n✓ Connection script created: connect_to_db.py")


def print_menu():
    """Print interactive menu"""
    print("\n" + "="*60)
    print("SQL Server Backup Restore Tool")
    print("="*60)
    print("\nOptions:")
    print("1. Analyze backup file (no SQL Server needed)")
    print("2. Restore backup using Docker (requires Docker)")
    print("3. Generate restore instructions")
    print("4. Exit")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python sql_restore_tool.py <backup_file.bak>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    if not Path(backup_file).exists():
        print(f"Error: File '{backup_file}' not found")
        sys.exit(1)
    
    tool = SQLServerRestoreTool(backup_file)
    
    while True:
        print_menu()
        choice = input("Select option (1-4): ").strip()
        
        if choice == '1':
            # Run the analyzer
            print("\nAnalyzing backup file...")
            backup_reader_path = Path(__file__).parent / 'sql_backup_reader.py'
            if backup_reader_path.exists():
                subprocess.run([sys.executable, str(backup_reader_path), backup_file])
            else:
                # Try current directory
                backup_reader_path = Path('sql_backup_reader.py')
                if backup_reader_path.exists():
                    subprocess.run([sys.executable, str(backup_reader_path), backup_file])
                else:
                    print("Error: sql_backup_reader.py not found. Please ensure it's in the same directory.")
            
        elif choice == '2':
            if not tool.check_docker():
                print("\nError: Docker is not installed or not running.")
                print("Please install Docker first: https://docs.docker.com/get-docker/")
                continue
            
            print("\nThis will:")
            print("  - Start SQL Server 2019 in Docker")
            print("  - Copy your backup file to the container")
            print("  - Restore the database")
            print()
            
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm != 'yes':
                continue
            
            sa_password = input("\nEnter SA password (default: YourStrong@Passw0rd): ").strip()
            if not sa_password:
                sa_password = "YourStrong@Passw0rd"
            
            if tool.start_sql_server_container(sa_password):
                if tool.copy_backup_to_container():
                    tool.get_backup_info()
                    
                    db_name = input("\nEnter name for restored database (default: RestoredDB): ").strip()
                    if not db_name:
                        db_name = "RestoredDB"
                    
                    if tool.restore_database(db_name, sa_password):
                        tool.generate_connection_script()
        
        elif choice == '3':
            print("\n" + "="*60)
            print("Manual Restore Instructions")
            print("="*60)
            print("""
Using SQL Server Management Studio (SSMS):
1. Connect to your SQL Server instance
2. Right-click 'Databases' → 'Restore Database'
3. Select 'Device' and browse to your .bak file
4. Click 'OK' to restore

Using T-SQL:
RESTORE DATABASE YourDatabaseName
FROM DISK = 'C:\\path\\to\\your\\backup.bak'
WITH REPLACE

Using Docker (manual):
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourPassword" \\
   -p 1433:1433 --name sql_server \\
   -d mcr.microsoft.com/mssql/server:2019-latest

docker cp backup.bak sql_server:/var/opt/mssql/backup.bak

docker exec sql_server /opt/mssql-tools/bin/sqlcmd \\
   -S localhost -U sa -P 'YourPassword' \\
   -Q "RESTORE DATABASE MyDB FROM DISK='/var/opt/mssql/backup.bak'"
            """)
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
