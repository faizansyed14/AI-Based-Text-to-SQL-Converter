# Read-Only Access Security Implementation

## Overview

The application now enforces **read-only access** to the SQL Server database. Users can only execute SELECT queries - all write operations are blocked.

## Security Features Implemented

### 1. **Backend Query Validation** (`backend/services/sql_service.py`)

#### Function: `is_read_only_query()`
- ✅ Checks if query starts with `SELECT`
- ✅ Blocks dangerous keywords: `DELETE`, `TRUNCATE`, `DROP`, `INSERT`, `UPDATE`, `ALTER`, `CREATE`, `EXEC`, `EXECUTE`, `SP_`, `XP_`, `GRANT`, `REVOKE`, `MERGE`, `BULK INSERT`, `BACKUP`, `RESTORE`, `DBCC`
- ✅ Removes SQL comments before checking (prevents comment-based bypass)
- ✅ Blocks multiple statements (semicolon-separated)
- ✅ Returns user-friendly error messages

#### Function: `execute_sql_query()`
- ✅ Validates query before execution
- ✅ Only executes if query passes read-only validation
- ✅ Returns clear error messages for blocked operations

### 2. **GPT Prompt Enhancement** (`backend/services/sql_service.py`)

The system prompt now includes:
```
8. **CRITICAL: READ-ONLY ACCESS ONLY**
   - You can ONLY generate SELECT queries
   - NEVER generate DELETE, TRUNCATE, DROP, INSERT, UPDATE, ALTER, CREATE, or any write operations
   - If the user asks to delete, update, modify, or change data, return "READ_ONLY_ERROR" instead of a query
   - The database has read-only access - only SELECT statements are allowed
```

**Examples added:**
- "Delete all brands" → `READ_ONLY_ERROR`
- "Update product prices" → `READ_ONLY_ERROR`
- "Drop table EDC_BRAND" → `READ_ONLY_ERROR`

### 3. **Backend Error Handling** (`backend/main.py`)

- ✅ Detects `READ_ONLY_ERROR` from GPT
- ✅ Detects read-only errors from query validation
- ✅ Returns user-friendly messages with examples
- ✅ Shows warning emoji (⚠️) for read-only errors

### 4. **Frontend Error Display** (`frontend/src/components/Message.tsx`)

- ✅ Special styling for read-only errors
- ✅ Lock icon (🔒) for visual indication
- ✅ Clear explanation of restrictions
- ✅ Suggestion box with allowed operations

## Blocked Operations

The following SQL operations are **completely blocked**:

| Operation | Purpose | Status |
|-----------|---------|--------|
| `DELETE` | Delete rows | ❌ Blocked |
| `TRUNCATE` | Delete all rows | ❌ Blocked |
| `DROP` | Delete tables/databases | ❌ Blocked |
| `INSERT` | Add new rows | ❌ Blocked |
| `UPDATE` | Modify existing rows | ❌ Blocked |
| `ALTER` | Modify table structure | ❌ Blocked |
| `CREATE` | Create new tables/objects | ❌ Blocked |
| `EXEC` / `EXECUTE` | Execute stored procedures | ❌ Blocked |
| `GRANT` / `REVOKE` | Permission management | ❌ Blocked |
| `MERGE` | Upsert operations | ❌ Blocked |
| `BULK INSERT` | Bulk data import | ❌ Blocked |
| `BACKUP` / `RESTORE` | Database backup/restore | ❌ Blocked |
| `DBCC` | Database console commands | ❌ Blocked |

## Allowed Operations

Only **SELECT queries** are allowed:

| Operation | Purpose | Status |
|-----------|---------|--------|
| `SELECT` | Query and view data | ✅ Allowed |
| `SELECT ... WHERE` | Filter data | ✅ Allowed |
| `SELECT ... JOIN` | Join tables | ✅ Allowed |
| `SELECT ... GROUP BY` | Aggregate data | ✅ Allowed |
| `SELECT ... ORDER BY` | Sort data | ✅ Allowed |
| `SELECT ... TOP N` | Limit results | ✅ Allowed |
| `SELECT COUNT(*)` | Count records | ✅ Allowed |
| `SELECT ... UNION` | Combine queries | ✅ Allowed |

## Security Layers

### Layer 1: GPT Prompt
- GPT is instructed to never generate write queries
- Returns `READ_ONLY_ERROR` for write requests

### Layer 2: Query Validation
- Backend validates every query before execution
- Checks for dangerous keywords
- Validates query structure

### Layer 3: Execution
- Only validated queries are executed
- Connection is read-only at application level

## User Experience

### When User Tries Write Operation:

**Example 1: "Delete all brands"**
```
⚠️ Read-Only Access: You only have read-only access to the VikasAI database. 
Write operations like DELETE, UPDATE, INSERT, TRUNCATE, DROP, or ALTER are not allowed.

You can only query and view data using SELECT statements. 
Please ask questions like:
- 'Show me all brands'
- 'How many products are there?'
- 'List products with their categories'
```

**Example 2: "Update product prices"**
```
⚠️ Read-Only Access: Write operations like 'UPDATE' are not allowed. 
You have read-only access to the VikasAI database.

You can only query and view data using SELECT statements. 
Write operations (DELETE, UPDATE, INSERT, TRUNCATE, DROP, ALTER, CREATE) are not permitted.
```

## Testing

To test the security:

1. **Try DELETE:**
   - Ask: "Delete all brands"
   - Expected: Read-only error message

2. **Try UPDATE:**
   - Ask: "Update all product prices to 100"
   - Expected: Read-only error message

3. **Try DROP:**
   - Ask: "Drop the EDC_BRAND table"
   - Expected: Read-only error message

4. **Try SELECT (should work):**
   - Ask: "Show me all brands"
   - Expected: Data displayed successfully

## Code Locations

- **Query Validation:** `backend/services/sql_service.py` (lines 170-228)
- **GPT Prompt:** `backend/services/sql_service.py` (lines 108-143)
- **Error Handling:** `backend/main.py` (lines 130-148)
- **Frontend Display:** `frontend/src/components/Message.tsx` (lines 154-173)
- **Frontend Styling:** `frontend/src/components/Message.css` (lines 364-406)

## Summary

✅ **Read-only access enforced**  
✅ **Multiple security layers**  
✅ **User-friendly error messages**  
✅ **GPT instructed to prevent write queries**  
✅ **Frontend displays clear warnings**  

The database is now fully protected against write operations while maintaining full read access for queries.

