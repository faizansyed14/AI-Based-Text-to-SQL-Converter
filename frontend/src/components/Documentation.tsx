import './Documentation.css'

const Documentation = ({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) => {
  if (!isOpen) return null

  return (
    <div className="documentation-overlay" onClick={onClose}>
      <div className="documentation-modal" onClick={(e) => e.stopPropagation()}>
        <div className="documentation-header">
          <h1>📚 Complete Documentation</h1>
          <button className="documentation-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="documentation-content">
          {/* Introduction */}
          <section className="doc-section">
            <h2>🎯 Introduction</h2>
            <p>
              This AI-powered Text-to-SQL application converts your natural language questions into SQL queries 
              and executes them against the VikasAI SQL Server database. The system uses OpenAI's GPT-4o-mini model 
              to understand your intent and generate accurate SQL queries.
            </p>
          </section>

          {/* How It Works */}
          <section className="doc-section">
            <h2>⚙️ How Query Generation Works</h2>
            <div className="flow-diagram">
              <div className="flow-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h3>You Ask a Question</h3>
                  <p>Type your question in natural language, e.g., "Show me all brands" or "What are the top 10 products by sales?"</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <h3>System Checks for Write Operations</h3>
                  <p>The system first checks if your question contains any write operations (DELETE, UPDATE, INSERT, TRUNCATE, DROP, ALTER, CREATE). If detected, the query is blocked immediately without sending to GPT.</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <h3>Database Schema is Retrieved</h3>
                  <p>The system connects to the SQL Server and retrieves the database schema (table names, column names, data types). <strong>Only the schema structure is retrieved, NOT any actual data rows.</strong></p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <h3>Schema is Formatted and Sent to GPT</h3>
                  <p>The schema is converted to JSON format and embedded in the system prompt. <strong>This happens on EVERY query</strong> - each time you ask a question, the current database schema is retrieved and sent to GPT along with your question.</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">5</div>
                <div className="step-content">
                  <h3>GPT Generates SQL Query</h3>
                  <p>OpenAI's GPT-4o-mini receives your question and the complete database schema in JSON format, then generates an appropriate SELECT query. The system explicitly instructs GPT to only generate SELECT queries for read-only access.</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">6</div>
                <div className="step-content">
                  <h3>Query is Validated</h3>
                  <p>Before execution, the generated SQL query is validated to ensure it's a SELECT statement and doesn't contain any write operations.</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">7</div>
                <div className="step-content">
                  <h3>Query is Executed</h3>
                  <p>The validated SQL query is executed against the VikasAI SQL Server database, and results are returned to you.</p>
                </div>
              </div>
              
              <div className="flow-arrow">↓</div>
              
              <div className="flow-step">
                <div className="step-number">8</div>
                <div className="step-content">
                  <h3>Results are Formatted</h3>
                  <p>The query results are formatted into a beautiful, readable HTML table or card view with proper data type formatting (numbers, dates, nulls).</p>
                </div>
              </div>
            </div>
          </section>

          {/* Security & Restrictions */}
          <section className="doc-section">
            <h2>🔒 Security & Read-Only Access</h2>
            <div className="warning-box">
              <strong>⚠️ Important:</strong> This application enforces <strong>READ-ONLY</strong> access to the database. 
              Write operations are completely blocked.
            </div>
            
            <h3>Blocked Operations</h3>
            <p>The following operations will <strong>immediately stop</strong> your query and show an error message:</p>
            <ul className="blocked-list">
              <li><code>DELETE</code> - Removing data from tables</li>
              <li><code>UPDATE</code> - Modifying existing data</li>
              <li><code>INSERT</code> - Adding new data</li>
              <li><code>TRUNCATE</code> - Clearing table contents</li>
              <li><code>DROP</code> - Deleting tables or databases</li>
              <li><code>ALTER</code> - Modifying table structure</li>
              <li><code>CREATE</code> - Creating new tables or databases</li>
            </ul>
            
            <h3>How Blocking Works</h3>
            <ol>
              <li><strong>Pre-LLM Check:</strong> Before sending your question to GPT, the system scans for keywords and patterns that indicate write operations.</li>
              <li><strong>GPT Instructions:</strong> Even if a write operation passes the pre-check, GPT is explicitly instructed to only generate SELECT queries.</li>
              <li><strong>Post-Generation Validation:</strong> The generated SQL is validated to ensure it's a SELECT statement.</li>
              <li><strong>Execution Check:</strong> Before execution, the query is checked one final time for write operations.</li>
            </ol>
            
            <div className="info-box">
              <strong>💡 Example:</strong> If you ask "Delete all users", the system will immediately block this and show: 
              <code>"⚠️ Read-Only Access: Write operations are not allowed"</code>
            </div>
          </section>

          {/* Best Practices */}
          <section className="doc-section">
            <h2>✨ How to Write Perfect Queries</h2>
            
            <h3>1. Be Specific and Clear</h3>
            <div className="example-box">
              <div className="example-bad">
                <strong>❌ Bad:</strong> "users"
                <p>Too vague - what about users?</p>
              </div>
              <div className="example-good">
                <strong>✅ Good:</strong> "Show me all users"
                <p>Clear intent to retrieve user data</p>
              </div>
            </div>

            <h3>2. Use Action Words</h3>
            <p>Start your queries with action words that indicate you want to <strong>read</strong> data:</p>
            <ul>
              <li><strong>Show me</strong> - "Show me all products"</li>
              <li><strong>List</strong> - "List all customers"</li>
              <li><strong>Display</strong> - "Display orders from last month"</li>
              <li><strong>Find</strong> - "Find products with price greater than 100"</li>
              <li><strong>Get</strong> - "Get the total sales"</li>
              <li><strong>What</strong> - "What are the top 10 products?"</li>
              <li><strong>How many</strong> - "How many orders were placed today?"</li>
              <li><strong>Which</strong> - "Which customers have pending orders?"</li>
              <li><strong>Give me</strong> - "Give me the full row whose pr addf code is CMQ/LAPT"</li>
              <li><strong>Tell me</strong> - "Tell me about all brands"</li>
            </ul>

            <h3>3. Specify Filters and Conditions</h3>
            <div className="example-box">
              <div className="example-bad">
                <strong>❌ Less Specific:</strong> "Show me products"
              </div>
              <div className="example-good">
                <strong>✅ More Specific:</strong> "Show me products where price is greater than 50 and category is Electronics"
              </div>
            </div>

            <h3>4. Use Natural Language for Aggregations</h3>
            <ul>
              <li>"Count the number of orders" → <code>SELECT COUNT(*) FROM orders</code></li>
              <li>"What is the total sales?" → <code>SELECT SUM(amount) FROM sales</code></li>
              <li>"Show me the average price" → <code>SELECT AVG(price) FROM products</code></li>
              <li>"What are the top 10 products by sales?" → <code>SELECT TOP 10 ... ORDER BY sales DESC</code></li>
            </ul>

            <h3>5. Reference Specific Columns</h3>
            <div className="example-box">
              <div className="example-good">
                <strong>✅ Good:</strong> "Show me the full row whose pr addf code is CMQ/LAPT"
                <p>This clearly specifies the column name and value to search for</p>
              </div>
            </div>

            <h3>6. Use Date Ranges</h3>
            <ul>
              <li>"Show me orders from last month"</li>
              <li>"What are the sales for this year?"</li>
              <li>"Display records created between January 1 and March 31"</li>
            </ul>
          </section>

          {/* Common Query Patterns */}
          <section className="doc-section">
            <h2>📋 Common Query Patterns</h2>
            
            <h3>Simple Select</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me all brands"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>SELECT * FROM brands</code></pre>
              </div>
            </div>

            <h3>Filtered Query</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me products where price is greater than 100"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>SELECT * FROM products WHERE price &gt; 100</code></pre>
              </div>
            </div>

            <h3>Search by Specific Value</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Give me the full row whose pr addf code is CMQ/LAPT"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>SELECT * FROM [table_name] WHERE [pr_addf_code] = 'CMQ/LAPT'</code></pre>
              </div>
            </div>

            <h3>Aggregation</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "How many orders were placed today?"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>SELECT COUNT(*) FROM orders WHERE order_date = CAST(GETDATE() AS DATE)</code></pre>
              </div>
            </div>

            <h3>Top N Results</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "What are the top 10 products by sales?"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>SELECT TOP 10 * FROM products ORDER BY sales DESC</code></pre>
              </div>
            </div>
          </section>

          {/* Complex Queries */}
          <section className="doc-section">
            <h2>🚀 Complex Query Capabilities</h2>
            <p>
              Yes! The system can understand and generate complex SQL queries. It uses OpenAI's GPT-4o-mini model, 
              which is capable of understanding sophisticated business questions and converting them into complex SQL statements.
            </p>

            <h3>✅ Supported Complex Query Types</h3>
            
            <h4>1. Multi-Table JOINs</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me all products with their brand names and category descriptions"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT p.PR_CODE, p.PR_DESC, b.BR_DESC, c.CT_DESC
FROM [EDC_PRODUCT] p
LEFT JOIN [EDC_BRAND] b ON p.PR_BR_CODE = b.BR_CODE
LEFT JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE`}</code></pre>
              </div>
            </div>

            <h4>2. Aggregations with GROUP BY</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "What is the total sales amount for each brand?"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT b.BR_DESC, SUM(s.amount) as total_sales
FROM [EDC_SALES] s
JOIN [EDC_PRODUCT] p ON s.product_id = p.PR_CODE
JOIN [EDC_BRAND] b ON p.PR_BR_CODE = b.BR_CODE
GROUP BY b.BR_DESC
ORDER BY total_sales DESC`}</code></pre>
              </div>
            </div>

            <h4>3. Subqueries and Nested Queries</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me products that have sales above the average"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT * FROM [EDC_PRODUCT]
WHERE PR_CODE IN (
    SELECT product_id FROM [EDC_SALES]
    WHERE amount > (SELECT AVG(amount) FROM [EDC_SALES])
)`}</code></pre>
              </div>
            </div>

            <h4>4. Multiple Conditions and Filters</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Find all products where price is between 50 and 200, brand is SAS, and category is Software"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT p.*
FROM [EDC_PRODUCT] p
JOIN [EDC_BRAND] b ON p.PR_BR_CODE = b.BR_CODE
JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE
WHERE p.PR_PRICE BETWEEN 50 AND 200
  AND LOWER(b.BR_DESC) = LOWER('SAS')
  AND LOWER(c.CT_DESC) = LOWER('Software')`}</code></pre>
              </div>
            </div>

            <h4>5. Date Range Queries</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me all orders from the last 30 days with customer names"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT o.*, c.CUSTOMER_NAME
FROM [EDC_ORDERS] o
JOIN [EDC_CUSTOMER] c ON o.CUSTOMER_ID = c.CUSTOMER_ID
WHERE o.ORDER_DATE >= DATEADD(day, -30, GETDATE())
ORDER BY o.ORDER_DATE DESC`}</code></pre>
              </div>
            </div>

            <h4>6. Statistical Functions</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "What is the average, minimum, and maximum price for each category?"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT 
    c.CT_DESC,
    AVG(p.PR_PRICE) as avg_price,
    MIN(p.PR_PRICE) as min_price,
    MAX(p.PR_PRICE) as max_price,
    COUNT(*) as product_count
FROM [EDC_PRODUCT] p
JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE
GROUP BY c.CT_DESC`}</code></pre>
              </div>
            </div>

            <h4>7. UNION Queries</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me all products from brand SAS and also all products with price over 1000"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT * FROM [EDC_PRODUCT] p
JOIN [EDC_BRAND] b ON p.PR_BR_CODE = b.BR_CODE
WHERE LOWER(b.BR_DESC) = LOWER('SAS')
UNION
SELECT * FROM [EDC_PRODUCT]
WHERE PR_PRICE > 1000`}</code></pre>
              </div>
            </div>

            <h4>8. Window Functions (Advanced)</h4>
            <div className="code-example">
              <div className="code-input">
                <strong>You ask:</strong> "Show me each product with its rank within its category by sales"
              </div>
              <div className="code-output">
                <strong>Generated SQL:</strong>
                <pre><code>{`SELECT 
    p.PR_CODE,
    p.PR_DESC,
    c.CT_DESC,
    s.total_sales,
    RANK() OVER (PARTITION BY c.CT_CODE ORDER BY s.total_sales DESC) as rank_in_category
FROM [EDC_PRODUCT] p
JOIN [EDC_CATEGORY] c ON p.PR_PT_CODE = c.CT_CODE
LEFT JOIN (
    SELECT product_id, SUM(amount) as total_sales
    FROM [EDC_SALES]
    GROUP BY product_id
) s ON p.PR_CODE = s.product_id`}</code></pre>
              </div>
            </div>

            <div className="info-box">
              <strong>💡 Tips for Complex Queries:</strong>
              <ul>
                <li><strong>Be specific:</strong> Mention table names, column names, and relationships when possible</li>
                <li><strong>Use natural language:</strong> Describe what you want in business terms - GPT will figure out the SQL</li>
                <li><strong>Break it down:</strong> For very complex queries, you can ask follow-up questions to refine</li>
                <li><strong>Use conversation history:</strong> The system remembers the last 5 messages, so you can build on previous queries</li>
                <li><strong>Check the generated SQL:</strong> Click "Show SQL" to see how GPT interpreted your question</li>
              </ul>
            </div>

            <div className="warning-box">
              <strong>⚠️ Limitations:</strong>
              <ul>
                <li>Maximum query complexity depends on GPT-4o-mini's token limits (500 tokens for SQL generation)</li>
                <li>Very long queries with many tables might need to be simplified</li>
                <li>If a query is too complex, try breaking it into smaller questions</li>
                <li>Always verify the generated SQL matches your intent before relying on results</li>
              </ul>
            </div>
          </section>

          {/* Data Privacy */}
          <section className="doc-section">
            <h2>🔐 Data Privacy & Security</h2>
            <div className="privacy-highlight">
              <h3>What is Sent to OpenAI (GPT)?</h3>
              <ul>
                <li>✅ <strong>Your question</strong> (natural language text)</li>
                <li>✅ <strong>Database schema/metadata</strong> (table names, column names, data types) - <strong>ONLY structure, NO data</strong></li>
                <li>✅ <strong>Conversation history</strong> (last 5 messages for context)</li>
                <li>❌ <strong>NO actual data rows</strong> are ever sent to OpenAI</li>
                <li>❌ <strong>NO sensitive data values</strong> are transmitted</li>
                <li>❌ <strong>NO user information</strong> beyond your question</li>
              </ul>
            </div>

            <h3>How Schema/Metadata is Retrieved and Sent to GPT</h3>
            <div className="schema-explanation">
              <p><strong>On EVERY query you make, here's exactly what happens:</strong></p>
              
              <h4>Step 1: Connect to Database and Get Schema</h4>
              <p>The backend code connects to your SQL Server and asks: "What tables do you have, and what columns are in each table?"</p>
              
              <div className="code-example">
                <div className="code-input">
                  <strong>Python Code (Backend):</strong>
                  <pre><code>{`# This code runs on EVERY query
def get_table_schema():
    # Connect to SQL Server
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    
    # Ask: "What tables exist?"
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_type = 'BASE TABLE'
    """)
    tables = cursor.fetchall()
    
    schema_info = {}
    for table in tables:
        table_name = table[0]
        # Ask: "What columns are in this table?"
        cursor.execute("""
            SELECT column_name, data_type, 
                   is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        
        # Store only structure (names, types), NOT data
        schema_info[table_name] = [
            {
                "name": col[0],      # Column name
                "type": col[1],      # Data type (int, varchar, etc.)
                "nullable": col[2],  # Can it be empty?
                "max_length": col[3] # Maximum length
            }
            for col in columns
        ]
    
    return schema_info  # Returns structure only, NO data!`}</code></pre>
                </div>
                <div className="code-output">
                  <strong>What This Code Does (Simple Explanation):</strong>
                  <ul>
                    <li>🔌 Connects to your SQL Server database</li>
                    <li>📋 Asks the database: "What tables do you have?"</li>
                    <li>📊 For each table, asks: "What columns are in this table?"</li>
                    <li>📝 Records: Table name, column names, data types (int, varchar, etc.)</li>
                    <li>❌ Does NOT retrieve any actual data values</li>
                    <li>✅ Returns only the structure/metadata</li>
                  </ul>
                </div>
              </div>

              <h4>Step 2: Convert Schema to JSON Format</h4>
              <p>The schema structure is converted to JSON (a text format that GPT can understand):</p>
              
              <div className="code-example">
                <div className="code-input">
                  <strong>Python Code:</strong>
                  <pre><code>{`# Get the schema structure
schema_info = get_table_schema()

# Convert to JSON text format
import json
schema_text = json.dumps(schema_info, indent=2)

# Result looks like this:
# {
#   "EDC_BRAND": [
#     {"name": "BR_CODE", "type": "int"},
#     {"name": "BR_DESC", "type": "varchar"}
#   ],
#   "EDC_PRODUCT": [
#     {"name": "PR_CODE", "type": "varchar"},
#     {"name": "PR_DESC", "type": "varchar"},
#     {"name": "PR_PRICE", "type": "decimal"}
#   ]
# }`}</code></pre>
                </div>
                <div className="code-output">
                  <strong>What This Creates:</strong>
                  <p>A text description of your database structure that looks like this:</p>
                  <pre><code>{`{
  "EDC_BRAND": [
    {"name": "BR_CODE", "type": "int"},
    {"name": "BR_DESC", "type": "varchar"}
  ],
  "EDC_PRODUCT": [
    {"name": "PR_CODE", "type": "varchar"},
    {"name": "PR_DESC", "type": "varchar"},
    {"name": "PR_PRICE", "type": "decimal"}
  ]
}`}</code></pre>
                  <p><strong>Notice:</strong> This shows table names and column types, but NO actual data like "SAS" or product prices!</p>
                </div>
              </div>

              <h4>Step 3: Send Schema + Your Question to GPT</h4>
              <p>The schema JSON is embedded in a "system prompt" (instructions for GPT) along with your question:</p>
              
              <div className="code-example">
                <div className="code-input">
                  <strong>Python Code (What Gets Sent to GPT):</strong>
                  <pre><code>{`# Create the system prompt with schema
system_prompt = f"""You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.

Database Schema:
{schema_text}  # ← The JSON schema goes here

Rules:
1. Generate ONLY SELECT queries
2. Use SQL Server syntax
3. ... (more rules)
"""

# Create messages to send to GPT
messages = [
    {"role": "system", "content": system_prompt},  # Schema + instructions
    {"role": "user", "content": user_query}         # Your question
]

# Send to OpenAI API
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,  # Schema + Your Question
    temperature=0.3,
    max_tokens=500
)

# GPT returns the SQL query
sql_query = response.choices[0].message.content`}</code></pre>
                </div>
                <div className="code-output">
                  <strong>What GPT Receives (Example):</strong>
                  <div className="gpt-message-box">
                    <p><strong>System Message (Instructions + Schema):</strong></p>
                    <pre><code>{`You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.

Database Schema:
{
  "EDC_BRAND": [
    {"name": "BR_CODE", "type": "int"},
    {"name": "BR_DESC", "type": "varchar"}
  ],
  "EDC_PRODUCT": [
    {"name": "PR_CODE", "type": "varchar"},
    {"name": "PR_DESC", "type": "varchar"}
  ]
}

Rules:
1. Generate ONLY SELECT queries
2. Use SQL Server syntax
...`}</code></pre>
                    <p><strong>User Message (Your Question):</strong></p>
                    <pre><code>"Show me all brands"</code></pre>
                  </div>
                </div>
              </div>

              <div className="info-box">
                <strong>💡 Simple Analogy:</strong>
                <p>
                  Think of it like asking a librarian: "I want to find books about cooking." 
                  The librarian needs to know:
                </p>
                <ul>
                  <li>✅ What sections exist (like "Fiction", "Non-Fiction", "Cooking") - This is like the schema</li>
                  <li>✅ What categories are in each section - This is like column names</li>
                  <li>❌ They DON'T need to know every single book title - This is like your actual data</li>
                </ul>
                <p>
                  GPT is like that librarian - it needs to know the structure (schema) to help you find what you want, 
                  but it doesn't need to see all your actual data.
                </p>
              </div>
              
              <div className="warning-box">
                <strong>⚠️ Important:</strong> The schema is retrieved fresh on <strong>EVERY query</strong>. 
                This means if you add new tables or columns to your database, GPT will see them in the next query 
                without needing to restart the application.
              </div>
            </div>

            <h3>What GPT Sees - Example</h3>
            <div className="code-example">
              <div className="code-input">
                <strong>System Prompt (sent to GPT):</strong>
                <pre><code>{`You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.

Database Schema:
{
  "EDC_BRAND": [
    {"name": "BR_CODE", "type": "int"},
    {"name": "BR_DESC", "type": "varchar"}
  ],
  "EDC_PRODUCT": [
    {"name": "PR_CODE", "type": "varchar"},
    {"name": "PR_DESC", "type": "varchar"}
  ]
}

Rules:
1. Generate ONLY SELECT queries
2. Use SQL Server syntax
...`}</code></pre>
              </div>
              <div className="code-output">
                <strong>User Message (your question):</strong>
                <pre><code>"Show me all brands"</code></pre>
              </div>
            </div>

            <div className="info-box">
              <strong>💡 Key Points:</strong>
              <ul>
                <li>GPT sees: "There's a table called EDC_BRAND with columns BR_CODE (int) and BR_DESC (varchar)"</li>
                <li>GPT does NOT see: "BR_CODE=1, BR_DESC='SAS'" or any actual data values</li>
                <li>GPT uses the schema to understand table structure and generate correct SQL</li>
                <li>All actual data stays in your SQL Server database and is never transmitted</li>
              </ul>
            </div>

            <h3>What Happens Locally?</h3>
            <ul>
              <li>Your question is processed by the backend server (running in Docker)</li>
              <li>The backend connects directly to your SQL Server database to get schema</li>
              <li>Schema is formatted and sent to OpenAI API</li>
              <li>GPT generates SQL query and returns it</li>
              <li>Backend validates and executes the SQL query locally</li>
              <li>Results are returned directly to you - data never leaves your infrastructure</li>
            </ul>

            <h3>Connection Architecture</h3>
            <div className="architecture-box">
              <p><strong>Step 1: Schema Retrieval</strong></p>
              <p>Your Browser → Backend (FastAPI) → SQL Server (VikasAI) → Get Schema</p>
              <p><strong>Step 2: Query Generation</strong></p>
              <p>Backend → OpenAI API (Schema JSON + Your Question) → GPT generates SQL</p>
              <p><strong>Step 3: Query Execution</strong></p>
              <p>Backend → SQL Server (VikasAI) → Execute SQL → Return Results</p>
              <p><strong>Step 4: Display Results</strong></p>
              <p>Backend → Your Browser → Display formatted results</p>
            </div>

            <div className="privacy-highlight">
              <h3>🔒 Privacy Guarantee</h3>
              <p>
                <strong>Your actual data NEVER leaves your SQL Server database.</strong> Only the structure 
                (table names, column names, data types) is sent to OpenAI to help GPT understand your database 
                and generate correct SQL queries. All data retrieval happens locally on your infrastructure.
              </p>
            </div>
          </section>

          {/* Troubleshooting */}
          <section className="doc-section">
            <h2>🔧 Troubleshooting</h2>
            
            <h3>Query Returns No Results</h3>
            <ul>
              <li>Check if the table/column names exist in the database</li>
              <li>Verify your filter conditions are correct</li>
              <li>Try a simpler query first to test connectivity</li>
            </ul>

            <h3>Query is Blocked (Read-Only Error)</h3>
            <ul>
              <li>Make sure you're using SELECT queries only</li>
              <li>Avoid words like "delete", "update", "insert", "drop", "truncate"</li>
              <li>Rephrase your question to be a read operation</li>
            </ul>

            <h3>Incorrect Results</h3>
            <ul>
              <li>Be more specific in your question</li>
              <li>Specify exact column names if possible</li>
              <li>Check the generated SQL query to verify it matches your intent</li>
              <li>Use the table selector to see available tables and columns</li>
            </ul>

            <h3>Connection Issues</h3>
            <ul>
              <li>Check if the SQL Server container is running</li>
              <li>Verify database connection settings</li>
              <li>Check backend logs for connection errors</li>
            </ul>
          </section>

          {/* Tips & Tricks */}
          <section className="doc-section">
            <h2>💡 Tips & Tricks</h2>
            <ul>
              <li><strong>Use the table selector:</strong> Click on the table selector panel to see all available tables and their columns</li>
              <li><strong>View the SQL:</strong> Click "Show SQL" to see the generated query and learn how GPT interpreted your question</li>
              <li><strong>Copy queries:</strong> Use the copy button to save useful SQL queries for reference</li>
              <li><strong>Be conversational:</strong> You can ask follow-up questions in the same conversation</li>
              <li><strong>Use examples:</strong> Click on example questions to see how they work</li>
              <li><strong>Check formatting:</strong> Results are automatically formatted - numbers have commas, dates are readable, nulls are clearly marked</li>
            </ul>
          </section>

          {/* Technical Details */}
          <section className="doc-section">
            <h2>⚙️ Technical Details</h2>
            <ul>
              <li><strong>AI Model:</strong> OpenAI GPT-4o-mini</li>
              <li><strong>Backend:</strong> FastAPI (Python)</li>
              <li><strong>Frontend:</strong> React with TypeScript</li>
              <li><strong>Database:</strong> SQL Server (VikasAI)</li>
              <li><strong>Query Validation:</strong> Multi-layer validation (pre-LLM, GPT instructions, post-generation, execution)</li>
              <li><strong>Result Formatting:</strong> Automatic HTML formatting with data type awareness</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

export default Documentation

