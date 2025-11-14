"""
Export all SQL Server (VikasAI) data to Excel
This script connects to the SQL Server database and exports all tables to an Excel file.
Each table will be exported as a separate sheet.
"""
import pymssql
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQL Server configuration
SQLSERVER_CONFIG = {
    "server": os.getenv("SQLSERVER_HOST", "localhost"),
    "port": int(os.getenv("SQLSERVER_PORT", "1433")),
    "database": os.getenv("SQLSERVER_DB", "VikasAI"),
    "user": os.getenv("SQLSERVER_USER", "sa"),
    "password": os.getenv("SQLSERVER_PASSWORD", "YourStrong@Passw0rd"),
}

def get_all_tables(conn):
    """Get list of all user tables in the database"""
    cursor = conn.cursor()
    try:
        # Query to get all user tables
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Exception as e:
        print(f"Error getting table list: {str(e)}")
        return []
    finally:
        cursor.close()

def export_table_to_dataframe(conn, table_name):
    """Export a single table to a pandas DataFrame"""
    cursor = conn.cursor()
    try:
        # Get row count first
        count_query = f"SELECT COUNT(*) FROM [{table_name}]"
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0]
        print(f"  Exporting {table_name}... ({row_count:,} rows)")
        
        # Export all data
        query = f"SELECT * FROM [{table_name}]"
        cursor.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        return df
    except Exception as e:
        print(f"  Error exporting {table_name}: {str(e)}")
        return None
    finally:
        cursor.close()

def export_all_to_excel():
    """Export all tables from SQL Server to Excel"""
    print("=" * 60)
    print("SQL Server to Excel Export Tool")
    print("=" * 60)
    print(f"\nConnecting to SQL Server...")
    print(f"  Server: {SQLSERVER_CONFIG['server']}:{SQLSERVER_CONFIG['port']}")
    print(f"  Database: {SQLSERVER_CONFIG['database']}")
    print(f"  User: {SQLSERVER_CONFIG['user']}")
    
    try:
        # Connect to SQL Server
        conn = pymssql.connect(
            server=SQLSERVER_CONFIG["server"],
            port=SQLSERVER_CONFIG["port"],
            user=SQLSERVER_CONFIG["user"],
            password=SQLSERVER_CONFIG["password"],
            database=SQLSERVER_CONFIG["database"],
            timeout=30
        )
        print("✓ Connected successfully!\n")
        
        # Get all tables
        print("Getting list of tables...")
        tables = get_all_tables(conn)
        print(f"✓ Found {len(tables)} tables: {', '.join(tables)}\n")
        
        if not tables:
            print("No tables found in the database.")
            conn.close()
            return
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Save in /app directory (mounted to backend folder)
        output_file = f"/app/VikasAI_Export_{timestamp}.xlsx"
        
        print("=" * 60)
        print(f"Exporting to: {output_file}")
        print("=" * 60)
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            exported_count = 0
            failed_count = 0
            
            for table_name in tables:
                try:
                    df = export_table_to_dataframe(conn, table_name)
                    if df is not None and not df.empty:
                        # Excel sheet names are limited to 31 characters
                        sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        exported_count += 1
                        print(f"  ✓ {table_name} exported ({len(df):,} rows)")
                    elif df is not None:
                        # Empty table
                        sheet_name = table_name[:31] if len(table_name) > 31 else table_name
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        exported_count += 1
                        print(f"  ✓ {table_name} exported (empty table)")
                    else:
                        failed_count += 1
                        print(f"  ✗ {table_name} failed to export")
                except Exception as e:
                    failed_count += 1
                    print(f"  ✗ {table_name} error: {str(e)}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("Export Complete!")
        print("=" * 60)
        print(f"✓ Successfully exported: {exported_count} tables")
        if failed_count > 0:
            print(f"✗ Failed: {failed_count} tables")
        print(f"\nOutput file: {output_file}")
        print(f"File location: {os.path.abspath(output_file)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Connection error: {str(e)}")
        print("\nPlease check:")
        print("  1. SQL Server is running")
        print("  2. Connection details in .env file are correct")
        print("  3. Network connectivity to SQL Server")

if __name__ == "__main__":
    export_all_to_excel()

