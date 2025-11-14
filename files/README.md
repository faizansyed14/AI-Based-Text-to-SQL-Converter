# SQL Server Backup File Reader and Restore Tools

This toolkit helps you read, analyze, and restore SQL Server `.bak` backup files.

## Files Included

1. **sql_backup_reader.py** - Analyzes .bak files and extracts metadata
2. **sql_restore_tool.py** - Interactive tool to restore backups
3. **connect_to_db.py** - Generated script to connect to restored database

## Quick Start

### Option 1: Analyze the Backup File (No SQL Server needed)

```bash
python sql_backup_reader.py your_backup.bak
```

This will show you:
- File size
- Database name (if detectable)
- Server name
- Backup date
- SQL Server version
- Other metadata

### Option 2: Restore the Backup

```bash
python sql_restore_tool.py your_backup.bak
```

This interactive tool provides:
1. Backup analysis
2. Automatic restore using Docker
3. Manual restore instructions

## Requirements

### For Analysis Only
- Python 3.6+
- No additional dependencies

### For Restoration
- Python 3.6+
- Docker (for automated restore)
- OR SQL Server installed locally/remotely

## Restore Methods

### Method 1: Using Docker (Easiest)

The tool will automatically:
1. Download SQL Server 2019 Docker image
2. Start a SQL Server container
3. Copy your backup file
4. Restore the database

Requirements:
- Docker installed and running
- About 1.5 GB disk space for SQL Server image

### Method 2: Using Existing SQL Server

If you have SQL Server installed:

**Using SSMS (SQL Server Management Studio):**
1. Open SSMS and connect to your server
2. Right-click "Databases" → "Restore Database"
3. Select "Device" and browse to your .bak file
4. Click OK

**Using T-SQL:**
```sql
RESTORE DATABASE YourDatabaseName
FROM DISK = 'C:\path\to\backup.bak'
WITH REPLACE
```

### Method 3: Using Python to Connect

After restoration, use the generated `connect_to_db.py`:

```bash
pip install pymssql
python connect_to_db.py
```

Or use your own connection:

```python
import pymssql

conn = pymssql.connect(
    server='localhost',
    user='sa',
    password='YourStrong@Passw0rd',
    database='RestoredDB'
)

cursor = conn.cursor()
cursor.execute('SELECT * FROM your_table')
for row in cursor:
    print(row)

conn.close()
```

## Common Issues

### Issue: "Not a valid SQL Server backup"
- The file might be corrupted
- It might be from a very old SQL Server version
- It might be encrypted or compressed with third-party tools

### Issue: Docker restore fails
- Ensure Docker has enough memory (4GB+ recommended)
- Check Docker is running: `docker ps`
- Check logs: `docker logs sqlserver_restore`

### Issue: Cannot connect after restore
- Wait 30-60 seconds for SQL Server to fully start
- Verify port 1433 is not blocked by firewall
- Check password is correct

## Working with the Restored Database

Once restored, you can:

1. **Query using Python:**
   ```python
   import pymssql
   conn = pymssql.connect('localhost', 'sa', 'password', 'RestoredDB')
   ```

2. **Query using sqlcmd:**
   ```bash
   sqlcmd -S localhost -U sa -P 'password' -d RestoredDB -Q "SELECT * FROM sys.tables"
   ```

3. **Export to other formats:**
   ```python
   import pandas as pd
   import pymssql
   
   conn = pymssql.connect('localhost', 'sa', 'password', 'RestoredDB')
   df = pd.read_sql('SELECT * FROM your_table', conn)
   df.to_csv('exported_data.csv', index=False)
   ```

4. **Connect with GUI tools:**
   - Azure Data Studio
   - SQL Server Management Studio (SSMS)
   - DBeaver
   - DataGrip

## Security Notes

- Default password in scripts: `YourStrong@Passw0rd`
- Change this for production use
- SQL Server in Docker is accessible on localhost:1433
- Use firewall rules to restrict access if needed

## Advanced Usage

### Custom Restore Location

```python
from sql_restore_tool import SQLServerRestoreTool

tool = SQLServerRestoreTool('backup.bak')
tool.start_sql_server_container(sa_password='CustomPassword123!')
tool.copy_backup_to_container()
tool.restore_database('MyCustomDBName')
```

### Extract Specific Tables

```python
import pymssql
import pandas as pd

conn = pymssql.connect('localhost', 'sa', 'password', 'RestoredDB')

# Get table list
tables = pd.read_sql("""
    SELECT TABLE_SCHEMA, TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
""", conn)

print(tables)

# Export specific table
df = pd.read_sql('SELECT * FROM dbo.YourTable', conn)
df.to_csv('table_export.csv')
```

## License

Free to use and modify.

## Troubleshooting

For help, run the analyzer first to understand your backup file:
```bash
python sql_backup_reader.py your_backup.bak
```

This will tell you the SQL Server version and help diagnose issues.
