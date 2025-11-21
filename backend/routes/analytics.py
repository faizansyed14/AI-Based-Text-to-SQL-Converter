"""Analytics endpoints for dashboard - Dynamic schema discovery"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json
import re
from database.sqlserver import get_sqlserver_connection
from services.schema_service import get_table_schema

router = APIRouter()

def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def get_safe_numeric_cast(column_name: str, schema: dict, table_name: str) -> str:
    """Get safe SQL expression to convert column to numeric, handling different data types"""
    if table_name not in schema:
        return f"TRY_CAST([{column_name}] AS FLOAT)"
    
    # Find the column in schema
    for col in schema[table_name]:
        if col['name'] == column_name:
            col_type = col.get('type', '').lower()
            # If already numeric, no cast needed
            if any(t in col_type for t in ['int', 'bigint', 'decimal', 'numeric', 'float', 'real', 'money', 'smallmoney']):
                return f"[{column_name}]"
            # For varchar/nvarchar, use TRY_CAST which returns NULL on failure
            elif any(t in col_type for t in ['varchar', 'nvarchar', 'char', 'nchar', 'text', 'ntext']):
                return f"TRY_CAST([{column_name}] AS FLOAT)"
            else:
                # Default to TRY_CAST for safety
                return f"TRY_CAST([{column_name}] AS FLOAT)"
    
    # Fallback to TRY_CAST if column not found
    return f"TRY_CAST([{column_name}] AS FLOAT)"

def detect_column_type(column_name: str, data_type: str, description: str = "") -> Dict[str, bool]:
    """Detect column type based on name, data type, and description"""
    col_lower = column_name.lower()
    desc_lower = description.lower() if description else ""
    
    return {
        'is_date': any(keyword in col_lower for keyword in ['date', 'time', 'created', 'updated', 'modified', 'timestamp']) or 
                   any(keyword in data_type.lower() for keyword in ['date', 'time']),
        'is_quantity': any(keyword in col_lower for keyword in ['qty', 'quantity', 'stock', 'onhand', 'on_hand', 'balance', 'amount', 'count']) or
                       'quantity' in desc_lower or 'stock' in desc_lower,
        'is_price': any(keyword in col_lower for keyword in ['price', 'cost', 'amount', 'value', 'fob', 'selling', 'purchase', 'unit_cost']) or
                    any(keyword in desc_lower for keyword in ['price', 'cost', 'amount']),
        'is_code': any(keyword in col_lower for keyword in ['code', 'id', '_code', '_id']) and 
                   not any(keyword in col_lower for keyword in ['description', 'desc']),
        'is_description': any(keyword in col_lower for keyword in ['desc', 'description', 'name', 'title']),
        'is_category': any(keyword in col_lower for keyword in ['category', 'type', 'class', 'group', 'classification']),
        'is_numeric': any(keyword in data_type.lower() for keyword in ['int', 'decimal', 'numeric', 'float', 'money', 'real', 'bigint', 'smallint', 'tinyint'])
    }

def find_columns_by_type(schema: Dict[str, List[Dict]], table_name: str, column_type: str) -> List[str]:
    """Find columns of a specific type in a table"""
    if table_name not in schema:
        return []
    
    columns = []
    for col in schema[table_name]:
        col_info = detect_column_type(col['name'], col['type'], col.get('description', ''))
        if col_info.get(column_type, False):
            columns.append(col['name'])
    return columns

def find_tables_with_columns(schema: Dict[str, List[Dict]], column_types: List[str]) -> List[Dict[str, Any]]:
    """Find tables that have specific column types"""
    matching_tables = []
    
    for table_name, columns in schema.items():
        table_info = {
            'table_name': table_name,
            'columns': {}
        }
        
        for col_type in column_types:
            found_cols = find_columns_by_type(schema, table_name, col_type)
            if found_cols:
                table_info['columns'][col_type] = found_cols
        
        # Only include if it has at least one of the required types
        if table_info['columns']:
            matching_tables.append(table_info)
    
    return matching_tables

@router.get("/api/analytics/overview")
async def get_overview_stats():
    """Get overview statistics for dashboard - dynamically discovers schema"""
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        schema = get_table_schema()
        
        stats = {}
        
        # Get table names and row counts
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            except:
                table_counts[table] = 0
        
        stats['table_counts'] = table_counts
        stats['total_tables'] = len(tables)
        stats['total_records'] = sum(table_counts.values())
        
        # Dynamically find tables with quantity/stock columns
        quantity_tables = find_tables_with_columns(schema, ['is_quantity'])
        for table_info in quantity_tables:
            table_name = table_info['table_name']
            quantity_cols = table_info['columns'].get('is_quantity', [])
            
            if quantity_cols:
                try:
                    # Try to sum the first quantity column
                    qty_col = quantity_cols[0]
                    safe_cast = get_safe_numeric_cast(qty_col, schema, table_name)
                    query = f"SELECT SUM({safe_cast}) FROM [{table_name}] WHERE [{qty_col}] IS NOT NULL AND {safe_cast} IS NOT NULL"
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result and result[0]:
                        if 'quantity_summary' not in stats:
                            stats['quantity_summary'] = []
                        stats['quantity_summary'].append({
                            'table': table_name,
                            'column': qty_col,
                            'total': float(result[0])
                        })
                except:
                    pass
        
        # Dynamically find tables with price/cost columns
        price_tables = find_tables_with_columns(schema, ['is_price'])
        for table_info in price_tables:
            table_name = table_info['table_name']
            price_cols = table_info['columns'].get('is_price', [])
            
            if price_cols:
                try:
                    price_col = price_cols[0]
                    safe_cast = get_safe_numeric_cast(price_col, schema, table_name)
                    query = f"SELECT AVG({safe_cast}) FROM [{table_name}] WHERE [{price_col}] IS NOT NULL AND {safe_cast} IS NOT NULL"
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result and result[0]:
                        if 'price_summary' not in stats:
                            stats['price_summary'] = []
                        stats['price_summary'].append({
                            'table': table_name,
                            'column': price_col,
                            'avg': float(result[0])
                        })
                except:
                    pass
        
        cursor.close()
        conn.close()
        
        return json.loads(json.dumps(stats, default=decimal_to_float))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/trends")
async def get_trends(
    table: Optional[str] = Query(None, description="Table name (auto-detected if not provided)"),
    date_column: Optional[str] = Query(None, description="Date column name (auto-detected if not provided)"),
    value_column: Optional[str] = Query(None, description="Value column to aggregate (auto-detected if not provided)"),
    x_axis_column: Optional[str] = Query(None, description="X-axis column for column-to-column comparison"),
    comparison_mode: Optional[str] = Query("date", description="Comparison mode: 'date' or 'column'"),
    days: int = Query(30, description="Number of days to analyze (use -1 for all time)"),
    group_by: str = Query("day", description="Group by: day, week, month")
):
    """Get trends over time - dynamically discovers date and value columns"""
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        schema = get_table_schema()
        
        # Auto-detect table if not provided
        if not table:
            # Prefer tables with both date and numeric columns
            date_numeric_tables = []
            for table_name, columns in schema.items():
                has_date = any(detect_column_type(col['name'], col['type'], col.get('description', '')).get('is_date') for col in columns)
                has_numeric = any(detect_column_type(col['name'], col['type'], col.get('description', '')).get('is_numeric') for col in columns)
                if has_date and has_numeric:
                    date_numeric_tables.append(table_name)
            
            if date_numeric_tables:
                table = date_numeric_tables[0]
            else:
                # Fallback to any table with date columns
                date_tables = find_tables_with_columns(schema, ['is_date'])
                if not date_tables:
                    return {'trends': [], 'message': 'No tables with date columns found'}
                table = date_tables[0]['table_name']
        
        if table not in schema:
            raise HTTPException(status_code=400, detail=f"Table {table} not found")
        
        # Handle column-to-column comparison mode
        if comparison_mode == 'column' and x_axis_column:
            # Column vs Column comparison
            if not value_column:
                # Auto-detect value column
                quantity_cols = find_columns_by_type(schema, table, 'is_quantity')
                price_cols = find_columns_by_type(schema, table, 'is_price')
                numeric_cols = find_columns_by_type(schema, table, 'is_numeric')
                
                if quantity_cols:
                    value_column = quantity_cols[0]
                elif price_cols:
                    value_column = price_cols[0]
                elif numeric_cols:
                    value_column = numeric_cols[0]
                else:
                    return {'trends': [], 'message': f'No suitable numeric column found for Y-axis'}
            
            safe_cast = get_safe_numeric_cast(value_column, schema, table)
            
            # Group by X-axis column and aggregate Y-axis values
            query = f"""
                SELECT 
                    [{x_axis_column}] as period,
                    SUM({safe_cast}) as total_value,
                    COUNT(*) as record_count,
                    AVG({safe_cast}) as avg_value
                FROM [{table}]
                WHERE [{x_axis_column}] IS NOT NULL
                    AND [{value_column}] IS NOT NULL
                    AND {safe_cast} IS NOT NULL
                GROUP BY [{x_axis_column}]
                ORDER BY total_value DESC
            """
        else:
            # Date vs Value comparison (original behavior)
            # Auto-detect date column if not provided
            if not date_column:
                date_cols = find_columns_by_type(schema, table, 'is_date')
                if not date_cols:
                    return {'trends': [], 'message': f'Table {table} does not have date columns'}
                date_column = date_cols[0]
            
            # Auto-detect value column if not provided
            if not value_column:
                quantity_cols = find_columns_by_type(schema, table, 'is_quantity')
                price_cols = find_columns_by_type(schema, table, 'is_price')
                numeric_cols = find_columns_by_type(schema, table, 'is_numeric')
                
                if quantity_cols:
                    value_column = quantity_cols[0]
                elif price_cols:
                    value_column = price_cols[0]
                elif numeric_cols:
                    # Use first numeric column
                    value_column = numeric_cols[0]
                else:
                    # If no numeric columns, use COUNT(*) as fallback
                    value_column = None
            
            # Build date grouping
            if group_by == "day":
                date_part = f"CONVERT(DATE, [{date_column}])"
            elif group_by == "week":
                date_part = f"YEAR([{date_column}]), DATEPART(WEEK, [{date_column}])"
            elif group_by == "month":
                date_part = f"YEAR([{date_column}]), MONTH([{date_column}])"
            else:
                date_part = f"CONVERT(DATE, [{date_column}])"
            
            # Handle "All Time" option (days = -1)
            if days > 0:
                date_filter = f"[{date_column}] >= DATEADD(DAY, -{days}, GETDATE()) AND "
            else:
                # All time - no date filter
                date_filter = ""
            
            if value_column:
                safe_cast = get_safe_numeric_cast(value_column, schema, table)
                query = f"""
                    SELECT 
                        {date_part} as period,
                        SUM({safe_cast}) as total_value,
                        COUNT(*) as record_count
                    FROM [{table}]
                    WHERE {date_filter}[{date_column}] IS NOT NULL
                        AND [{value_column}] IS NOT NULL
                        AND {safe_cast} IS NOT NULL
                    GROUP BY {date_part}
                    ORDER BY period DESC
                """
            else:
                # Fallback: just count records by date
                query = f"""
                    SELECT 
                        {date_part} as period,
                        COUNT(*) as total_value,
                        COUNT(*) as record_count
                    FROM [{table}]
                    WHERE {date_filter}[{date_column}] IS NOT NULL
                    GROUP BY {date_part}
                    ORDER BY period DESC
                """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        trends = []
        for row in rows:
            if comparison_mode == 'column':
                # Column comparison: period is the X-axis column value
                period = str(row[0]) if row[0] is not None else 'N/A'
            else:
                # Date comparison: format based on group_by
                if group_by == "day":
                    period = str(row[0])
                elif group_by == "week":
                    period = f"{row[0]}-W{row[1]:02d}"
                elif group_by == "month":
                    period = f"{row[0]}-{row[1]:02d}"
                else:
                    period = str(row[0])
            
            trends.append({
                'period': period,
                'value': float(row[1]) if row[1] else 0,
                'count': row[2] if row[2] else 0
            })
        
        cursor.close()
        conn.close()
        
        return {
            'trends': trends,
            'table': table,
            'date_column': date_column if comparison_mode != 'column' else None,
            'value_column': value_column or 'count',
            'x_axis_column': x_axis_column if comparison_mode == 'column' else None,
            'comparison_mode': comparison_mode
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/top-items")
async def get_top_items(
    table: Optional[str] = Query(None, description="Table name"),
    code_column: Optional[str] = Query(None, description="Code/ID column"),
    description_column: Optional[str] = Query(None, description="Description column"),
    value_column: Optional[str] = Query(None, description="Value column to sort by"),
    limit: int = Query(10, description="Number of top items"),
    sort_by: str = Query("desc", description="Sort direction: asc, desc")
):
    """Get top items from any table - dynamically discovers columns"""
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        schema = get_table_schema()
        
        # Auto-detect table if not provided
        if not table:
            # Find tables with both code and quantity/price columns (prefer these)
            code_tables = find_tables_with_columns(schema, ['is_code', 'is_quantity'])
            if not code_tables:
                code_tables = find_tables_with_columns(schema, ['is_code', 'is_price'])
            if not code_tables:
                # Fallback: find any table with numeric columns
                numeric_tables = find_tables_with_columns(schema, ['is_numeric'])
                if numeric_tables:
                    table = numeric_tables[0]['table_name']
                else:
                    return {'items': [], 'message': 'No suitable tables with numeric columns found'}
            else:
                table = code_tables[0]['table_name']
        
        if table not in schema:
            raise HTTPException(status_code=400, detail=f"Table {table} not found")
        
        # Auto-detect columns
        if not code_column:
            code_cols = find_columns_by_type(schema, table, 'is_code')
            if code_cols:
                code_column = code_cols[0]
        
        if not description_column:
            desc_cols = find_columns_by_type(schema, table, 'is_description')
            if desc_cols:
                description_column = desc_cols[0]
        
        if not value_column:
            quantity_cols = find_columns_by_type(schema, table, 'is_quantity')
            price_cols = find_columns_by_type(schema, table, 'is_price')
            numeric_cols = find_columns_by_type(schema, table, 'is_numeric')
            
            if quantity_cols:
                value_column = quantity_cols[0]
            elif price_cols:
                value_column = price_cols[0]
            elif numeric_cols:
                # Use first numeric column (excluding code columns)
                value_column = next((col for col in numeric_cols if col not in (code_cols or [])), numeric_cols[0])
            else:
                # If no numeric columns, return empty result instead of error
                return {'items': [], 'message': f'Table {table} does not have suitable numeric columns for analysis'}
        
        # Build query
        select_cols = []
        if code_column:
            select_cols.append(f"[{code_column}] as code")
        if description_column:
            select_cols.append(f"[{description_column}] as description")
        safe_cast = get_safe_numeric_cast(value_column, schema, table)
        select_cols.append(f"{safe_cast} as value")
        
        order_dir = "DESC" if sort_by.lower() == "desc" else "ASC"
        
        query = f"""
            SELECT TOP {limit}
                {', '.join(select_cols)}
            FROM [{table}]
            WHERE [{value_column}] IS NOT NULL
                AND {safe_cast} IS NOT NULL
            ORDER BY {safe_cast} {order_dir}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        items = []
        for row in rows:
            item = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, Decimal):
                    value = float(value)
                item[col] = value
            items.append(item)
        
        cursor.close()
        conn.close()
        
        return {
            'items': items,
            'table': table,
            'columns_used': {
                'code': code_column,
                'description': description_column,
                'value': value_column
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/group-by")
async def get_group_by_analysis(
    table: Optional[str] = Query(None, description="Table name"),
    group_column: Optional[str] = Query(None, description="Column to group by (category, type, etc.)"),
    value_column: Optional[str] = Query(None, description="Value column to aggregate"),
    limit: int = Query(20, description="Maximum number of groups")
):
    """Get grouped analysis - dynamically discovers grouping and value columns"""
    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        schema = get_table_schema()
        
        # Auto-detect table if not provided
        if not table:
            category_tables = find_tables_with_columns(schema, ['is_category', 'is_quantity'])
            if not category_tables:
                category_tables = find_tables_with_columns(schema, ['is_category', 'is_price'])
            if category_tables:
                table = category_tables[0]['table_name']
            else:
                return {'groups': [], 'message': 'No suitable tables found for grouping'}
        
        if table not in schema:
            raise HTTPException(status_code=400, detail=f"Table {table} not found")
        
        # Auto-detect group column
        if not group_column:
            category_cols = find_columns_by_type(schema, table, 'is_category')
            if category_cols:
                group_column = category_cols[0]
            else:
                desc_cols = find_columns_by_type(schema, table, 'is_description')
                if desc_cols:
                    group_column = desc_cols[0]
                else:
                    return {'groups': [], 'message': f'Table {table} does not have suitable grouping columns'}
        
        # Auto-detect value column
        if not value_column:
            quantity_cols = find_columns_by_type(schema, table, 'is_quantity')
            price_cols = find_columns_by_type(schema, table, 'is_price')
            numeric_cols = find_columns_by_type(schema, table, 'is_numeric')
            
            if quantity_cols:
                value_column = quantity_cols[0]
            elif price_cols:
                value_column = price_cols[0]
            elif numeric_cols:
                value_column = numeric_cols[0]
            else:
                # Use COUNT(*) as fallback
                value_column = None
        
        if value_column:
            safe_cast = get_safe_numeric_cast(value_column, schema, table)
            query = f"""
                SELECT TOP {limit}
                    [{group_column}] as group_name,
                    SUM({safe_cast}) as total_value,
                    COUNT(*) as count,
                    AVG({safe_cast}) as avg_value
                FROM [{table}]
                WHERE [{group_column}] IS NOT NULL
                    AND [{value_column}] IS NOT NULL
                    AND {safe_cast} IS NOT NULL
                GROUP BY [{group_column}]
                ORDER BY total_value DESC
            """
        else:
            # Fallback: just count records by group
            query = f"""
                SELECT TOP {limit}
                    [{group_column}] as group_name,
                    COUNT(*) as total_value,
                    COUNT(*) as count,
                    COUNT(*) as avg_value
                FROM [{table}]
                WHERE [{group_column}] IS NOT NULL
                GROUP BY [{group_column}]
                ORDER BY total_value DESC
            """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        groups = []
        for row in rows:
            groups.append({
                'group_name': row[0] or 'Uncategorized',
                'total_value': float(row[1]) if row[1] else 0,
                'count': row[2] if row[2] else 0,
                'avg_value': float(row[3]) if row[3] else 0
            })
        
        cursor.close()
        conn.close()
        
        return {
            'groups': groups,
            'table': table,
            'group_column': group_column,
            'value_column': value_column or 'count'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/schema-info")
async def get_schema_info():
    """Get schema information for frontend to build dynamic UI"""
    try:
        schema = get_table_schema()
        
        schema_info = {}
        for table_name, columns in schema.items():
            table_info = {
                'columns': [],
                'detected_types': {}
            }
            
            for col in columns:
                col_info = detect_column_type(col['name'], col['type'], col.get('description', ''))
                table_info['columns'].append({
                    'name': col['name'],
                    'type': col['type'],
                    'description': col.get('description', ''),
                    'types': col_info
                })
                
                # Track detected types
                for col_type, is_match in col_info.items():
                    if is_match:
                        if col_type not in table_info['detected_types']:
                            table_info['detected_types'][col_type] = []
                        table_info['detected_types'][col_type].append(col['name'])
            
            schema_info[table_name] = table_info
        
        return {'schema': schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/custom-query")
async def get_custom_analytics(
    query: str = Query(..., description="Custom SQL query (SELECT only)")
):
    """Execute custom analytics query (read-only)"""
    try:
        # Validate query is SELECT only
        query_upper = query.upper().strip()
        if not query_upper.startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        
        # Check for write operations
        write_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        if any(keyword in query_upper for keyword in write_keywords):
            raise HTTPException(status_code=400, detail="Write operations are not allowed")
        
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, Decimal):
                    value = float(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col] = value
            results.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return {'columns': columns, 'data': results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
