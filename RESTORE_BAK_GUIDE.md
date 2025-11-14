# How to Restore Your .bak File to SQL Database

This guide will help you restore your `VikasAI.Bak` file to create a SQL Server database.

## Quick Start

### Option 1: Use the Automated Tool (Recommended)

1. **Make sure Docker is installed and running**
   - Download Docker Desktop: https://www.docker.com/products/docker-desktop
   - Start Docker Desktop

2. **Run the restore tool:**
   ```bash
   python restore_bak_file.py
   ```
   
   Or directly:
   ```bash
   python files/sql_restore_tool.py VikasAI.Bak
   ```

3. **Follow the interactive prompts:**
   - Select option `2` to restore using Docker
   - Confirm when prompted
   - Enter a database name (or use default: `RestoredDB`)
   - Wait for the restore to complete

### Option 2: Manual Steps

If you prefer to do it manually:

1. **Start SQL Server in Docker:**
   ```bash
   docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" \
      -p 1433:1433 --name sqlserver_restore \
      -d mcr.microsoft.com/mssql/server:2019-latest
   ```

2. **Wait for SQL Server to start (about 30 seconds)**

3. **Copy your backup file to the container:**
   ```bash
   docker cp VikasAI.Bak sqlserver_restore:/var/opt/mssql/backup.bak
   ```

4. **Get backup information (to find logical file names):**
   ```bash
   docker exec sqlserver_restore /opt/mssql-tools/bin/sqlcmd \
      -S localhost -U sa -P 'YourStrong@Passw0rd' \
      -Q "RESTORE FILELISTONLY FROM DISK='/var/opt/mssql/backup.bak'"
   ```

5. **Restore the database:**
   ```bash
   docker exec sqlserver_restore /opt/mssql-tools/bin/sqlcmd \
      -S localhost -U sa -P 'YourStrong@Passw0rd' \
      -Q "RESTORE DATABASE [VikasAI] FROM DISK='/var/opt/mssql/backup.bak' WITH REPLACE"
   ```

   Note: If the restore fails, you may need to specify the logical file names. The tool will automatically detect these.

## After Restoration

Once restored, you can connect to your database:

**Connection Details:**
- Server: `localhost,1433`
- Database: `VikasAI` (or whatever name you chose)
- Username: `sa`
- Password: `YourStrong@Passw0rd` (or the password you set)

### Using Python (pymssql):

```python
import pymssql

conn = pymssql.connect(
    server='localhost',
    user='sa',
    password='YourStrong@Passw0rd',
    database='VikasAI'
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES")
for row in cursor:
    print(row)

conn.close()
```

### Using SQL Server Management Studio (SSMS):

1. Download SSMS: https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms
2. Connect to:
   - Server name: `localhost,1433`
   - Authentication: SQL Server Authentication
   - Login: `sa`
   - Password: `YourStrong@Passw0rd`
3. Browse your restored database

## Troubleshooting

### Issue: "Docker is not installed"
- Install Docker Desktop from https://www.docker.com/products/docker-desktop
- Make sure Docker is running (check system tray)

### Issue: "Container already exists"
- The tool will automatically start the existing container
- To remove and recreate: `docker rm -f sqlserver_restore`

### Issue: "Restore failed - file names not found"
- The tool now automatically detects logical file names
- If it still fails, try the manual restore without MOVE clauses

### Issue: "Port 1433 already in use"
- Stop any existing SQL Server instances
- Or change the port mapping: `-p 1434:1433` (then use `localhost,1434`)

## Migrating to PostgreSQL (Optional)

If you want to use PostgreSQL instead of SQL Server:

1. First restore to SQL Server (as above)
2. Use a migration tool like:
   - **pgloader**: https://pgloader.readthedocs.io/
   - **SQL Server Migration Assistant (SSMA)**: https://docs.microsoft.com/en-us/sql/ssma/sql-server/microsoft-sql-server-migration-assistant-for-sql-server
   - Or export data to CSV and import to PostgreSQL

## Notes

- The restored database will be in a Docker container
- Data persists as long as the container exists
- To persist data permanently, use Docker volumes
- The container uses about 1.5 GB of disk space

