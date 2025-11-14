"""Service for SQL query generation and execution"""
import json
import re
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Optional, Tuple, Dict, Any
from openai import OpenAI
from models.schemas import ChatMessage
from database.sqlserver import get_sqlserver_connection
from services.schema_service import get_table_schema
from services.model_service import generate_sql_with_model

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_sql_from_response(response: str) -> str:
    """Extract SQL query from model response, handling cases where model returns text + SQL"""
    if not response:
        return ""
    
    response = response.strip()
    
    # If response contains SELECT, extract the SQL part
    if "SELECT" in response.upper():
        # Find the first SELECT
        select_index = response.upper().find("SELECT")
        sql_part = response[select_index:]
        
        # Find where SQL ends (semicolon, or end of string, or before explanation text)
        semicolon_index = sql_part.find(";")
        if semicolon_index > 0:
            sql_part = sql_part[:semicolon_index + 1]
        else:
            # Try to find end of SQL by looking for common SQL keywords followed by non-SQL text
            lines = sql_part.split("\n")
            sql_lines = []
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                # Stop if we hit explanatory text (common patterns)
                if line_stripped.lower().startswith(("there are", "the query", "this will", "note:", "warning:", "error:", "the result")):
                    break
                # Stop if line doesn't look like SQL
                if not any(keyword in line_stripped.upper() for keyword in ["SELECT", "FROM", "WHERE", "JOIN", "ORDER", "GROUP", "HAVING", "COUNT", "SUM", "AVG", "MAX", "MIN", "TOP", "DISTINCT", "AS", "ON", "AND", "OR", "IN", "LIKE", "BETWEEN", "IS", "NULL", "[", "]", "(", ")", ";", ",", "=", "<", ">", "!"]):
                    if len(sql_lines) > 0:  # Only stop if we already have some SQL
                        break
                sql_lines.append(line)
            sql_part = " ".join(sql_lines).strip()
        
        return sql_part
    
    return response

def make_case_insensitive(sql_query: str) -> str:
    """Post-process SQL query to ensure case-insensitive text comparisons"""
    import re
    
    sql_upper = sql_query.upper()
    if 'LOWER(' in sql_upper and 'ILIKE' in sql_upper:
        return sql_query
    
    def replace_equals(match):
        full_match = match.group(0)
        column = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        if value.replace('.', '').replace('-', '').isdigit():
            return full_match
        
        if any(keyword in value.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'NULL']):
            return full_match
        
        if f"LOWER({column})" in sql_query or f"UPPER({column})" in sql_query:
            return full_match
        
        return f"LOWER({column}) = LOWER({quote}{value}{quote})"
    
    def replace_like(match):
        full_match = match.group(0)
        column = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        if f"LOWER({column})" in sql_query or f"UPPER({column})" in sql_query:
            return full_match
        
        if '%' not in value and '_' not in value:
            return f"{column} LIKE {quote}%{value}%{quote}"
        else:
            return f"{column} LIKE {quote}{value}{quote}"
    
    def replace_in(match):
        full_match = match.group(0)
        column = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        values = [v.strip().strip(quote) for v in value.split(',')]
        lower_values = ', '.join([f"{quote}{v}{quote}" for v in values])
        return f"LOWER({column}) IN ({lower_values})"
    
    pattern1 = r'(\w+)\s*=\s*([\'"])([^\'"]+)\2'
    modified_query = re.sub(pattern1, replace_equals, sql_query, flags=re.IGNORECASE)
    
    pattern2 = r'(\w+)\s+LIKE\s+([\'"])([^\'"]+)\2'
    modified_query = re.sub(pattern2, replace_like, modified_query, flags=re.IGNORECASE)
    
    pattern3 = r'(\w+)\s+IN\s+\(([\'"])([^\)]+)\2\)'
    modified_query = re.sub(pattern3, replace_in, modified_query, flags=re.IGNORECASE)
    
    return modified_query

def schema_to_toon(schema_info: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Convert database schema from JSON format to TOON (Token-Oriented Object Notation) format.
    This reduces token usage by 30-60% while maintaining the same information.
    
    DYNAMIC: Automatically detects all fields present in the schema, so it handles
    any additional fields that might be added in the future.
    
    Example:
    JSON: {"EDC_BRAND": [{"name": "BR_CODE", "type": "int"}, {"name": "BR_DESC", "type": "varchar"}]}
    TOON: EDC_BRAND[2]{name, type, nullable, max_length}:
            BR_CODE, int, false, null
            BR_DESC, varchar, true, 255
    """
    toon_lines = []
    
    for table_name, columns in schema_info.items():
        if not columns:
            continue
        
        # Get column count
        col_count = len(columns)
        
        # DYNAMIC: Get all unique field names from all columns in this table
        # This ensures we handle any fields that might be present, not just hardcoded ones
        field_names = []
        if columns:
            # Collect all unique keys from all columns in this table
            all_keys = set()
            for col in columns:
                all_keys.update(col.keys())
            # Sort for consistent output (put common fields first)
            common_fields = ["name", "type", "nullable", "max_length"]
            field_names = [f for f in common_fields if f in all_keys]
            # Add any other fields that aren't in the common list
            other_fields = sorted([f for f in all_keys if f not in common_fields])
            field_names.extend(other_fields)
        
        # Build TOON header: table_name[count]{field1, field2, ...}:
        header = f"{table_name}[{col_count}]{{{', '.join(field_names)}}}:"
        toon_lines.append(header)
        
        # Add each column as a row
        for col in columns:
            # Extract values in the same order as field_names (DYNAMIC)
            values = []
            for field_name in field_names:
                value = col.get(field_name)
                # Format the value appropriately
                if value is None:
                    values.append("null")
                elif isinstance(value, bool):
                    values.append(str(value).lower())
                else:
                    values.append(str(value))
            
            row = "  " + ", ".join(values)
            toon_lines.append(row)
        
        # Add blank line between tables for readability
        toon_lines.append("")
    
    return "\n".join(toon_lines).strip()

def contains_write_operation(user_query: str) -> Tuple[bool, Optional[str]]:
    """Check if user query contains write operation keywords - block before LLM call"""
    if not user_query:
        return False, None
    
    query_lower = user_query.lower().strip()
    
    # Write operation keywords and phrases
    write_keywords = [
        'delete', 'remove', 'erase', 'clear', 'truncate', 'drop', 'destroy',
        'insert', 'add', 'create', 'new', 'make', 'build',
        'update', 'modify', 'change', 'edit', 'alter', 'set',
        'grant', 'revoke', 'permission', 'access',
        'backup', 'restore', 'export', 'import',
        'execute', 'exec', 'run procedure', 'stored procedure'
    ]
    
    # Check for write operation keywords
    for keyword in write_keywords:
        if keyword in query_lower:
            # Check if it's part of a read operation (e.g., "show deleted items")
            read_contexts = [
                'show', 'list', 'display', 'find', 'get', 'view', 'see',
                'count', 'how many', 'what', 'which', 'where', 'give', 'tell'
            ]
            # Check if a read keyword appears before the write keyword
            keyword_index = query_lower.find(keyword)
            before_keyword = query_lower[:keyword_index] if keyword_index > 0 else ""
            
            # If it's clearly a write operation (not a read query about write operations)
            if not any(read_context in before_keyword for read_context in read_contexts):
                return True, keyword
    
    return False, None

def is_valid_database_query(user_query: str) -> bool:
    """Check if the user query is a valid database query request"""
    if not user_query or len(user_query.strip()) < 3:
        return False
    
    query_lower = user_query.lower().strip()
    
    if len(query_lower) < 3:
        return False
    
    db_keywords = [
        'show', 'list', 'get', 'find', 'select', 'count', 'how many', 'what', 'which',
        'where', 'who', 'when', 'display', 'fetch', 'retrieve', 'query', 'search',
        'filter', 'sort', 'order', 'group', 'sum', 'average', 'avg', 'max', 'min',
        'all', 'top', 'bottom', 'first', 'last', 'users', 'customers', 'orders',
        'products', 'data', 'table', 'records', 'rows', 'columns', 'brand', 'category',
        'product', 'stock', 'vikas'
    ]
    
    has_db_keyword = any(keyword in query_lower for keyword in db_keywords)
    
    if not has_db_keyword and len(query_lower) < 10:
        return False
    
    non_query_patterns = [
        'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
        'gg', 'lol', 'haha', 'ok', 'okay', 'yes', 'no', 'maybe'
    ]
    
    if query_lower in non_query_patterns or (len(query_lower) < 5 and not has_db_keyword):
        return False
    
    return True

def generate_sql_query(user_query: str, conversation_history: List[ChatMessage], model: str = "gpt-4o-mini") -> str:
    """Generate SQL query using OpenAI GPT-4"""
    try:
        # Check for write operations BEFORE calling LLM (saves API costs)
        has_write_op, write_keyword = contains_write_operation(user_query)
        if has_write_op:
            return "READ_ONLY_ERROR"
        
        if not is_valid_database_query(user_query):
            return None
        
        schema_info = get_table_schema()
        # Convert schema to TOON format for 30-60% token reduction
        schema_text = schema_to_toon(schema_info)
        
        # Use same prompt structure as GPT for Ollama, but with full schema
        if model == "llama3.2:1b" or model == "llama":
            # Use TOON format (same as GPT now)
            # Limit schema size slightly to avoid timeouts, but keep full structure
            schema_display = schema_text[:4000] if len(schema_text) > 4000 else schema_text
            
            # Use the SAME prompt structure as GPT, just ensure it outputs SQL only
            system_prompt = f"""You are a SQL query generator. Your ONLY job is to convert user questions into SQL SELECT queries.

CRITICAL: DO NOT answer the user's question directly. DO NOT provide explanations. ONLY output the SQL query.

Database Schema (TOON format - this is METADATA, not SQL syntax):
The schema below shows table structures in TOON format. This is just metadata describing columns - DO NOT use TOON syntax in your SQL queries.

Format: table_name[column_count]{{field_names}}:
  column_name, data_type, nullable, max_length
  column_name, data_type, nullable, max_length

IMPORTANT: The TOON format (with brackets and braces) is ONLY for showing you the schema structure. When writing SQL, use normal SQL syntax like: SELECT * FROM [table_name] WHERE column_name = 'value'

{schema_display}

Rules:
1. **YOU MUST OUTPUT ONLY SQL CODE. NO TEXT, NO EXPLANATIONS, NO ANSWERS TO THE QUESTION.**
2. Start your response with SELECT (not with text or explanations)
3. Use SQL Server (T-SQL) syntax
4. Use EXACT column names from the schema above
5. For aggregation queries, use appropriate GROUP BY clauses
6. Always use proper JOIN syntax when needed
7. **CRITICAL: READ-ONLY ACCESS ONLY** - Only SELECT queries allowed
8. Use TOP instead of LIMIT for limiting results
9. Use square brackets [] around table/column names if they contain special characters
10. Always use case-insensitive matching for text searches (LOWER() or LIKE with COLLATE)

Examples:
- "Show me all brands" -> SELECT TOP 100 * FROM [EDC_BRAND];
- "How many products are there?" -> SELECT COUNT(*) FROM [EDC_PRODUCT];
- "List products with their categories" -> SELECT TOP 100 p.PR_CODE, p.PR_DESC, c.CT_DESC FROM [EDC_PRODUCT] p LEFT JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE;
- "Find all brands with SAS" -> SELECT * FROM [EDC_BRAND] WHERE LOWER(BR_DESC) = LOWER('SAS') OR BR_DESC LIKE '%SAS%';
- "Show me products with brand and category information and prices" -> SELECT TOP 100 p.PR_CODE, p.PR_DESC, b.BR_DESC, c.CT_DESC, p.PR_SELLING_PRICE FROM [EDC_PRODUCT] p LEFT JOIN [EDC_BRAND] b ON p.PR_PT_CODE = b.BR_CODE LEFT JOIN [EDC_CATEGORY] c ON p.PR_DIV_CODE = c.CT_CODE;
- "What is the average selling price for each brand?" -> SELECT b.BR_CODE, b.BR_DESC, AVG(p.PR_SELLING_PRICE) AS Average_Selling_Price FROM [EDC_BRAND] b JOIN [EDC_PRODUCT] p ON b.BR_CODE = p.PR_PT_CODE GROUP BY b.BR_CODE, b.BR_DESC;
- "Delete all brands" -> READ_ONLY_ERROR
- "Update product prices" -> READ_ONLY_ERROR
- "Drop table EDC_BRAND" -> READ_ONLY_ERROR

REMEMBER: Output ONLY the SQL query. No explanations, no markdown, no text. Just the SQL statement."""
        else:
            # Full prompt for OpenAI
            system_prompt = f"""You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.

Database Schema (TOON format - this is METADATA, not SQL syntax):
The schema below shows table structures in TOON format. This is just metadata describing columns - use normal SQL syntax in your queries.

Format: table_name[column_count]{{field_names}}:
  column_name, data_type, nullable, max_length
  column_name, data_type, nullable, max_length

IMPORTANT: The TOON format (with brackets and braces) is ONLY for showing you the schema structure. When writing SQL, use normal SQL syntax like: SELECT * FROM [table_name] WHERE column_name = 'value'

{schema_text}

Rules:
1. Generate ONLY the SQL query, no explanations or markdown
2. Use SQL Server (T-SQL) syntax
3. Be precise and efficient
4. If the question is unclear, make reasonable assumptions based on the schema
5. For aggregation queries, use appropriate GROUP BY clauses
6. Always use proper JOIN syntax when needed
7. If the question cannot be converted to a meaningful SQL query, return "INVALID_QUERY"
8. **CRITICAL: READ-ONLY ACCESS ONLY**
   - You can ONLY generate SELECT queries
   - NEVER generate DELETE, TRUNCATE, DROP, INSERT, UPDATE, ALTER, CREATE, or any write operations
   - If the user asks to delete, update, modify, or change data, return "READ_ONLY_ERROR" instead of a query
   - The database has read-only access - only SELECT statements are allowed
9. **IMPORTANT: Always use case-insensitive matching for text searches**
   - Use LIKE with COLLATE for case-insensitive pattern matching: column_name LIKE '%search%' COLLATE SQL_Latin1_General_CP1_CI_AS
   - Or use LOWER() function for case-insensitive comparisons: LOWER(column_name) = LOWER('search_term')
   - When searching for text fields, always make the search case-insensitive
   - Example: WHERE LOWER(BR_DESC) = LOWER('SAS') OR BR_DESC LIKE '%SAS%'
   - This ensures users can search with any case combination and still get results
10. Use TOP instead of LIMIT for limiting results
11. Use square brackets [] around table/column names if they contain special characters

Examples:
- "Show me all brands" -> SELECT TOP 100 * FROM [EDC_BRAND];
- "How many products are there?" -> SELECT COUNT(*) FROM [EDC_PRODUCT];
- "List products with their categories" -> SELECT TOP 100 p.PR_CODE, p.PR_DESC, c.CT_DESC FROM [EDC_PRODUCT] p LEFT JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE;
- "Find all brands with SAS" -> SELECT * FROM [EDC_BRAND] WHERE LOWER(BR_DESC) = LOWER('SAS') OR BR_DESC LIKE '%SAS%';
- "Delete all brands" -> READ_ONLY_ERROR
- "Update product prices" -> READ_ONLY_ERROR
- "Drop table EDC_BRAND" -> READ_ONLY_ERROR
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in conversation_history[-5:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_query})
        
        # Use the model service to generate SQL
        # For Ollama, use more tokens for complex queries (JOINs, aggregations)
        # Check if query is complex (contains multiple entities or aggregations)
        is_complex = any(word in user_query.lower() for word in ['with', 'and', 'each', 'average', 'sum', 'count', 'group', 'join'])
        max_tokens_for_model = 400 if (model == "llama3.2:1b" or model == "llama" and is_complex) else (300 if (model == "llama3.2:1b" or model == "llama") else 500)
        sql_query = generate_sql_with_model(model, messages, temperature=0.3, max_tokens=max_tokens_for_model)
        
        # Extract SQL from response (handle cases where model returns text + SQL)
        # For Ollama, be more aggressive in extracting SQL
        if model == "llama3.2:1b" or model == "llama":
            # If response doesn't start with SELECT, try to extract it
            if not sql_query.strip().upper().startswith("SELECT"):
                sql_query = extract_sql_from_response(sql_query)
                # If still no SELECT, it's likely text - return error
                if not sql_query.strip().upper().startswith("SELECT"):
                    raise Exception("Model returned text instead of SQL. Please ensure the query is a valid SQL SELECT statement.")
        else:
            sql_query = extract_sql_from_response(sql_query)
        
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Additional cleanup for Ollama responses that might include explanations
        if model == "llama3.2:1b" or model == "llama":
            # Remove any text before SELECT
            if "SELECT" in sql_query.upper():
                select_index = sql_query.upper().find("SELECT")
                sql_query = sql_query[select_index:]
            # Remove any text after semicolon or newline
            if ";" in sql_query:
                sql_query = sql_query[:sql_query.index(";") + 1]
            # Remove trailing explanations
            lines = sql_query.split("\n")
            sql_lines = []
            for line in lines:
                line = line.strip()
                if line.upper().startswith("SELECT") or line.upper().startswith("FROM") or line.upper().startswith("WHERE") or line.upper().startswith("ORDER") or line.upper().startswith("GROUP") or line.upper().startswith("HAVING") or line.upper().startswith("JOIN") or line.upper().startswith("LEFT") or line.upper().startswith("RIGHT") or line.upper().startswith("INNER") or line.upper().startswith("OUTER") or line.upper().startswith("UNION") or line.upper().startswith("WITH") or line.startswith("[") or line.startswith("(") or line.startswith(")") or line == ";" or line == "":
                    sql_lines.append(line)
                elif any(keyword in line.upper() for keyword in ["COUNT", "SUM", "AVG", "MAX", "MIN", "TOP", "DISTINCT", "AS", "ON", "AND", "OR", "IN", "LIKE", "BETWEEN", "IS", "NULL"]):
                    sql_lines.append(line)
                else:
                    # Stop at first non-SQL line
                    break
            sql_query = " ".join(sql_lines).strip()
        
        sql_query = make_case_insensitive(sql_query)
        sql_query = sql_query.replace('ILIKE', 'LIKE')
        
        # Ensure COUNT(*) has an alias if missing (fixes display issues)
        if "COUNT(*)" in sql_query.upper() and " AS " not in sql_query.upper() and "COUNT(*) AS" not in sql_query.upper():
            # Add alias for COUNT(*) if missing
            sql_query = sql_query.replace("COUNT(*)", "COUNT(*) as count").replace("count(*)", "COUNT(*) as count")
        
        return sql_query
    except Exception as e:
        raise Exception(f"Error generating SQL: {str(e)}")

def is_read_only_query(sql_query: str) -> Tuple[bool, Optional[str]]:
    """Check if SQL query is read-only (SELECT only) and safe to execute"""
    sql_upper = sql_query.strip().upper()
    
    # Remove comments and strings to check for hidden dangerous keywords
    import re
    # Remove SQL comments (-- and /* */)
    sql_no_comments = re.sub(r'--.*?$', '', sql_query, flags=re.MULTILINE)
    sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
    sql_no_comments_upper = sql_no_comments.upper()
    
    # List of dangerous write operations
    dangerous_keywords = [
        'DELETE', 'TRUNCATE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 
        'CREATE', 'EXEC', 'EXECUTE', 'SP_', 'XP_', 'GRANT', 'REVOKE',
        'MERGE', 'BULK INSERT', 'BACKUP', 'RESTORE', 'DBCC'
    ]
    
    # Check if query starts with SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed. You have read-only access to the database."
    
    # Check for dangerous keywords anywhere in the query
    for keyword in dangerous_keywords:
        if keyword in sql_no_comments_upper:
            return False, f"Write operations like '{keyword}' are not allowed. You have read-only access to the VikasAI database."
    
    # Additional check for semicolon-separated multiple statements
    if ';' in sql_query and sql_query.count(';') > 1:
        return False, "Multiple statements are not allowed. You have read-only access to the database."
    
    return True, None

def execute_sql_query(sql_query: str) -> Tuple[List[dict], Optional[str]]:
    """Execute SQL query on SQL Server and return results (READ-ONLY)"""
    try:
        # Validate query is read-only
        is_safe, error_msg = is_read_only_query(sql_query)
        if not is_safe:
            return None, error_msg
        
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        
        sql_query = sql_query.replace('ILIKE', 'LIKE')
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        data = [dict(zip(columns, row)) for row in results]
        
        cursor.close()
        conn.close()
        
        return data, None
    except Exception as e:
        return None, f"SQL execution error: {str(e)}"

