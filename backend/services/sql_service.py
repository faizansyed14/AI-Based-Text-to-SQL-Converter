"""Service for SQL query generation and execution"""
import json
import re
import sys
import os
import logging
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Optional, Tuple, Dict, Any
from openai import OpenAI
from models.schemas import ChatMessage
from database.sqlserver import get_sqlserver_connection
from services.schema_service import get_table_schema
from services.model_service import generate_sql_with_model

# Set up logging
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_sql_from_response(response: str) -> str:
    """Extract SQL query from model response, handling cases where model returns text + SQL"""
    if not response:
        return ""
    
    response = response.strip()
    
    # Remove common explanatory prefixes that models sometimes add
    explanatory_prefixes = [
        "here is the sql query:",
        "here's the sql:",
        "the sql query is:",
        "sql query:",
        "query:",
        "sql:",
    ]
    for prefix in explanatory_prefixes:
        if response.lower().startswith(prefix):
            response = response[len(prefix):].strip()
    
    # Check if response contains WITH (CTE) or SELECT
    response_upper = response.upper()
    has_with = "WITH" in response_upper
    has_select = "SELECT" in response_upper
    
    if has_with or has_select:
        # If it starts with WITH, find the WITH keyword
        if has_with:
            with_index = response_upper.find("WITH")
            # Check if WITH appears before SELECT (it should for CTEs)
            if has_select:
                select_index = response_upper.find("SELECT")
                if with_index < select_index:
                    # WITH comes first, start from WITH
                    sql_part = response[with_index:]
                else:
                    # SELECT comes first, start from SELECT
                    sql_part = response[select_index:]
            else:
                # Only WITH, no SELECT (unusual but possible)
                sql_part = response[with_index:]
        else:
            # Only SELECT, no WITH
            select_index = response_upper.find("SELECT")
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
                if line_stripped.lower().startswith(("there are", "the query", "this will", "note:", "warning:", "error:", "the result", "this query", "allowed", "permitted", "read-only")):
                    break
                # Stop if line doesn't look like SQL
                if not any(keyword in line_stripped.upper() for keyword in ["WITH", "SELECT", "FROM", "WHERE", "JOIN", "ORDER", "GROUP", "HAVING", "COUNT", "SUM", "AVG", "MAX", "MIN", "TOP", "DISTINCT", "AS", "ON", "AND", "OR", "IN", "LIKE", "BETWEEN", "IS", "NULL", "[", "]", "(", ")", ";", ",", "=", "<", ">", "!"]):
                    if len(sql_lines) > 0:  # Only stop if we already have some SQL
                        break
                sql_lines.append(line)
            sql_part = " ".join(sql_lines).strip()
        
        # Ensure we have a valid SQL statement (WITH or SELECT)
        if not (sql_part.upper().startswith("WITH") or sql_part.upper().startswith("SELECT")):
            # Try to find WITH or SELECT in the extracted part
            with_pos = sql_part.upper().find("WITH")
            select_pos = sql_part.upper().find("SELECT")
            if with_pos >= 0 and (select_pos < 0 or with_pos < select_pos):
                sql_part = sql_part[with_pos:]
            elif select_pos >= 0:
                sql_part = sql_part[select_pos:]
            else:
                # If no WITH or SELECT found, return empty (invalid SQL)
                return ""
        
        return sql_part
    
    return response

def make_case_insensitive(sql_query: str) -> str:
    """Post-process SQL query to ensure case-insensitive text comparisons in WHERE clauses only"""
    import re
    
    sql_upper = sql_query.upper()
    if 'LOWER(' in sql_upper and 'ILIKE' in sql_upper:
        return sql_query
    
    # Only modify WHERE clauses, not SELECT clauses
    # Split the query into parts: before WHERE, WHERE clause, and after WHERE
    where_match = re.search(r'\bWHERE\b', sql_query, re.IGNORECASE)
    if not where_match:
        # No WHERE clause, return as-is
        return sql_query
    
    # Split query at WHERE
    before_where = sql_query[:where_match.start()]
    where_clause_and_after = sql_query[where_match.start():]
    
    # Find the end of WHERE clause (before ORDER BY, GROUP BY, HAVING, UNION, etc.)
    where_end_pattern = r'\b(ORDER\s+BY|GROUP\s+BY|HAVING|UNION|INTERSECT|EXCEPT)\b'
    where_end_match = re.search(where_end_pattern, where_clause_and_after, re.IGNORECASE)
    
    if where_end_match:
        where_clause = where_clause_and_after[:where_end_match.start()]
        after_where = where_clause_and_after[where_end_match.start():]
    else:
        where_clause = where_clause_and_after
        after_where = ""
    
    def replace_equals(match):
        full_match = match.group(0)
        column = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        if value.replace('.', '').replace('-', '').isdigit():
            return full_match
        
        if any(keyword in value.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'NULL']):
            return full_match
        
        if f"LOWER({column})" in where_clause or f"UPPER({column})" in where_clause:
            return full_match
        
        return f"LOWER({column}) = LOWER({quote}{value}{quote})"
    
    def replace_like(match):
        full_match = match.group(0)
        column = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        
        if f"LOWER({column})" in where_clause or f"UPPER({column})" in where_clause:
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
    
    # Only modify the WHERE clause
    pattern1 = r'(\w+)\s*=\s*([\'"])([^\'"]+)\2'
    modified_where = re.sub(pattern1, replace_equals, where_clause, flags=re.IGNORECASE)
    
    pattern2 = r'(\w+)\s+LIKE\s+([\'"])([^\'"]+)\2'
    modified_where = re.sub(pattern2, replace_like, modified_where, flags=re.IGNORECASE)
    
    pattern3 = r'(\w+)\s+IN\s+\(([\'"])([^\)]+)\2\)'
    modified_where = re.sub(pattern3, replace_in, modified_where, flags=re.IGNORECASE)
    
    # Reconstruct the query
    return before_where + modified_where + after_where

def schema_to_json(schema_info: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Convert database schema to JSON format string.
    
    Example:
    {"EDC_BRAND": [{"name": "BR_CODE", "type": "int", "nullable": false}, {"name": "BR_DESC", "type": "varchar", "nullable": true, "max_length": 255}]}
    """
    return json.dumps(schema_info, indent=2)

def contains_write_operation(user_query: str) -> Tuple[bool, Optional[str]]:
    """
    Check if user query contains write operation keywords - block before LLM call.
    Only blocks when keywords are used as explicit SQL commands.
    Natural language questions are allowed even if they contain these words.
    """
    if not user_query:
        return False, None
    
    query_lower = user_query.lower().strip()
    
    # Only block if the query explicitly looks like a SQL write command
    # Check for patterns like "DELETE FROM", "UPDATE table", "INSERT INTO", etc.
    sql_write_patterns = [
        r'\bdelete\s+from\b',
        r'\bupdate\s+\w+\s+set\b',
        r'\binsert\s+into\b',
        r'\btruncate\s+table\b',
        r'\bdrop\s+table\b',
        r'\bdrop\s+database\b',
        r'\balter\s+table\b',

    ]
    
    import re
    for pattern in sql_write_patterns:
        if re.search(pattern, query_lower):
            return True, pattern
    
    # Special handling for 'execute' - only block if it's not "execute this query" with SELECT
    if query_lower.startswith('execute'):
        # Check if it's "execute this query" followed by SELECT
        if 'select' in query_lower and ('this query' in query_lower or 'query' in query_lower):
            # This is likely "Execute this query and show all results: SELECT..."
            # Don't block it, let it through
            return False, None
        # Otherwise, check if it looks like a SQL command
        if 'procedure' in query_lower or 'exec' in query_lower:
            return True, 'execute'
    
    # Don't block natural language questions - let the LLM handle them
    # The LLM will generate appropriate SQL or clarification
    return False, None

def is_valid_database_query(user_query: str) -> bool:
    """Check if the user query is a valid database query request - only filter obvious non-queries"""
    if not user_query or len(user_query.strip()) < 2:
        return False
    
    query_lower = user_query.lower().strip()
    
    # Only filter obvious greetings and non-queries
    non_query_patterns = [
        'hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye',
        'gg', 'lol', 'haha', 'ok', 'okay'
    ]
    
    # Reject if it's just a greeting or very short casual response
    if query_lower in non_query_patterns:
        return False
    
    # Everything else is accepted - let the LLM handle it
    return True

def generate_sql_query(user_query: str, conversation_history: List[ChatMessage], model: str = "gpt-4o-mini") -> str:
    """Generate SQL query using OpenAI GPT-4"""
    try:
        # Check for write operations BEFORE calling LLM (saves API costs)
        # Note: This is a lightweight check. Final validation happens in is_read_only_query()
        # which checks the actual SQL query generated by the LLM
        has_write_op, write_keyword = contains_write_operation(user_query)
        if has_write_op:
            # Only block if it's clearly a write command, not if keyword is part of field name
            return "READ_ONLY_ERROR"
        
        if not is_valid_database_query(user_query):
            return None
        
        schema_info = get_table_schema()
        # Convert schema to JSON format
        schema_text = schema_to_json(schema_info)
        
        # Log the prompt being sent to LLM including the schema
        logger.info("=" * 80)
        logger.info(f"📤 Sending prompt to LLM (Model: {model})")
        logger.info(f"📝 User Query: {user_query}")
        logger.info(f"📊 Schema (JSON):\n{schema_text}")
        logger.info("=" * 80)
        
        # Full prompt for OpenAI GPT models
        system_prompt = f"""You are an intelligent assistant that helps users with database queries and general questions. Your primary job is to convert natural language database questions to SQL, but you can also answer logical questions, explain differences, and provide helpful information.

Database Schema (JSON format):
The schema below shows table structures in JSON format. Each table contains columns with their names, data types, and detailed descriptions. This is metadata describing columns - use normal SQL syntax in your queries.

IMPORTANT: Each column has a "description" field that explains what the column represents. Use these descriptions to understand the meaning and purpose of each column when generating SQL queries.

{schema_text}

IMPORTANT INSTRUCTIONS:
1. **Handle Different Types of Questions**:
   - **Database queries**: Convert to SQL and return ONLY the SQL query (no text)
   - **Logical/comparison questions**: Answer directly with explanation (e.g., "what is the difference between X and Y")
   - **General questions**: Answer helpfully if you can, or return "CLARIFICATION_NEEDED:" if you need more info
   - **Excel/formula questions**: Provide helpful Excel formula guidance

2. **Handle Typos and Mistakes Dynamically**: Users don't know exact column/table names. Use fuzzy matching and best guesses:
   - If user says "product" but schema has "PR_DESC" or "EDC_PRODUCT", match intelligently
   - If column name is slightly wrong (e.g., "brand" vs "BR_DESC"), use the closest match from schema
   - **CRITICAL: Use column descriptions to understand what each column means** - the "description" field in the schema tells you what each column represents
   - Match user's intent to column descriptions, not just column names
   - Example: If user asks for "selling price" and you see a column "PR_SELLING_PRICE" with description "Selling price", use that column
   - Look at the schema context and descriptions to understand what the user likely means

3. **Ask Clarifying Questions Only When Truly Ambiguous**: 
   - If the query is clear enough to generate SQL, do it
   - Only ask for clarification if you genuinely cannot determine what the user wants
   - **For Excel/calculation questions**: If user asks about Excel formulas or calculations, offer to help them do it on the database instead. Return "LOGICAL_ANSWER: [Excel formula explanation]. Would you like me to perform this calculation on your database instead? Please specify which table and column contain the dates."
   - Examples:
     - User: "show table" -> "CLARIFICATION_NEEDED: Which table would you like to see? Available tables: [list tables from schema]"
     - User: "show columns" -> "CLARIFICATION_NEEDED: Which table's columns would you like to see? Please specify the table name."
     - User: "what is the total stock on hold" -> Generate SQL (clear enough - sum of stock on hand)
     - User: "what is the total of each stock on hold" -> Generate SQL with GROUP BY (clear enough - per product breakdown)
     - User: "calculate average age in Excel" -> "LOGICAL_ANSWER: [Excel formula]. Would you like me to calculate the average age from your database instead? Please specify which table and date column you'd like to use."

4. **Response Format**:
   - **For database queries**: Return ONLY the SQL query, no text
   - **For logical/comparison questions**: Return "LOGICAL_ANSWER: [your explanation]"
   - **For clarification needed**: Return "CLARIFICATION_NEEDED: [your question]"
   - **For write operations**: Return "READ_ONLY_ERROR"
   - **For truly invalid**: Return "INVALID_QUERY"

5. **SQL Generation Rules**:
   - Use SQL Server (T-SQL) syntax
   - Use square brackets [] around table/column names if they contain special characters
   - Use EXACT column/table names from the schema (after matching user's intent)
   - For aggregation queries, use appropriate GROUP BY clauses
   - **ALWAYS use proper JOIN syntax** (INNER JOIN, LEFT JOIN, RIGHT JOIN) - avoid old-style comma-separated FROM clauses
   - For multiple table queries, use explicit JOINs with ON conditions
   - **NO TOP LIMIT unless user specifically asks for limited results** - return ALL results by default
   - If user says "all" or doesn't specify a limit, don't use TOP clause
   - **For complex queries with multiple tables**: Use proper JOIN syntax, not comma-separated tables
   - **For string functions**: Use SUBSTRING() instead of SUBSTR(), ISNULL() instead of NVL(), GETDATE() instead of SYSDATE
   - **For date functions**: Use CONVERT(DATE, column) or CAST(column AS DATE) instead of TRUNC() for dates
   - **For conditional logic**: Use CASE WHEN or proper WHERE conditions with AND/OR

6. **Case-Insensitive Matching**:
   - Always use case-insensitive matching for text searches
   - Use LOWER() function: LOWER(column_name) = LOWER('search_term')
   - Or LIKE with COLLATE: column_name LIKE '%search%' COLLATE SQL_Latin1_General_CP1_CI_AS

7. **READ-ONLY ACCESS ONLY**:
   - ONLY generate SELECT queries
   - NEVER generate DELETE, TRUNCATE, DROP, INSERT, UPDATE, ALTER, CREATE, or any write operations
   - If user asks to delete/update/modify, return "READ_ONLY_ERROR"

Examples:
- "Show me all brands" -> SELECT * FROM [EDC_BRAND];
- "Show all products" -> SELECT * FROM [EDC_PRODUCT];
- "Show me top 10 products" -> SELECT TOP 10 * FROM [EDC_PRODUCT];
- "How many products are there?" -> SELECT COUNT(*) as count FROM [EDC_PRODUCT];
- "List products with their categories" -> SELECT p.PR_CODE, p.PR_DESC, c.CT_DESC FROM [EDC_PRODUCT] p LEFT JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE;
- "Find all brands with SAS" -> SELECT * FROM [EDC_BRAND] WHERE LOWER(BR_DESC) = LOWER('SAS') OR BR_DESC LIKE '%SAS%';

**Complex Multi-Table Query Examples:**
- "Show stock age with product details and brand" -> 
  SELECT sa.SA_PR_CODE AS PRODUCT_CODE, c.CT_DESC AS PRODUCT_TAG, p.PR_DESC AS DESCRIPTION, 
         sa.SA_STOCK_QTY AS stock_qty, p.PR_FREE_QTY AS free_qty, sa.SA_UNIT_COST AS unit_price,
         sa.SA_STOCK_QTY * sa.SA_UNIT_COST AS Total_Value, b.BR_DESC AS brand
  FROM [STR_STOCK_AGE] sa
  INNER JOIN [EDC_PRODUCT] p ON sa.SA_PR_CODE = p.PR_CODE
  INNER JOIN [EDC_BRAND] b ON SUBSTRING(p.PR_CODE, 1, 3) = b.BR_CODE
  LEFT JOIN [EDC_CATEGORY] c ON c.CT_CODE = p.PR_PT_CODE;

**IMPORTANT - Available Tables:**
The database contains these tables: EDC_BRAND, EDC_CATEGORY, EDC_PRODUCT, EDC_PROD_DESC, STR_STOCK_CARD
- **EDC_CATEGORY** (NOT EDC_PRODUCT_TAG) - contains category/tag information with CT_CODE and CT_DESC columns
- Product category/tag is linked via PR_PT_CODE in EDC_PRODUCT joining to CT_CODE in EDC_CATEGORY
- When user asks for "product tag", use EDC_CATEGORY table with CT_DESC column
- When user asks for "stock age", check if STR_STOCK_AGE table exists, otherwise use STR_STOCK_CARD with date calculations

- "Show products with brand and category filtered by division" ->
  SELECT p.PR_CODE, p.PR_DESC, b.BR_DESC, c.CT_DESC
  FROM [EDC_PRODUCT] p
  LEFT JOIN [EDC_BRAND] b ON SUBSTRING(p.PR_CODE, 1, 3) = b.BR_CODE
  LEFT JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE
  WHERE p.PR_DIV_CODE LIKE '%' OR p.PR_DIV_CODE IS NULL;

- "Show stock card data with product code, category description, product description, stock quantity, free quantity, unit cost, total value, and brand" ->
  SELECT sa.SCD_PR_CODE AS PRODUCT_CODE, c.CT_DESC AS PRODUCT_TAG, p.PR_DESC AS DESCRIPTION,
         (sa.SCD_RCPT_QTY - sa.SCD_ISSUE_QTY) AS stock_qty, p.PR_FREE_QTY AS free_qty,
         sa.SCD_UNIT_COST AS unit_price,
         (sa.SCD_RCPT_QTY - sa.SCD_ISSUE_QTY) * sa.SCD_UNIT_COST AS Total_Value,
         b.BR_DESC AS brand
  FROM [STR_STOCK_CARD] sa
  INNER JOIN [EDC_PRODUCT] p ON sa.SCD_PR_CODE = p.PR_CODE
  LEFT JOIN [EDC_BRAND] b ON SUBSTRING(p.PR_CODE, 1, 3) = b.BR_CODE
  LEFT JOIN [EDC_CATEGORY] c ON c.CT_CODE = p.PR_PT_CODE
  WHERE (sa.SCD_RCPT_QTY - sa.SCD_ISSUE_QTY) > 0;

**Important for Complex Queries:**
- When user asks for data from multiple tables (e.g., "products with brands", "stock with product details"), use JOINs
- Match tables by common columns (codes, IDs) found in the schema
- Use SUBSTRING() for partial code matching (e.g., first 3 characters of product code = brand code)
- Use ISNULL() or COALESCE() for NULL handling instead of NVL()
- Use CONVERT(DATE, column) for date truncation instead of TRUNC()
- For conditional age ranges, use CASE WHEN or WHERE conditions with BETWEEN
- **CRITICAL: Only use tables that exist in the schema** - Check available tables: EDC_BRAND, EDC_CATEGORY, EDC_PRODUCT, EDC_PROD_DESC, STR_STOCK_CARD
- **Product Tag = Category**: When user asks for "product tag", use EDC_CATEGORY table (CT_DESC column), NOT EDC_PRODUCT_TAG (doesn't exist)
- **Stock Age**: If STR_STOCK_AGE table doesn't exist, use STR_STOCK_CARD and calculate age from SCD_TRANSACTION_DATE
- **Stock Quantity**: In STR_STOCK_CARD, stock quantity = SCD_RCPT_QTY - SCD_ISSUE_QTY (receipt minus issue)
- "What was the oldest and newest product?" -> SELECT * FROM [EDC_PRODUCT] WHERE [PR_CREATED_DATE] = (SELECT MIN([PR_CREATED_DATE]) FROM [EDC_PRODUCT]) OR [PR_CREATED_DATE] = (SELECT MAX([PR_CREATED_DATE]) FROM [EDC_PRODUCT]) OR [PR_UPDATED_DATE] = (SELECT MIN([PR_UPDATED_DATE]) FROM [EDC_PRODUCT] WHERE [PR_UPDATED_DATE] IS NOT NULL) OR [PR_UPDATED_DATE] = (SELECT MAX([PR_UPDATED_DATE]) FROM [EDC_PRODUCT] WHERE [PR_UPDATED_DATE] IS NOT NULL);
- "show table" -> "CLARIFICATION_NEEDED: Which table would you like to see? Available tables: EDC_BRAND, EDC_PRODUCT, EDC_CATEGORY, etc."
- "show columns" -> "CLARIFICATION_NEEDED: Which table's columns would you like to see? Please specify the table name."
- "show all" -> "CLARIFICATION_NEEDED: What would you like to see? Please specify: all tables, all products, all brands, etc."
- "Delete all brands" -> "READ_ONLY_ERROR"

**Stock Card (STR_STOCK_CARD) Specific Examples:**
- "Show stock with balance" -> SELECT SCD_PR_CODE, SCD_PR_DESC, SCD_TRANSACTION_DATE, (SCD_RCPT_QTY - SCD_ISSUE_QTY) AS Balance FROM [STR_STOCK_CARD] WHERE (SCD_RCPT_QTY - SCD_ISSUE_QTY) > 0;
- "Calculate median age of stock" -> WITH StockAges AS (SELECT DATEDIFF(day, SCD_TRANSACTION_DATE, GETDATE()) AS Age FROM [STR_STOCK_CARD] WHERE SCD_TRANSACTION_DATE IS NOT NULL AND (SCD_RCPT_QTY - SCD_ISSUE_QTY) > 0), OrderedAges AS (SELECT Age, ROW_NUMBER() OVER (ORDER BY Age) AS RowNum, COUNT(*) OVER () AS TotalCount FROM StockAges) SELECT AVG(CAST(Age AS FLOAT)) AS MedianAge FROM OrderedAges WHERE RowNum IN ((TotalCount + 1) / 2, (TotalCount + 2) / 2);
- "Total cost value of stock on hand" -> SELECT SUM((SCD_RCPT_QTY - SCD_ISSUE_QTY) * SCD_UNIT_COST) AS TotalCostValue FROM [STR_STOCK_CARD] WHERE (SCD_RCPT_QTY - SCD_ISSUE_QTY) > 0 AND SCD_UNIT_COST IS NOT NULL;
- "Average age of stock" -> SELECT AVG(DATEDIFF(day, SCD_TRANSACTION_DATE, GETDATE())) AS AverageAgeInDays FROM [STR_STOCK_CARD] WHERE SCD_TRANSACTION_DATE IS NOT NULL AND (SCD_RCPT_QTY - SCD_ISSUE_QTY) > 0;

**Important Notes for Stock Calculations:**
- Stock balance = SCD_RCPT_QTY - SCD_ISSUE_QTY (receipt minus issue)
- Stock age = DATEDIFF(day, SCD_TRANSACTION_DATE, GETDATE()) (days between transaction date and today)
- For median calculations, use CTE (Common Table Expression) with ROW_NUMBER() and handle even/odd counts
- For cost calculations, multiply balance by SCD_UNIT_COST: (SCD_RCPT_QTY - SCD_ISSUE_QTY) * SCD_UNIT_COST
- Always filter out zero or negative balances: WHERE (SCD_RCPT_QTY - SCD_ISSUE_QTY) > 0

IMPORTANT: When user asks for BOTH extremes (e.g., "oldest AND newest", "highest AND lowest", "first AND last"), return BOTH records:
- Use UNION ALL or OR conditions to return multiple records
- For "oldest and newest": Return records with MIN date AND MAX date
- For "highest and lowest": Return records with MAX value AND MIN value
- Always return ALL requested extremes, not just one
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in conversation_history[-5:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_query})
        
        # Log the full messages being sent
        logger.info(f"💬 Full messages being sent to LLM:\n{json.dumps(messages, indent=2)}")
        
        # Use the model service to generate SQL
        # Check if query is complex (contains multiple entities or aggregations) for token allocation
        is_complex = any(word in user_query.lower() for word in ['with', 'and', 'each', 'average', 'sum', 'count', 'group', 'join'])
        max_tokens_for_model = 600 if is_complex else 500
        response = generate_sql_with_model(model, messages, temperature=0.3, max_tokens=max_tokens_for_model)
        
        # Check if response is a clarification request
        response_stripped = response.strip()
        if response_stripped.startswith("CLARIFICATION_NEEDED:"):
            logger.info(f"✅ Clarification request detected: {response_stripped[:100]}")
            return response_stripped  # Return the clarification question as-is
        
        # Check if response is a logical answer (explanation, comparison, etc.)
        if response_stripped.startswith("LOGICAL_ANSWER:"):
            logger.info(f"✅ Logical answer detected: {response_stripped[:100]}")
            return response_stripped  # Return the logical answer as-is
        
        # Check if response contains SQL keywords - if not, it's likely a text answer (Excel formula, explanation, etc.)
        has_sql_keywords = any(keyword in response_stripped.upper() for keyword in ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "TRUNCATE"])
        
        # If response doesn't contain SQL keywords, check if it looks like a text answer
        if not has_sql_keywords:
            # Check if it's a clarification
            clarification_phrases = [
                "which table", "which table's", "please specify", "available tables", 
                "what would you like", "could you please", "please provide"
            ]
            looks_like_clarification = any(phrase in response_stripped.lower() for phrase in clarification_phrases)
            
            if looks_like_clarification:
                logger.info(f"✅ Clarification-like response detected (no SQL keywords): {response_stripped[:100]}")
                # Add the prefix if missing
                if not response_stripped.startswith("CLARIFICATION_NEEDED:"):
                    return f"CLARIFICATION_NEEDED: {response_stripped}"
                return response_stripped
            
            # Check if it looks like a general text answer (Excel formula, explanation, etc.)
            text_answer_indicators = [
                "excel", "formula", "=", "average", "sum", "count", "today()", "if(", "vlookup",
                "to calculate", "you can use", "here is", "the following", "this formula"
            ]
            looks_like_text_answer = any(indicator in response_stripped.lower() for indicator in text_answer_indicators)
            
            if looks_like_text_answer:
                logger.info(f"✅ Text answer detected (Excel formula/explanation): {response_stripped[:100]}")
                # Return as logical answer so it's displayed as text
                return f"LOGICAL_ANSWER: {response_stripped}"
        
        # Check if response is a read-only error
        if response.strip() == "READ_ONLY_ERROR" or response.strip().startswith("READ_ONLY_ERROR"):
            return "READ_ONLY_ERROR"
        
        # Check if response is invalid query
        if response.strip() == "INVALID_QUERY" or response.strip().startswith("INVALID_QUERY"):
            return "INVALID_QUERY"
        
        # Extract SQL from response (handle cases where model returns text + SQL)
        sql_query = extract_sql_from_response(response)
        
        # If SQL extraction returned empty or doesn't look like SQL, check if it's a text answer
        if not sql_query or not any(keyword in sql_query.upper() for keyword in ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE"]):
            # Check if the original response looks like a text answer
            text_answer_indicators = [
                "excel", "formula", "average", "sum", "count", "today()", "if(", "vlookup",
                "to calculate", "you can use", "here is", "the following", "this formula",
                "```excel", "=average", "=sum", "=count"
            ]
            if any(indicator in response_stripped.lower() for indicator in text_answer_indicators):
                logger.info(f"✅ Text answer detected after SQL extraction (Excel formula/explanation): {response_stripped[:100]}")
                return f"LOGICAL_ANSWER: {response_stripped}"
        
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # If after extraction we still don't have valid SQL, return as logical answer
        if not sql_query or not any(keyword in sql_query.upper() for keyword in ["WITH", "SELECT", "FROM"]):
            logger.info(f"✅ No valid SQL found, treating as text answer: {response_stripped[:100]}")
            return f"LOGICAL_ANSWER: {response_stripped}"
        
        # Fix CTE queries that might be missing WITH keyword
        # If query has CTE pattern (SELECT ... FROM ... ), AS (SELECT ...) but doesn't start with WITH
        if " AS (" in sql_query.upper() and not sql_query.upper().startswith("WITH"):
            # Check if it looks like a CTE (has pattern: name AS (SELECT ...))
            cte_pattern = r'(\w+)\s+AS\s*\('
            matches = re.findall(cte_pattern, sql_query, re.IGNORECASE)
            if matches and len(matches) > 1:
                # This looks like a CTE missing WITH, add it
                sql_query = "WITH " + sql_query.lstrip()
                logger.info("✅ Added missing WITH keyword to CTE query")
        
        # Remove TOP 100 if user didn't explicitly ask for a limit
        # Only remove if it's TOP 100 (default limit), keep TOP N if N is specified
        # Remove "TOP 100" but keep "TOP 10", "TOP 50", etc. if user specified
        if "top 100" in sql_query.lower() and not any(f"top {n}" in user_query.lower() for n in ["100", "hundred"]):
            # Only remove TOP 100 if it appears right after SELECT
            # Pattern: SELECT TOP 100 -> SELECT
            sql_query = re.sub(r'\bSELECT\s+TOP\s+100\b', 'SELECT', sql_query, flags=re.IGNORECASE)
            sql_query = sql_query.strip()
            # Clean up any double spaces
            sql_query = re.sub(r'\s+', ' ', sql_query)
            # Ensure SELECT is still present (safety check)
            if not re.search(r'\bSELECT\b', sql_query, re.IGNORECASE):
                raise Exception("SQL extraction error: SELECT keyword missing after TOP removal")
        
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
        'CREATE TABLE', 'CREATE INDEX', 'CREATE VIEW', 'CREATE PROCEDURE', 'CREATE FUNCTION',  # Only block CREATE statements, not column names
        'EXEC', 'EXECUTE', 'SP_', 'XP_', 'GRANT', 'REVOKE',
        'MERGE', 'BULK INSERT', 'BACKUP', 'RESTORE', 'DBCC'
    ]
    
    # Check if query starts with SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed. You have read-only access to the database."
    
    # Check for dangerous keywords anywhere in the query
    # But be careful - column/table names might contain these words
    for keyword in dangerous_keywords:
        # Check if keyword appears as a standalone SQL command (not part of a column/table name)
        # Look for keyword followed by space or at end of query, or as part of a SQL statement
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_no_comments_upper):
            return False, f"Write operations like '{keyword}' are not allowed. You have read-only access to the VikasAI database."
    
    # Additional check for semicolon-separated multiple statements
    if ';' in sql_query and sql_query.count(';') > 1:
        return False, "Multiple statements are not allowed. You have read-only access to the database."
    
    return True, None

def execute_sql_query(sql_query: str, limit: int = 1000) -> Tuple[List[dict], Optional[str], Optional[int]]:
    """
    Execute SQL query on SQL Server and return results (READ-ONLY)
    Returns: (data, error, total_count)
    - data: List of results (limited to 1000 by default)
    - error: Error message if any
    - total_count: Total number of records (None if query doesn't support counting)
    """
    try:
        # Validate query is read-only
        is_safe, error_msg = is_read_only_query(sql_query)
        if not is_safe:
            return None, error_msg, None
        
        conn = get_sqlserver_connection()
        cursor = conn.cursor()
        
        sql_query = sql_query.replace('ILIKE', 'LIKE')
        
        # Check if query already has TOP clause
        sql_upper = sql_query.upper()
        has_top = 'TOP' in sql_upper
        
        # Get total count first (if possible)
        total_count = None
        try:
            # Try to get count by wrapping query in a subquery
            # This works for most SELECT queries
            count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) as subquery"
            cursor.execute(count_query)
            count_result = cursor.fetchone()
            if count_result:
                total_count = count_result[0]
        except:
            # If count query fails, we'll just proceed without total count
            pass
        
        # Limit results to specified limit if not already limited
        limited_query = sql_query
        if not has_top and limit > 0:
            # Add TOP clause if not present
            # Find the SELECT keyword and insert TOP after it
            limited_query = re.sub(r'\bSELECT\b', f'SELECT TOP {limit}', sql_query, count=1, flags=re.IGNORECASE)
        
        cursor.execute(limited_query)
        results = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        data = [dict(zip(columns, row)) for row in results]
        
        # If we got exactly the limit and didn't get total count, try to estimate
        if total_count is None and len(data) == limit:
            # Try a simpler count approach
            try:
                # Extract table name from query for a rough estimate
                # This is a fallback - not perfect but better than nothing
                pass  # We'll handle this in the response message
            except:
                pass
        
        cursor.close()
        conn.close()
        
        return data, None, total_count
    except Exception as e:
        return None, f"SQL execution error: {str(e)}", None

