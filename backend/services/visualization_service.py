"""Service for detecting visualization requests and determining chart types"""
import re
from typing import Dict, List, Any, Optional, Tuple


def detect_visualization_request(message: str) -> bool:
    """Detect if user is requesting visualization/graph/chart"""
    if not message:
        return False
    
    message_lower = message.lower().strip()
    
    # Keywords that indicate visualization request (pure visualization requests)
    visualization_keywords = [
        'show in visual',
        'show in graph',
        'show in chart',
        'visualize',
        'visualization',
        'display as graph',
        'display as chart',
        'show graph',
        'show chart',
        'plot',
        'graph it',
        'chart it',
        'make a graph',
        'make a chart',
        'create graph',
        'create chart',
        'draw graph',
        'draw chart',
        'show me in graph',
        'show me in chart',
        'show me in visual',
        'visualize this',
        'graph this',
        'chart this',
        'plot this'
    ]
    
    # Check if message is ONLY a visualization request (no query keywords)
    # This handles cases like "show me in graph" which should visualize previous response
    query_keywords = ['top', 'all', 'list', 'find', 'get', 'select', 'how many', 'what', 'which', 'where', 'when']
    has_query_keywords = any(keyword in message_lower for keyword in query_keywords)
    
    # Check if any visualization keyword is present
    has_visualization_keyword = any(keyword in message_lower for keyword in visualization_keywords)
    
    # If it has visualization keywords but no query keywords, it's a pure visualization request
    if has_visualization_keyword and not has_query_keywords:
        return True
    
    # If it has both, it's a combined query+visualization (e.g., "show top 10 products in graph")
    # This will be handled differently - generate query AND visualize
    if has_visualization_keyword and has_query_keywords:
        return True  # Still return True, but the handler will know to generate query too
    
    return False

def determine_chart_type(data: List[Dict[str, Any]]) -> Optional[str]:
    """
    Determine the best chart type based on data structure
    
    Returns: 'trend', 'bar', 'pie', 'line', or None
    """
    if not data or len(data) == 0:
        return None
    
    # Get column names
    columns = list(data[0].keys())
    
    # Check for date column
    has_date = False
    date_column = None
    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['date', 'time', 'created', 'updated', 'transaction']):
            # Check if values are actually dates
            sample_value = data[0].get(col)
            if sample_value and (isinstance(sample_value, str) and ('202' in str(sample_value) or '201' in str(sample_value) or '200' in str(sample_value))):
                has_date = True
                date_column = col
                break
    
    # Check for numeric columns
    numeric_columns = []
    for col in columns:
        sample_value = data[0].get(col)
        if sample_value is not None:
            # Try to convert to number
            try:
                float(str(sample_value).replace(',', '').replace('$', '').replace('AED', '').strip())
                numeric_columns.append(col)
            except (ValueError, AttributeError):
                pass
    
    # Check for category/group columns
    category_columns = []
    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['category', 'type', 'brand', 'group', 'code', 'name', 'desc', 'description']):
            if col != date_column:
                category_columns.append(col)
    
    # Decision logic - prefer trend/line charts for better understanding
    if has_date and numeric_columns:
        # Time series data - use line or area chart
        return 'trend'
    elif len(category_columns) > 0 and numeric_columns:
        # Categorical data with values - use trend chart for easier understanding
        # Trend charts show progression and are easier to read than bar charts
        return 'trend'
    elif numeric_columns:
        # Has numeric values - use trend chart for better visualization
        return 'trend'
    elif len(data) == 1:
        # Single row - not suitable for charts
        return None
    
    # Default to trend chart (preferred for easier understanding)
    return 'trend'

def find_matching_column(requested_name: str, available_columns: List[str]) -> Optional[str]:
    """
    Find the best matching column from available columns based on requested name
    Uses fuzzy matching to handle variations in column names
    """
    if not requested_name:
        return None
    
    # Normalize requested name: remove extra spaces, convert to lowercase
    requested_normalized = requested_name.lower().strip()
    # Create variations: with spaces, with underscores, with no separators
    requested_variations = [
        requested_normalized,  # "total value"
        requested_normalized.replace(' ', '_'),  # "total_value"
        requested_normalized.replace(' ', ''),  # "totalvalue"
        requested_normalized.replace('_', ' '),  # in case it already has underscores
    ]
    
    # Try exact match first (case-insensitive)
    for col in available_columns:
        col_lower = col.lower()
        for variation in requested_variations:
            if variation == col_lower:
                print(f"✅ Exact match found: '{requested_name}' -> '{col}'")
                return col
    
    # Try substring match (requested name in column or column in requested name)
    for col in available_columns:
        col_lower = col.lower()
        for variation in requested_variations:
            if variation in col_lower or col_lower in variation:
                print(f"✅ Substring match found: '{requested_name}' -> '{col}'")
                return col
    
    # Try partial word match (e.g., "total value" matches "Total_Value" or "TOTAL_VALUE")
    requested_words = set(re.findall(r'\w+', requested_normalized))
    best_match = None
    best_score = 0
    
    for col in available_columns:
        col_lower = col.lower()
        col_words = set(re.findall(r'\w+', col_lower))
        # Count matching words
        matching_words = requested_words.intersection(col_words)
        score = len(matching_words)
        # Prefer matches where all requested words are found
        if len(matching_words) == len(requested_words) and score > best_score:
            best_score = score
            best_match = col
        elif score > best_score:
            best_score = score
            best_match = col
    
    # If no match found, try semantic matching for common terms
    if not best_match:
        # Check for semantic equivalents
        semantic_mappings = {
            'total value': ['value', 'total', 'amount', 'cost', 'price', 'sum'],
            'total_value': ['value', 'total', 'amount', 'cost', 'price', 'sum'],
            'product description': ['description', 'desc', 'product', 'name', 'title'],
            'product_description': ['description', 'desc', 'product', 'name', 'title'],
        }
        
        for key, synonyms in semantic_mappings.items():
            if key in requested_normalized or requested_normalized in key:
                # Look for columns containing any of the synonyms
                for col in available_columns:
                    col_lower = col.lower()
                    for synonym in synonyms:
                        if synonym in col_lower:
                            print(f"✅ Semantic match found: '{requested_name}' -> '{col}' (via '{synonym}')")
                            return col
    
    if best_match:
        print(f"✅ Word match found: '{requested_name}' -> '{best_match}' (score: {best_score})")
    else:
        print(f"❌ No match found for: '{requested_name}'")
        print(f"   Available columns: {', '.join(available_columns)}")
    
    return best_match

def prepare_chart_data(data: List[Dict[str, Any]], chart_type: str, requested_column: Optional[str] = None, x_axis_column: Optional[str] = None, y_axis_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare data for chart rendering
    
    Returns: Dictionary with chart configuration
    """
    if not data or len(data) == 0:
        return {}
    
    columns = list(data[0].keys())
    
    # Find date column
    date_column = None
    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['date', 'time', 'created', 'updated', 'transaction']):
            sample_value = data[0].get(col)
            if sample_value and (isinstance(sample_value, str) and ('202' in str(sample_value) or '201' in str(sample_value) or '200' in str(sample_value))):
                date_column = col
                break
    
    # Find numeric columns
    numeric_columns = []
    for col in columns:
        sample_value = data[0].get(col)
        if sample_value is not None:
            try:
                float(str(sample_value).replace(',', '').replace('$', '').replace('AED', '').strip())
                numeric_columns.append(col)
            except (ValueError, AttributeError):
                pass
    
    # If user requested a specific column, prioritize it
    if requested_column:
        # Try to find exact match (case-insensitive)
        requested_col_lower = requested_column.lower().replace(' ', '_').replace('-', '_')
        for col in columns:
            col_lower = col.lower()
            if requested_col_lower in col_lower or col_lower in requested_col_lower:
                # Move this column to the front of numeric_columns if it's numeric
                if col in numeric_columns:
                    numeric_columns.remove(col)
                    numeric_columns.insert(0, col)
                elif col not in numeric_columns:
                    # Check if it's numeric and add it
                    sample_val = data[0].get(col)
                    if sample_val is not None:
                        try:
                            float(str(sample_val).replace(',', '').replace('$', '').replace('AED', '').strip())
                            numeric_columns.insert(0, col)
                        except:
                            pass
                break
    
    # Find category columns
    category_columns = []
    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['category', 'type', 'brand', 'group', 'code', 'name', 'desc', 'description']):
            if col != date_column:
                category_columns.append(col)
    
    # Determine X and Y axis columns based on user requests
    selected_x_axis = None
    selected_y_axis = None
    
    # If user specified both columns, try to match them
    matched_x_col = None
    matched_y_col = None
    
    if x_axis_column:
        matched_x_col = find_matching_column(x_axis_column, columns)
        if matched_x_col:
            print(f"📊 User specified X-axis column: {x_axis_column} -> matched to: {matched_x_col}")
    
    if y_axis_column:
        matched_y_col = find_matching_column(y_axis_column, columns)
        if matched_y_col:
            print(f"📊 User specified Y-axis column: {y_axis_column} -> matched to: {matched_y_col}")
    
    # If both columns were specified, determine which is X and which is Y
    # by checking which is numeric (Y-axis) and which is categorical (X-axis)
    if matched_x_col and matched_y_col:
        x_is_numeric = matched_x_col in numeric_columns
        y_is_numeric = matched_y_col in numeric_columns
        
        # If both are numeric or both are categorical, use the order specified
        if x_is_numeric == y_is_numeric:
            selected_x_axis = matched_x_col
            selected_y_axis = matched_y_col
        else:
            # Assign based on type: numeric = Y-axis, categorical = X-axis
            if x_is_numeric:
                selected_x_axis = matched_y_col
                selected_y_axis = matched_x_col
            else:
                selected_x_axis = matched_x_col
                selected_y_axis = matched_y_col
    elif matched_x_col:
        # Only X-axis specified
        selected_x_axis = matched_x_col
    elif matched_y_col:
        # Only Y-axis specified
        selected_y_axis = matched_y_col
    
    # If only Y-axis was specified (backward compatibility with requested_column)
    if not selected_y_axis and requested_column:
        selected_y_axis = find_matching_column(requested_column, columns)
        if selected_y_axis:
            print(f"📊 User requested column: {requested_column} -> matched to: {selected_y_axis}")
    
    # If X-axis not specified, try to infer it
    if not selected_x_axis:
        # Prefer date column for X-axis if available
        if date_column:
            selected_x_axis = date_column
        # Otherwise prefer category columns
        elif category_columns:
            selected_x_axis = category_columns[0]
        # Fallback to first non-numeric column
        else:
            for col in columns:
                if col not in numeric_columns and col != selected_y_axis:
                    selected_x_axis = col
                    break
    
    # If Y-axis not specified, try to infer it
    if not selected_y_axis:
        # Prioritize cost/price columns
        for col in numeric_columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['landed_cost', 'landed cost', 'selling_price', 'selling price', 'cost', 'price', 'fob']):
                selected_y_axis = col
                break
        
        # If no cost/price column, use first numeric column
        if not selected_y_axis and numeric_columns:
            selected_y_axis = numeric_columns[0]
    
    chart_config = {
        'type': chart_type,
        'data': data,
        'columns': columns,
        'dateColumn': date_column,
        'numericColumns': numeric_columns,
        'categoryColumns': category_columns,
        'xAxisColumn': selected_x_axis,  # Explicitly selected X-axis column
        'yAxisColumn': selected_y_axis,   # Explicitly selected Y-axis column
    }
    
    return chart_config

