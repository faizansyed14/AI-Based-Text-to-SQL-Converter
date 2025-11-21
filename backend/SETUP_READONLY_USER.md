# SQL Server Read-Only User Setup Guide

This guide will help you set up a read-only SQL Server user for enhanced security.

## Why Use a Read-Only User?

1. **Database-Level Protection**: Even if application code has bugs, the database user cannot write
2. **Defense in Depth**: Multiple layers of security (application + database)
3. **SQL Injection Protection**: Read-only user cannot execute write operations even if SQL injection occurs
4. **Compliance**: Meets security best practices for production systems

## Prerequisites

- SQL Server Management Studio (SSMS) or `sqlcmd` command-line tool
- Administrator access to SQL Server (sa account or sysadmin role)
- Access to the VikasAI database

## Setup Steps

### Step 1: Run the SQL Script

1. **Option A: Using SQL Server Management Studio (SSMS)**
   - Open SSMS and connect as administrator (sa)
   - Open the file `backend/setup_readonly_user.sql`
   - **IMPORTANT**: Change the password in the script (line 12)
   - Execute the script (F5)

2. **Option B: Using sqlcmd (Command Line)**
   ```bash
   sqlcmd -S localhost -U sa -P "YourCurrentSAPassword" -i backend/setup_readonly_user.sql
   ```

### Step 2: Update Environment Variables

Update your `.env` file or `docker-compose.yml` with the new credentials:

**Option A: Update `.env` file**
```env
SQLSERVER_USER=vikasai_readonly
SQLSERVER_PASSWORD=YourStrong@ReadOnlyPassw0rd!2024
```

**Option B: Update `docker-compose.yml`**
```yaml
environment:
  SQLSERVER_USER: ${SQLSERVER_USER:-vikasai_readonly}
  SQLSERVER_PASSWORD: ${SQLSERVER_PASSWORD:-YourStrong@ReadOnlyPassw0rd!2024}
```

### Step 3: Restart Backend

```bash
docker-compose restart backend
```

### Step 4: Verify Connection

1. Check backend logs:
   ```bash
   docker-compose logs backend | grep -i "sql server\|vikasai"
   ```

2. Test a query in the UI - it should work normally

3. Try to verify read-only status (optional):
   ```sql
   -- Connect as vikasai_readonly and try:
   INSERT INTO [EDC_BRAND] (BR_CODE, BR_DESC) VALUES ('TEST', 'TEST');
   -- This should fail with permission denied
   ```

## Security Features

### What the Read-Only User Can Do:
✅ Execute SELECT queries on all tables
✅ View database schema/metadata
✅ Read data from views
✅ Query system tables (for schema discovery)

### What the Read-Only User CANNOT Do:
❌ INSERT, UPDATE, DELETE operations
❌ CREATE, ALTER, DROP tables/views/procedures
❌ Execute stored procedures (unless explicitly granted)
❌ Modify database structure
❌ Access other databases (unless granted)

## SQL Injection Protection

The application has **multiple layers** of SQL injection protection:

1. **Application-Level Validation**:
   - `contains_write_operation()` - Blocks write keywords in user queries
   - `is_read_only_query()` - Validates SQL before execution
   - Only allows SELECT statements

2. **Database-Level Protection**:
   - Read-only user cannot execute write operations
   - Even if SQL injection bypasses application checks, database blocks it

3. **Parameterized Queries** (for future use):
   - The application uses direct SQL execution for dynamic queries
   - For user input in WHERE clauses, consider parameterized queries

## Current Protection Status

✅ **Application-level read-only enforcement** (already active)
✅ **SQL query validation** (already active)
✅ **Database-level read-only user** (after setup)

## Troubleshooting

### Issue: "Login failed for user 'vikasai_readonly'"
- **Solution**: Verify the password is correct in both SQL script and environment variables
- Check SQL Server authentication mode (should allow SQL Server authentication)

### Issue: "The SELECT permission was denied"
- **Solution**: Re-run the GRANT statements in the setup script
- Check if tables are in a different schema (not dbo)

### Issue: "Cannot connect to SQL Server"
- **Solution**: Verify SQL Server is running and accessible
- Check firewall rules and network connectivity
- Verify SQL Server allows remote connections

## Rollback

If you need to revert to the original `sa` user:

1. Update environment variables:
   ```env
   SQLSERVER_USER=sa
   SQLSERVER_PASSWORD=YourOriginalSAPassword
   ```

2. Restart backend:
   ```bash
   docker-compose restart backend
   ```

## Notes

- The read-only user is created at the **database level** (VikasAI), not server-wide
- All existing and future tables in the `dbo` schema will have SELECT permission
- The user can view metadata needed for schema discovery (required for the app to work)
- Password complexity requirements follow SQL Server policy settings

