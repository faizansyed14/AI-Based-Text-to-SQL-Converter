"""Service for formatting SQL query results into readable HTML/structured format"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

def format_number(value: Any) -> str:
    """Format numbers with thousand separators"""
    if value is None:
        return "null"
    try:
        if isinstance(value, (int, float)):
            if isinstance(value, float):
                # Format float with 2 decimal places if needed
                if value == int(value):
                    return f"{int(value):,}"
                return f"{value:,.2f}"
            return f"{value:,}"
    except:
        pass
    return str(value)

def format_date(value: Any) -> str:
    """Format date values"""
    if value is None:
        return "null"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, str):
        try:
            # Try to parse and format date strings
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return value
    return str(value)

def format_value(value: Any, column_name: str = "") -> str:
    """Format a single value based on its type"""
    if value is None:
        return "null"
    
    # Check if it's a date/datetime column
    if 'date' in column_name.lower() or 'time' in column_name.lower():
        return format_date(value)
    
    # Check if it's a numeric column
    if isinstance(value, (int, float)):
        return format_number(value)
    
    # Check if it's a boolean
    if isinstance(value, bool):
        return "Yes" if value else "No"
    
    return str(value)

def format_results_as_html(data: List[Dict[str, Any]], summary: Optional[Dict[str, Any]] = None) -> str:
    """Format SQL results as HTML table"""
    if not data or len(data) == 0:
        return '<div class="no-results-html"><p>No results found</p></div>'
    
    html = []
    
    # Add summary if provided
    if summary:
        html.append('<div class="results-summary">')
        html.append(f'<div class="summary-item"><strong>Total Rows:</strong> {summary.get("total_rows", len(data)):,}</div>')
        if summary.get("columns"):
            html.append(f'<div class="summary-item"><strong>Columns:</strong> {len(summary["columns"])}</div>')
        html.append('</div>')
    
    # Start table
    html.append('<div class="table-wrapper-html">')
    html.append('<table class="results-table-html">')
    
    # Header
    if data:
        columns = list(data[0].keys())
        html.append('<thead><tr>')
        for col in columns:
            # Format column names (replace underscores, capitalize)
            formatted_col = col.replace('_', ' ').title()
            html.append(f'<th>{formatted_col}</th>')
        html.append('</tr></thead>')
        
        # Body
        html.append('<tbody>')
        for row in data:
            html.append('<tr>')
            for col in columns:
                value = row.get(col)
                formatted_value = format_value(value, col)
                css_class = ""
                if value is None:
                    css_class = ' class="null-cell"'
                elif isinstance(value, (int, float)):
                    css_class = ' class="number-cell"'
                elif isinstance(value, (datetime, str)) and ('date' in col.lower() or 'time' in col.lower()):
                    css_class = ' class="date-cell"'
                
                html.append(f'<td{css_class}>{formatted_value}</td>')
            html.append('</tr>')
        html.append('</tbody>')
        
        # Footer with column headers
        html.append('<tfoot><tr>')
        for col in columns:
            formatted_col = col.replace('_', ' ').title()
            html.append(f'<th>{formatted_col}</th>')
        html.append('</tr></tfoot>')
    
    html.append('</table>')
    html.append('</div>')
    
    return ''.join(html)

def format_results_as_summary(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a summary of the results"""
    if not data:
        return {
            "total_rows": 0,
            "columns": [],
            "column_types": {}
        }
    
    columns = list(data[0].keys())
    column_types = {}
    
    for col in columns:
        sample_values = [row.get(col) for row in data[:10] if row.get(col) is not None]
        if sample_values:
            first_value = sample_values[0]
            if isinstance(first_value, (int, float)):
                column_types[col] = "number"
            elif isinstance(first_value, datetime):
                column_types[col] = "date"
            elif isinstance(first_value, bool):
                column_types[col] = "boolean"
            else:
                column_types[col] = "text"
        else:
            column_types[col] = "unknown"
    
    return {
        "total_rows": len(data),
        "columns": columns,
        "column_types": column_types
    }

def format_single_row_as_cards(data: List[Dict[str, Any]]) -> str:
    """Format single row results as cards (better for readability)"""
    if not data or len(data) == 0:
        return '<div class="no-results-html"><p>No results found</p></div>'
    
    # If more than 5 rows, use table format instead
    if len(data) > 5:
        return format_results_as_html(data)
    
    html = []
    html.append('<div class="results-cards">')
    
    for idx, row in enumerate(data):
        html.append('<div class="result-card">')
        html.append(f'<div class="card-header">Record {idx + 1}</div>')
        html.append('<div class="card-body">')
        
        for key, value in row.items():
            formatted_key = key.replace('_', ' ').title()
            formatted_value = format_value(value, key)
            
            html.append('<div class="card-field">')
            html.append(f'<div class="field-label">{formatted_key}:</div>')
            html.append(f'<div class="field-value">{formatted_value}</div>')
            html.append('</div>')
        
        html.append('</div>')
        html.append('</div>')
    
    html.append('</div>')
    
    return ''.join(html)

def format_results(data: List[Dict[str, Any]], format_type: str = "auto") -> Dict[str, Any]:
    """
    Format SQL results with summary and HTML
    
    Args:
        data: List of dictionaries containing query results
        format_type: "auto", "table", or "cards"
    
    Returns:
        Dictionary with formatted_html, summary, and raw_data
    """
    summary = format_results_as_summary(data)
    
    # Auto-detect format type
    if format_type == "auto":
        if len(data) == 1:
            format_type = "cards"
        elif len(data) <= 5 and len(data[0].keys()) <= 5:
            format_type = "cards"
        else:
            format_type = "table"
    
    if format_type == "cards":
        formatted_html = format_single_row_as_cards(data)
    else:
        formatted_html = format_results_as_html(data, summary)
    
    return {
        "formatted_html": formatted_html,
        "summary": summary,
        "raw_data": data,
        "format_type": format_type
    }

