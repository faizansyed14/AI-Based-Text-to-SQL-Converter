"""Service for getting database schema"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.sqlserver import get_sqlserver_connection

# Global variable for selected table
selected_table_name = None

def get_table_schema():
    """Get the schema of all tables from SQL Server database"""
    global selected_table_name
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        
        schema_info = {}
        
        # If a table is selected, only return that table's schema
        if selected_table_name:
            table_name = selected_table_name
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            if columns:
                schema_info[table_name] = [
                    {
                        "name": col[0], 
                        "type": col[1], 
                        "nullable": col[2] == 'YES',
                        "max_length": col[3] if col[3] else None
                    }
                    for col in columns
                ]
        else:
            # Get all table names from SQL Server
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                # Get column information
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                schema_info[table_name] = [
                    {
                        "name": col[0], 
                        "type": col[1], 
                        "nullable": col[2] == 'YES',
                        "max_length": col[3] if col[3] else None
                    }
                    for col in columns
                ]
        
        cursor.close()
        conn.close()
        return schema_info
    except Exception as e:
        print(f"Error getting schema from SQL Server: {str(e)}")
        return {}

def set_selected_table(table_name):
    """Set the selected table name"""
    global selected_table_name
    selected_table_name = table_name

def get_selected_table():
    """Get the selected table name"""
    global selected_table_name
    return selected_table_name

