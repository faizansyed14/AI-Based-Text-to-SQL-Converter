# SQL Server Integration Setup

## ✅ What Has Been Done

Your application has been updated to connect directly to the SQL Server database (VikasAI) for business data queries!

### Changes Made:

1. **Added SQL Server Support**
   - Added `pymssql` library to `requirements.txt`
   - Created `get_sqlserver_connection()` function
   - Updated `get_table_schema()` to read from SQL Server
   - Updated `execute_sql_query()` to execute on SQL Server

2. **Removed Dummy Data**
   - Removed all test/dummy tables from `init_db.sql`
   - PostgreSQL now only stores app metadata (chat_sessions, chat_messages, excel_tables)

3. **Updated SQL Generation**
   - Changed from PostgreSQL syntax to SQL Server (T-SQL) syntax
   - Uses `TOP` instead of `LIMIT`
   - Uses square brackets `[]` for table/column names
   - Handles SQL Server-specific features

## 🗄️ Database Architecture

### PostgreSQL (Port 5433)
- **Purpose:** App metadata only
- **Tables:**
  - `chat_sessions` - Chat session history
  - `chat_messages` - Individual messages
  - `excel_tables` - Excel upload metadata

### SQL Server (Port 1433)
- **Purpose:** Business data
- **Database:** `VikasAI`
- **Tables:**
  - `EDC_BRAND` - 388 brands
  - `EDC_CATEGORY` - 1,751 categories
  - `EDC_PRODUCT` - 188,064 products
  - `EDC_PROD_DESC` - 218,702 product descriptions
  - `STR_STOCK_CARD` - 2,145,991 stock transactions

## 🔧 Configuration

The SQL Server connection is configured via environment variables (with defaults):

```env
SQLSERVER_HOST=localhost
SQLSERVER_PORT=1433
SQLSERVER_DB=VikasAI
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=YourStrong@Passw0rd
```

## 🚀 How to Use

1. **Make sure SQL Server container is running:**
   ```bash
   docker ps | grep sqlserver_restore
   ```

2. **Start your application:**
   ```bash
   docker-compose up
   ```

3. **Use the frontend:**
   - Open http://localhost:8080
   - Type questions in English like:
     - "Show me all brands"
     - "How many products are there?"
     - "List products with SAS brand"
     - "Show top 10 products by price"

4. **The application will:**
   - Convert your English question to SQL
   - Execute it on SQL Server (VikasAI database)
   - Return the results

## 📝 Example Queries

You can ask questions like:

- "Show me all brands"
- "How many products are in the database?"
- "List products with their descriptions"
- "Show me products from brand SAS"
- "What are the top 10 most expensive products?"
- "Count products by category"
- "Show stock transactions for product X"

## 🔒 Security

- Only `SELECT` queries are allowed (read-only)
- No data modification possible
- SQL Server runs in isolated Docker container
- Connection is local only (localhost)

## 🐛 Troubleshooting

### If queries fail:

1. **Check SQL Server is running:**
   ```bash
   docker ps | grep sqlserver_restore
   ```

2. **Check connection:**
   ```bash
   docker exec sqlserver_restore /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourStrong@Passw0rd" -C -d VikasAI -Q "SELECT 1"
   ```

3. **Check backend logs:**
   ```bash
   docker logs text-to-sql-backend
   ```

### Common Issues:

- **Connection refused:** SQL Server container not running
- **Login failed:** Wrong password in environment variables
- **Table not found:** Check table names (they're case-sensitive in SQL Server)

## 📊 Data Overview

Your VikasAI database contains:
- **388 brands** (EDC_BRAND)
- **1,751 categories** (EDC_CATEGORY)  
- **188,064 products** (EDC_PRODUCT)
- **218,702 product descriptions** (EDC_PROD_DESC)
- **2,145,991 stock transactions** (STR_STOCK_CARD)

Total: Over 2.5 million records!

## 🎯 Next Steps

1. Start the containers: `docker-compose up`
2. Open the frontend: http://localhost:8080
3. Start querying your data in English!

The application will automatically:
- Connect to SQL Server
- Get the schema
- Convert your questions to SQL
- Execute and return results

Enjoy querying your VikasAI database! 🎉

