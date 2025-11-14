"""
Export all SQL Server (VikasAI) data to Excel
This script connects to the SQL Server database and exports all tables to an Excel file.
Each table will be exported as a separate sheet.
"""
import pymssql
import pandas as pd
from datetime import datetime
import os
import re
from dotenv import load_dotenv

# Excel limitations
EXCEL_MAX_ROWS = 1048576  # Maximum rows per sheet in Excel (includes header)
EXCEL_SAFE_MAX_ROWS = 1048575  # Safe limit: max rows - 1 (to account for header row)
EXCEL_MAX_SHEET_NAME_LENGTH = 31  # Maximum sheet name length

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

def sanitize_sheet_name(name):
    """Sanitize sheet name to be Excel-compatible"""
    # Remove invalid characters: \ / ? * [ ]
    name = re.sub(r'[\\/?*\[\]]', '_', name)
    # Truncate to max length
    if len(name) > EXCEL_MAX_SHEET_NAME_LENGTH:
        name = name[:EXCEL_MAX_SHEET_NAME_LENGTH]
    return name

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

def clean_dataframe(df, aggressive=False):
    """Clean DataFrame to remove problematic characters for Excel (only if needed)"""
    if df is None or df.empty:
        return df
    
    if not aggressive:
        # Minimal cleaning - only remove null bytes that break Excel
        for col in df.select_dtypes(include=['object']).columns:
            # Only remove null bytes (0x00) which Excel cannot handle
            df[col] = df[col].astype(str).str.replace('\x00', '', regex=False)
    else:
        # Aggressive cleaning for problematic cases
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.replace('\x00', '', regex=False)
            df[col] = df[col].str.replace('\x01', '', regex=False)
            df[col] = df[col].str.replace('\x02', '', regex=False)
            df[col] = df[col].replace('nan', '', regex=False)
    
    return df

def get_table_primary_key(conn, table_name):
    """Get primary key column name for a table"""
    cursor = conn.cursor()
    try:
        query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = %s AND CONSTRAINT_NAME LIKE 'PK_%'
        """
        cursor.execute(query, (table_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except:
        return None
    finally:
        cursor.close()

def export_table_chunk(conn, table_name, chunk_num=0, limit=100000):
    """Export a chunk of a table to a pandas DataFrame"""
    cursor = conn.cursor()
    try:
        # For first chunk or no primary key, just use TOP
        query = f"SELECT TOP {limit} * FROM [{table_name}]"
        
        cursor.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch rows
        rows = cursor.fetchall()
        
        if not rows:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Minimal cleaning - only remove null bytes that break Excel
        df = clean_dataframe(df, aggressive=False)
        
        return df
    except Exception as e:
        return None
    finally:
        cursor.close()

def export_table_to_dataframe(conn, table_name, max_rows=500):
    """Export a table to a pandas DataFrame (limited to max_rows)"""
    cursor = conn.cursor()
    try:
        # Get row count first
        count_query = f"SELECT COUNT(*) FROM [{table_name}]"
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0]
        
        # Always limit to max_rows for sample export
        print(f"  Exporting {table_name}... (showing {min(max_rows, row_count):,} of {row_count:,} total rows)")
        
        # Export limited data
        query = f"SELECT TOP {max_rows} * FROM [{table_name}]"
        cursor.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Minimal cleaning - only remove null bytes that break Excel
        # Keep all other data exactly as it is in the server
        df = clean_dataframe(df, aggressive=False)
        
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
    print("Sample Export: 500 rows per table")
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
        output_file = f"/app/VikasAI_Sample_Export_{timestamp}.xlsx"
        
        print("=" * 60)
        print(f"Exporting to: {output_file}")
        print("=" * 60)
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            exported_count = 0
            failed_count = 0
            
            for table_name in tables:
                try:
                    # Get row count first
                    cursor = conn.cursor()
                    count_query = f"SELECT COUNT(*) FROM [{table_name}]"
                    cursor.execute(count_query)
                    total_rows = cursor.fetchone()[0]
                    cursor.close()
                    
                    print(f"  Processing {table_name}... ({total_rows:,} total rows)")
                    
                    # Export limited sample (500 rows per table)
                    df = export_table_to_dataframe(conn, table_name, max_rows=500)
                    if df is not None and not df.empty:
                        row_count = len(df)
                        # Normal export - single sheet (already limited to 500 rows)
                        sheet_name = sanitize_sheet_name(table_name)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        exported_count += 1
                        print(f"  ✓ {table_name} exported ({row_count:,} rows)")
                    elif df is not None:
                        # Empty table
                        sheet_name = sanitize_sheet_name(table_name)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        exported_count += 1
                        print(f"  ✓ {table_name} exported (empty table)")
                    else:
                        failed_count += 1
                        print(f"  ✗ {table_name} failed to export")
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    # Provide more helpful error messages
                    if "cannot be used in worksheets" in error_msg or "invalid" in error_msg.lower():
                        print(f"  ⚠ {table_name} has problematic characters - applying minimal cleaning...")
                        # Try with aggressive cleaning only if minimal cleaning failed
                        try:
                            df = export_table_to_dataframe(conn, table_name, max_rows=500)
                            if df is not None:
                                # Apply aggressive cleaning only for problematic characters
                                df = clean_dataframe(df, aggressive=True)
                                
                                sheet_name = sanitize_sheet_name(table_name)
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                                print(f"  ✓ {table_name} exported after cleaning ({len(df):,} rows)")
                                exported_count += 1
                                failed_count -= 1
                        except Exception as e2:
                            print(f"  ✗ {table_name} error after cleaning attempt: {str(e2)}")
                    else:
                        print(f"  ✗ {table_name} error: {error_msg}")
        
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

