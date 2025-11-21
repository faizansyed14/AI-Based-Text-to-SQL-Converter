"""Service for getting database schema"""
import sys
import os
import re
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.sqlserver import get_sqlserver_connection

# Global variable for selected table
selected_table_name = None

def generate_column_description(column_name: str, data_type: str, table_name: str) -> str:
    """Generate an intelligent description for a column based on its name and type"""
    col_lower = column_name.lower()
    
    # Special handling for STR_STOCK_CARD table
    if table_name == 'STR_STOCK_CARD':
        stock_card_descriptions = {
            'scd_pr_code': 'Product code - unique identifier for the product',
            'scd_pr_desc': 'Product description - name of the product',
            'scd_unit_cost': 'Unit cost - cost per unit of the product at transaction time',
            'scd_lo_code': 'Location code - warehouse or location identifier',
            'scd_transaction_type': 'Transaction type - type of stock movement (receipt, issue, etc.)',
            'scd_transaction_ref': 'Transaction reference - reference number for the transaction',
            'scd_transaction_date': 'Transaction date - date when stock was received or issued (used to calculate stock age)',
            'scd_party_code': 'Party code - supplier or customer code',
            'scd_party_name': 'Party name - supplier or customer name',
            'scd_rcpt_qty': 'Receipt quantity - quantity of stock received (incoming stock)',
            'scd_issue_qty': 'Issue quantity - quantity of stock issued/sold (outgoing stock)',
        }
        if col_lower in stock_card_descriptions:
            return stock_card_descriptions[col_lower]
    
    # Common patterns and their meanings
    descriptions = {
        # Code/ID fields
        'code': 'Unique identifier code',
        'id': 'Unique identifier',
        'no': 'Number or identifier',
        'num': 'Numeric identifier',
        # Description fields
        'desc': 'Description or name',
        'name': 'Name or title',
        'title': 'Title or heading',
        # Date fields
        'date': 'Date value',
        'created': 'Creation date',
        'updated': 'Last update date',
        'modified': 'Modification date',
        # Price/Cost fields
        'price': 'Price value',
        'cost': 'Cost value',
        'amount': 'Monetary amount',
        'fob': 'Free on board price',
        'selling': 'Selling price',
        'purchase': 'Purchase price',
        # Quantity fields
        'qty': 'Quantity',
        'quantity': 'Quantity amount',
        'stock': 'Stock quantity',
        'onhand': 'Quantity on hand',
        'on_order': 'Quantity on order',
        # Status flags
        'flag': 'Status flag (Y/N)',
        'status': 'Status indicator',
        'active': 'Active status',
        'delete': 'Delete flag',
        # Category/Type fields
        'type': 'Type classification',
        'category': 'Category classification',
        'class': 'Class or category',
        # User fields
        'user': 'User identifier',
        'by': 'Created/updated by user',
        'manager': 'Manager identifier',
        # Other common fields
        'percent': 'Percentage value',
        'duration': 'Time duration',
        'period': 'Time period',
        'weight': 'Weight value',
        'height': 'Height dimension',
        'width': 'Width dimension',
        'depth': 'Depth dimension',
    }
    
    # Check for common patterns
    for pattern, desc in descriptions.items():
        if pattern in col_lower:
            # Enhance description based on context
            if 'code' in col_lower or 'id' in col_lower:
                if 'product' in table_name.lower():
                    return f'Product {desc}'
                elif 'brand' in table_name.lower():
                    return f'Brand {desc}'
                elif 'category' in table_name.lower():
                    return f'Category {desc}'
                return desc
            elif 'desc' in col_lower or 'name' in col_lower:
                if 'product' in table_name.lower():
                    return f'Product {desc}'
                elif 'brand' in table_name.lower():
                    return f'Brand {desc}'
                elif 'category' in table_name.lower():
                    return f'Category {desc}'
                return desc
            return desc
    
    # If no pattern matches, create a description from the column name
    # Convert PR_CODE -> Product Code, BR_DESC -> Brand Description, etc.
    parts = re.split(r'[_\s]+', column_name)
    if len(parts) > 1:
        prefix = parts[0]
        suffix = ' '.join(parts[1:])
        
        prefix_map = {
            'PR': 'Product',
            'BR': 'Brand',
            'CT': 'Category',
            'EDC': 'EDC',
            'STR': 'Stock',
            'US': 'User',
            'DIV': 'Division',
            'UOM': 'Unit of Measure',
        }
        
        prefix_desc = prefix_map.get(prefix, prefix)
        return f'{prefix_desc} {suffix}'
    
    # Fallback: capitalize and add context
    return f'{column_name.replace("_", " ").title()} field'

def get_table_schema():
    """Get the schema of all tables from SQL Server database with column descriptions"""
    global selected_table_name
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        
        schema_info = {}
        
        # If a table is selected, only return that table's schema
        if selected_table_name:
            table_name = selected_table_name
            # Try to get column descriptions from extended properties
            try:
                cursor.execute("""
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.IS_NULLABLE,
                        c.CHARACTER_MAXIMUM_LENGTH,
                        ISNULL(CAST(ep.value AS NVARCHAR(MAX)), '') as DESCRIPTION
                    FROM INFORMATION_SCHEMA.COLUMNS c
                    LEFT JOIN sys.extended_properties ep 
                        ON ep.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
                        AND ep.minor_id = c.ORDINAL_POSITION
                        AND ep.name = 'MS_Description'
                    WHERE c.TABLE_NAME = %s
                    ORDER BY c.ORDINAL_POSITION
                """, (table_name,))
            except:
                # Fallback if extended properties query fails
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
            
            columns = cursor.fetchall()
            if columns:
                schema_info[table_name] = []
                for col in columns:
                    col_name = col[0]
                    data_type = col[1]
                    nullable = col[2] == 'YES'
                    max_length = col[3] if len(col) > 3 and col[3] else None
                    description = col[4] if len(col) > 4 and col[4] else None
                    
                    # If no description from extended properties, generate one
                    if not description or description.strip() == '':
                        description = generate_column_description(col_name, data_type, table_name)
                    
                    schema_info[table_name].append({
                        "name": col_name,
                        "type": data_type,
                        "nullable": nullable,
                        "max_length": max_length,
                        "description": description
                    })
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
                # Try to get column descriptions from extended properties
                try:
                    cursor.execute("""
                        SELECT 
                            c.COLUMN_NAME,
                            c.DATA_TYPE,
                            c.IS_NULLABLE,
                            c.CHARACTER_MAXIMUM_LENGTH,
                            ISNULL(CAST(ep.value AS NVARCHAR(MAX)), '') as DESCRIPTION
                        FROM INFORMATION_SCHEMA.COLUMNS c
                        LEFT JOIN sys.extended_properties ep 
                            ON ep.major_id = OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME)
                            AND ep.minor_id = c.ORDINAL_POSITION
                            AND ep.name = 'MS_Description'
                        WHERE c.TABLE_NAME = %s
                        ORDER BY c.ORDINAL_POSITION
                    """, (table_name,))
                except:
                    # Fallback if extended properties query fails
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                
                columns = cursor.fetchall()
                schema_info[table_name] = []
                for col in columns:
                    col_name = col[0]
                    data_type = col[1]
                    nullable = col[2] == 'YES'
                    max_length = col[3] if len(col) > 3 and col[3] else None
                    description = col[4] if len(col) > 4 and col[4] else None
                    
                    # If no description from extended properties, generate one
                    if not description or description.strip() == '':
                        description = generate_column_description(col_name, data_type, table_name)
                    
                    schema_info[table_name].append({
                        "name": col_name,
                        "type": data_type,
                        "nullable": nullable,
                        "max_length": max_length,
                        "description": description
                    })
        
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

