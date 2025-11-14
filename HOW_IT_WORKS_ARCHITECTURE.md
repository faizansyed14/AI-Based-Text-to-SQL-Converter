# How Your Text-to-SQL Application Works

## 🔒 **IMPORTANT: GPT Does NOT Have Direct Access to Your Database**

**GPT (OpenAI) never directly connects to your VikasAI database.** Here's what actually happens:

---

## 📊 **Architecture Overview**

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTP Request
       │ "Show me all brands"
       ▼
┌─────────────────────────────────────┐
│      Backend (FastAPI)               │
│  ┌───────────────────────────────┐  │
│  │  Step 1: Get Database Schema  │  │
│  │  (Connects to SQL Server)     │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
│  ┌──────────────▼────────────────┐  │
│  │  Step 2: Send Schema to GPT   │  │
│  │  (NOT the actual data!)        │  │
│  │  Schema = Table/Column names  │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
│  ┌──────────────▼────────────────┐  │
│  │  Step 3: GPT Generates SQL    │  │
│  │  Returns: SELECT * FROM...    │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
│  ┌──────────────▼────────────────┐  │
│  │  Step 4: Execute SQL Query    │  │
│  │  (Backend connects to DB)     │  │
│  └──────────────┬────────────────┘  │
│                 │                    │
└─────────────────┼────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  SQL Server      │
         │  (VikasAI DB)    │
         │  - EDC_BRAND     │
         │  - EDC_PRODUCT   │
         │  - EDC_CATEGORY  │
         └─────────────────┘
```

---

## 🔍 **Step-by-Step Flow**

### **Step 1: User Asks a Question**
```
User types: "Show me all brands"
```

### **Step 2: Backend Gets Database Schema (NOT Data!)**
The backend connects to your SQL Server and retrieves **only the schema information**:

**What is Schema?**
- Table names (EDC_BRAND, EDC_PRODUCT, etc.)
- Column names (BR_CODE, BR_DESC, PR_CODE, etc.)
- Data types (varchar, int, etc.)
- **NOT the actual data rows!**

**Code Location:** `backend/services/schema_service.py`
```python
def get_table_schema():
    # Connects to SQL Server
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    
    # Gets ONLY table/column structure
    cursor.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_type = 'BASE TABLE'
    """)
    # Returns schema info, NOT data
```

**Example Schema Sent to GPT:**
```json
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
```

**How It's Sent to GPT:**

The schema is sent as part of the **system prompt** in the OpenAI API call. Here's the exact code flow:

**Step 1: Get Schema from Database** (`backend/services/schema_service.py`)
```python
def get_table_schema():
    conn = get_sqlserver_connection()  # Connect to SQL Server
    cursor = conn.cursor()
    
    # Query SQL Server's information_schema to get table/column structure
    cursor.execute("""
        SELECT table_name, column_name, data_type, is_nullable, character_maximum_length
        FROM information_schema.columns
        WHERE table_type = 'BASE TABLE'
        ORDER BY table_name, ordinal_position
    """)
    
    # Build schema dictionary (NO DATA, only structure!)
    schema_info = {}
    for table in tables:
        schema_info[table_name] = [
            {
                "name": col[0],      # Column name
                "type": col[1],      # Data type
                "nullable": col[2],   # Can be NULL?
                "max_length": col[3]  # Max length
            }
            for col in columns
        ]
    
    return schema_info  # Returns: {"EDC_BRAND": [...], "EDC_PRODUCT": [...]}
```

**Step 2: Convert Schema to JSON String** (`backend/services/sql_service.py`)
```python
def generate_sql_query(user_query, conversation_history):
    # Get schema dictionary from database
    schema_info = get_table_schema()
    
    # Convert Python dictionary to JSON string
    schema_text = json.dumps(schema_info, indent=2)
    # Result: '{\n  "EDC_BRAND": [\n    {"name": "BR_CODE", "type": "int"}, ...\n  ]\n}'
```

**Step 3: Embed Schema in System Prompt**
```python
    system_prompt = f"""You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.

Database Schema:
{schema_text}  # ← The JSON schema string is inserted here

Rules:
1. Generate ONLY the SQL query, no explanations or markdown
2. Use SQL Server (T-SQL) syntax
...
"""
```

**Step 4: Send to OpenAI API**
```python
    messages = [
        {"role": "system", "content": system_prompt},  # ← Schema is in system prompt
        {"role": "user", "content": user_query}        # ← User's question
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,  # ← Schema + question sent here
        temperature=0.3,
        max_tokens=500
    )
```

**Actual Message Format Sent to OpenAI:**
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "You are a SQL expert. Given a database schema and a user's question, generate a valid SQL query.\n\nDatabase Schema:\n{\n  \"EDC_BRAND\": [\n    {\"name\": \"BR_CODE\", \"type\": \"int\"},\n    {\"name\": \"BR_DESC\", \"type\": \"varchar\"}\n  ],\n  \"EDC_PRODUCT\": [\n    {\"name\": \"PR_CODE\", \"type\": \"varchar\"},\n    {\"name\": \"PR_DESC\", \"type\": \"varchar\"}\n  ]\n}\n\nRules:\n1. Generate ONLY the SQL query...\n..."
    },
    {
      "role": "user",
      "content": "Show me all brands"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 500
}
```

**Key Points:**
- ✅ Schema is sent as **text/string** in the system prompt
- ✅ It's a **JSON-formatted string** embedded in the prompt
- ✅ GPT receives it as part of the conversation context
- ✅ GPT uses this schema to understand table/column structure
- ❌ **NO actual data rows are included** - only structure!

### **Step 3: GPT Generates SQL Query**
The backend sends to OpenAI API:
- ✅ Database schema (table/column names)
- ✅ User's question
- ✅ Conversation history
- ❌ **NO actual data from your database**

**Code Location:** `backend/services/sql_service.py`
```python
def generate_sql_query(user_query, conversation_history):
    # Get schema (structure only, no data)
    schema_info = get_table_schema()
    
    # Send to GPT
    system_prompt = f"""
    Database Schema:
    {schema_info}  # Only structure, no data!
    
    Generate SQL for: "{user_query}"
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    # GPT returns SQL query like:
    # "SELECT * FROM [EDC_BRAND]"
    return sql_query
```

**What GPT Sees:**
- ✅ "There's a table called EDC_BRAND with columns BR_CODE and BR_DESC"
- ✅ "User wants to see all brands"
- ❌ **GPT never sees actual brand data like "SAS", "QUEST SOFTWARE", etc.**

### **Step 4: Backend Executes SQL Query**
The backend now connects to your database and runs the SQL query:

**Code Location:** `backend/services/sql_service.py`
```python
def execute_sql_query(sql_query):
    # Backend connects to SQL Server
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    
    # Security check: Only SELECT queries allowed
    if not sql_query.strip().upper().startswith("SELECT"):
        return None, "Only SELECT queries allowed"
    
    # Execute query
    cursor.execute(sql_query)
    results = cursor.fetchall()
    
    # Return actual data
    return data, None
```

### **Step 5: Results Sent to Frontend**
The backend sends the query results back to the frontend, which displays them.

---

## 🔐 **Security Features**

1. **Read-Only Access**: Only `SELECT` queries are allowed
   ```python
   if not sql_query.strip().upper().startswith("SELECT"):
       return None, "Only SELECT queries allowed"
   ```

2. **No Data Sent to GPT**: GPT only receives schema (structure), never actual data

3. **Local Database**: Your VikasAI database runs in a Docker container on your machine

---

## 🗄️ **How You're Connected to VikasAI Database**

### **Database Location**
Your VikasAI database is running in a **Docker container** on your local machine:

```
┌─────────────────────────────────────┐
│  Your Computer (Windows)            │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Docker Container             │ │
│  │  SQL Server 2019              │ │
│  │  Port: 1433                   │ │
│  │  Database: VikasAI            │ │
│  │  User: sa                     │ │
│  │  Password: YourStrong@Passw0rd│ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Docker Container             │ │
│  │  Backend (FastAPI)             │ │
│  │  Connects to SQL Server       │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### **Connection Configuration**

**File:** `backend/database/sqlserver.py`
```python
SQLSERVER_CONFIG = {
    "server": "host.docker.internal",  # Connects to host machine
    "port": 1433,                       # SQL Server port
    "database": "VikasAI",              # Your database name
    "user": "sa",                       # SQL Server admin user
    "password": "YourStrong@Passw0rd"  # SQL Server password
}
```

**File:** `docker-compose.yml`
```yaml
backend:
  environment:
    SQLSERVER_HOST: host.docker.internal  # Allows Docker to access host
    SQLSERVER_PORT: 1433
    SQLSERVER_DB: VikasAI
    SQLSERVER_USER: sa
    SQLSERVER_PASSWORD: YourStrong@Passw0rd
  extra_hosts:
    - "host.docker.internal:host-gateway"  # Maps to your Windows machine
```

### **How It Works**
1. **SQL Server Container** runs on your Windows machine (port 1433)
2. **Backend Container** connects using `host.docker.internal`
3. This special hostname allows Docker containers to access services on the host machine
4. The backend uses `pymssql` library to connect to SQL Server

---

## 🚀 **How Everything Runs**

### **Docker Compose Services**

**File:** `docker-compose.yml`

1. **PostgreSQL Container** (`text-to-sql-db`)
   - Stores chat sessions and messages
   - Port: 5433 (mapped from 5432)
   - Not your business data!

2. **Backend Container** (`text-to-sql-backend`)
   - FastAPI application
   - Connects to PostgreSQL (for chat history)
   - Connects to SQL Server (for VikasAI data)
   - Port: 8000 (internal)

3. **Frontend Container** (`text-to-sql-frontend`)
   - React application
   - Port: 3000 (internal)

4. **Nginx Container** (`text-to-sql-nginx`)
   - Reverse proxy
   - Port: 8080 (exposed to your browser)
   - Routes requests to frontend/backend

5. **SQL Server Container** (separate, not in docker-compose)
   - Running separately on port 1433
   - Contains your VikasAI database

### **Network Flow**

```
Browser (localhost:8080)
    │
    ▼
Nginx (port 8080)
    │
    ├──► Frontend (React) ──► Backend API
    │
    └──► Backend API (FastAPI)
            │
            ├──► PostgreSQL (chat sessions)
            │
            └──► SQL Server (VikasAI data)
```

---

## 📝 **Summary**

### **What GPT Has Access To:**
✅ Database schema (table/column names and types)  
✅ Your question  
✅ Conversation history  

### **What GPT Does NOT Have Access To:**
❌ Actual data from your database  
❌ Database connection credentials  
❌ Ability to execute queries directly  
❌ Any write/delete operations  

### **What Your Backend Does:**
✅ Connects to SQL Server to get schema  
✅ Sends schema to GPT  
✅ Receives SQL query from GPT  
✅ Executes SQL query on your database  
✅ Returns results to frontend  

### **Security:**
- Only SELECT queries allowed
- GPT never sees actual data
- Database runs locally in Docker
- No external access to your database

---

## 🔄 **Complete Example Flow**

**User:** "Show me all brands"

1. **Frontend** → Sends HTTP POST to `/api/chat`
2. **Backend** → Connects to SQL Server, gets schema:
   ```json
   {"EDC_BRAND": [{"name": "BR_CODE"}, {"name": "BR_DESC"}]}
   ```
3. **Backend** → Sends to OpenAI API:
   - Schema: `{"EDC_BRAND": [...]}`
   - Question: "Show me all brands"
   - **NO data sent!**
4. **OpenAI** → Returns SQL: `SELECT * FROM [EDC_BRAND]`
5. **Backend** → Executes SQL on SQL Server
6. **SQL Server** → Returns data: `[{"BR_CODE": 899, "BR_DESC": "SAS"}, ...]`
7. **Backend** → Sends data to frontend
8. **Frontend** → Displays results in table

**GPT never saw the actual brand names like "SAS" or "QUEST SOFTWARE"!**

