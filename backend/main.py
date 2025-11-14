from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from dotenv import load_dotenv
import pandas as pd
import io
from datetime import datetime
import os

# Import refactored modules
from database.postgres import get_db_connection
from database.sqlserver import get_sqlserver_connection, check_sqlserver_connection
from services.schema_service import get_table_schema, set_selected_table, get_selected_table
from services.sql_service import generate_sql_query, execute_sql_query
from services.format_service import format_results
from models.schemas import (
    ChatMessage, ChatRequest, ChatResponse, ChatSessionResponse,
    ChatMessageResponse, ExcelTableResponse, TableSelectionRequest, HealthResponse
)
from routes import health, schema, auth

load_dotenv()

app = FastAPI(title="Text to SQL API - VikasAI Database")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configurations are now in database/postgres.py and database/sqlserver.py
# OpenAI client is now in services/sql_service.py

# Database schema (you can update this based on your actual schema)
DB_SCHEMA = os.getenv("DB_SCHEMA", """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_name VARCHAR(100),
    quantity INTEGER,
    price DECIMAL(10, 2),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")


# All Pydantic models are now in models/schemas.py


# Database and service functions are now imported from modules


# Schema and SQL service functions are now imported from services module
# All SQL generation, validation, and execution functions are in services/sql_service.py

# Include routers
app.include_router(health.router)
app.include_router(schema.router)
app.include_router(auth.router)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint that converts text to SQL and executes it"""
    try:
        session_id = request.session_id
        
        # Create new session if not provided
        if not session_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Generate title from first message (truncate to 50 chars)
            title = request.message[:50] if request.message else "New Chat"
            cursor.execute(
                "INSERT INTO chat_sessions (title) VALUES (%s) RETURNING id",
                (title,)
            )
            session_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
        else:
            # Update session updated_at
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (session_id,)
            )
            conn.commit()
            cursor.close()
            conn.close()
        
        # Save user message
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO chat_messages (session_id, role, content) 
               VALUES (%s, %s, %s) RETURNING id""",
            (session_id, 'user', request.message)
        )
        user_message_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Initialize formatted_result
        formatted_result = None
        
        # Get model from request (default to gpt-4o-mini)
        model = request.model if hasattr(request, 'model') and request.model else "gpt-4o-mini"
        
        # Log model selection
        print(f"\n{'='*60}")
        print(f"📝 User Query: {request.message[:100]}")
        print(f"🤖 Selected Model: {model}")
        print(f"{'='*60}\n")
        
        # Generate SQL query
        sql_query = generate_sql_query(request.message, request.conversation_history, model=model)
        
        # Check if query is invalid
        if sql_query is None:
            response_message = "I'm sorry, but that doesn't seem to be a valid database query. Please ask me questions about your VikasAI database, such as:\n- 'Show me all brands'\n- 'How many products are there?'\n- 'List products with their categories'\n- 'What are the top 10 products?'"
            data = None
            error = None
        elif sql_query == "INVALID_QUERY" or not sql_query.strip():
            response_message = "I couldn't understand your question as a database query. Could you please rephrase it? For example:\n- 'Show me all brands'\n- 'How many products are in the database?'\n- 'List all categories'"
            data = None
            error = None
        elif sql_query == "READ_ONLY_ERROR":
            response_message = "⚠️ **Read-Only Access**: You only have read-only access to the VikasAI database. Write operations like DELETE, UPDATE, INSERT, TRUNCATE, DROP, or ALTER are not allowed.\n\nYou can only query and view data using SELECT statements. Please ask questions like:\n- 'Show me all brands'\n- 'How many products are there?'\n- 'List products with their categories'"
            data = None
            error = "Read-only access: Write operations are not allowed"
        else:
            # Execute SQL query
            data, error = execute_sql_query(sql_query)
            
            # Format results if data exists
            if data and not error:
                formatted_result = format_results(data)
            
            # Prepare response message
            if error:
                # Check if it's a read-only error
                if "read-only" in error.lower() or "not allowed" in error.lower():
                    response_message = f"⚠️ **Read-Only Access**: {error}\n\nYou can only query and view data using SELECT statements. Write operations (DELETE, UPDATE, INSERT, TRUNCATE, DROP, ALTER, CREATE) are not permitted."
                else:
                    response_message = f"I generated a SQL query, but there was an error executing it: {error}"
            else:
                if len(data) == 0:
                    response_message = "The query executed successfully but returned no results."
                else:
                    response_message = f"Found {len(data):,} result{'s' if len(data) != 1 else ''}."
        
        # Save assistant message
        # Serialize data properly for JSONB (handle datetime and other non-serializable types)
        data_json = None
        if data:
            try:
                # Convert datetime objects to strings
                def json_serializer(obj):
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                    raise TypeError(f"Type {type(obj)} not serializable")
                data_json = json.dumps(data, default=json_serializer)
            except Exception as e:
                print(f"Error serializing data: {e}")
                data_json = json.dumps([])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # Only save SQL query if it was generated
        sql_query_to_save = sql_query if sql_query and sql_query != "INVALID_QUERY" else None
        cursor.execute(
            """INSERT INTO chat_messages (session_id, role, content, sql_query, data, error) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (session_id, 'assistant', response_message, sql_query_to_save, data_json, error)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session title if it's the first message (use first user message)
        if not request.session_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_sessions SET title = %s WHERE id = %s",
                (request.message[:50], session_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
        
        return ChatResponse(
            message=response_message,
            sql_query=sql_query if sql_query and sql_query != "INVALID_QUERY" else None,
            data=data if data is not None else [],
            formatted_html=formatted_result.get("formatted_html") if formatted_result else None,
            summary=formatted_result.get("summary") if formatted_result else None,
            session_id=session_id,
            error=error,
            model_name=model  # Include which model was actually used
        )
    except Exception as e:
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}",
            error=str(e),
            session_id=request.session_id
        )


# Schema endpoint is now in routes/schema.py


@app.post("/api/sessions", response_model=ChatSessionResponse)
async def create_session():
    """Create a new chat session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_sessions (title) VALUES (%s) RETURNING id, title, created_at, updated_at",
            ("New Chat",)
        )
        result = cursor.fetchone()
        session_id, title, created_at, updated_at = result
        conn.commit()
        cursor.close()
        conn.close()
        
        # Handle datetime objects properly
        created_at_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
        updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
        
        return ChatSessionResponse(
            id=session_id,
            title=title,
            created_at=created_at_str,
            updated_at=updated_at_str
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=List[ChatSessionResponse])
async def get_sessions():
    """Get all chat sessions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC"
        )
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for row in sessions:
            # Handle datetime objects properly
            created_at = row[2]
            updated_at = row[3]
            
            created_at_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
            updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
            
            result.append(ChatSessionResponse(
                id=row[0],
                title=row[1],
                created_at=created_at_str,
                updated_at=updated_at_str
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(session_id: int):
    """Get all messages for a chat session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, role, content, sql_query, data, error, timestamp 
               FROM chat_messages 
               WHERE session_id = %s 
               ORDER BY timestamp ASC""",
            (session_id,)
        )
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for row in messages:
            # Parse JSONB data if it exists
            data = row[4]
            parsed_data = None
            if data:
                if isinstance(data, str):
                    try:
                        parsed_data = json.loads(data)
                    except:
                        parsed_data = None
                else:
                    # PostgreSQL JSONB returns as dict/list already
                    parsed_data = data
                
                # Ensure data is a list
                if parsed_data is not None:
                    if isinstance(parsed_data, dict):
                        parsed_data = [parsed_data]
                    elif not isinstance(parsed_data, list):
                        parsed_data = [parsed_data] if parsed_data else None
            
            # Handle timestamp - ensure it's a datetime object before calling isoformat
            timestamp = row[6]
            if timestamp and hasattr(timestamp, 'isoformat'):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp) if timestamp else ""
            
            result.append(ChatMessageResponse(
                id=row[0],
                role=row[1],
                content=row[2],
                sql_query=row[3],
                data=parsed_data,
                error=row[5],
                timestamp=timestamp_str
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int):
    """Delete a chat session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Selected table is now managed in services/schema_service.py


def sanitize_table_name(name: str) -> str:
    """Convert string to valid PostgreSQL table name"""
    # Remove special characters, replace spaces with underscores
    name = "".join(c if c.isalnum() or c == '_' else '_' for c in name)
    # Remove leading numbers
    while name and name[0].isdigit():
        name = name[1:] or 'table'
    # Ensure it starts with a letter
    if not name or not name[0].isalpha():
        name = 'table_' + name
    # Limit length
    return name[:63].lower()


def check_table_exists(table_name: str) -> bool:
    """Check if table exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        exists = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"Error checking table: {str(e)}")
        return False


def get_table_columns(table_name: str) -> List[str]:
    """Get column names from existing table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns
    except Exception as e:
        print(f"Error getting columns: {str(e)}")
        return []


def create_table_from_excel(df: pd.DataFrame, table_name: str) -> int:
    """Create SQL table from pandas DataFrame"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate CREATE TABLE statement
        columns_sql = []
        for col in df.columns:
            # Determine column type
            dtype = str(df[col].dtype)
            if 'int' in dtype:
                sql_type = 'INTEGER'
            elif 'float' in dtype:
                sql_type = 'DECIMAL(10, 2)'
            elif 'bool' in dtype:
                sql_type = 'BOOLEAN'
            elif 'datetime' in dtype:
                sql_type = 'TIMESTAMP'
            else:
                sql_type = 'TEXT'
            
            col_name = sanitize_table_name(col)
            columns_sql.append(f'"{col_name}" {sql_type}')
        
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns_sql)})'
        cursor.execute(create_sql)
        conn.commit()
        
        # Insert data
        row_count = 0
        for _, row in df.iterrows():
            col_names = [sanitize_table_name(col) for col in df.columns]
            placeholders = ', '.join(['%s'] * len(col_names))
            col_names_quoted = ', '.join([f'"{c}"' for c in col_names])
            insert_sql = f'INSERT INTO "{table_name}" ({col_names_quoted}) VALUES ({placeholders})'
            
            values = []
            for val in row:
                if pd.isna(val):
                    values.append(None)
                elif isinstance(val, pd.Timestamp):
                    values.append(val.to_pydatetime())
                else:
                    values.append(val)
            
            cursor.execute(insert_sql, tuple(values))
            row_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        return row_count
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise Exception(f"Error creating table: {str(e)}")


def append_to_table(df: pd.DataFrame, table_name: str) -> int:
    """Append data to existing table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        row_count = 0
        col_names = [sanitize_table_name(col) for col in df.columns]
        placeholders = ', '.join(['%s'] * len(col_names))
        col_names_quoted = ', '.join([f'"{c}"' for c in col_names])
        insert_sql = f'INSERT INTO "{table_name}" ({col_names_quoted}) VALUES ({placeholders})'
        
        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append(None)
                elif isinstance(val, pd.Timestamp):
                    values.append(val.to_pydatetime())
                else:
                    values.append(val)
            
            cursor.execute(insert_sql, tuple(values))
            row_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        return row_count
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise Exception(f"Error appending to table: {str(e)}")


@app.post("/api/upload-excel", response_model=ExcelTableResponse)
async def upload_excel(file: UploadFile = File(...)):
    """Upload Excel file and convert to SQL table"""
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file is empty")
        
        # Get column names
        columns = [str(col) for col in df.columns]
        
        # Generate table name from filename
        file_name = file.filename or "uploaded_file"
        base_name = os.path.splitext(file_name)[0]
        table_name = sanitize_table_name(base_name)
        
        # Check if table with same columns exists
        existing_table = None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, columns 
            FROM excel_tables
        """)
        for row in cursor.fetchall():
            existing_table_name, existing_columns_json = row
            existing_columns = json.loads(existing_columns_json) if isinstance(existing_columns_json, str) else existing_columns_json
            # Normalize column names for comparison
            normalized_existing = [sanitize_table_name(c).lower() for c in existing_columns]
            normalized_new = [sanitize_table_name(c).lower() for c in columns]
            if set(normalized_existing) == set(normalized_new):
                existing_table = existing_table_name
                break
        cursor.close()
        conn.close()
        
        # Create or append to table
        if existing_table and check_table_exists(existing_table):
            row_count = append_to_table(df, existing_table)
            table_name = existing_table
            action = "appended"
        else:
            # Ensure unique table name
            original_name = table_name
            counter = 1
            while check_table_exists(table_name):
                table_name = f"{original_name}_{counter}"
                counter += 1
            
            row_count = create_table_from_excel(df, table_name)
            action = "created"
        
        # Update excel_tables metadata
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total row count
        count_sql = f'SELECT COUNT(*) FROM "{table_name}"'
        cursor.execute(count_sql)
        total_rows = cursor.fetchone()[0]
        
        # Insert or update metadata
        cursor.execute("""
            INSERT INTO excel_tables (table_name, file_name, columns, row_count, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (table_name) 
            DO UPDATE SET 
                row_count = %s,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, created_at, updated_at
        """, (table_name, file_name, json.dumps(columns), total_rows, total_rows))
        
        result = cursor.fetchone()
        table_id, created_at, updated_at = result
        conn.commit()
        cursor.close()
        conn.close()
        
        return ExcelTableResponse(
            id=table_id,
            table_name=table_name,
            file_name=file_name,
            columns=columns,
            row_count=total_rows,
            created_at=created_at.isoformat(),
            updated_at=updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Excel file: {str(e)}")


@app.get("/api/excel-tables", response_model=List[ExcelTableResponse])
async def get_excel_tables():
    """Get all uploaded Excel tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, table_name, file_name, columns, row_count, created_at, updated_at
            FROM excel_tables
            ORDER BY updated_at DESC
        """)
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for row in tables:
            table_id, table_name, file_name, columns_json, row_count, created_at, updated_at = row
            columns = json.loads(columns_json) if isinstance(columns_json, str) else columns_json
            
            result.append(ExcelTableResponse(
                id=table_id,
                table_name=table_name,
                file_name=file_name,
                columns=columns,
                row_count=row_count,
                created_at=created_at.isoformat(),
                updated_at=updated_at.isoformat()
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/select-table")
async def select_table(request: TableSelectionRequest):
    """Select a table for querying"""
    if request.table_name:
        # Verify table exists
        if not check_table_exists(request.table_name):
            raise HTTPException(status_code=404, detail="Table not found")
        set_selected_table(request.table_name)
    else:
        set_selected_table(None)
    
    return {"selected_table": get_selected_table()}


@app.get("/api/selected-table")
async def get_selected_table_endpoint():
    """Get currently selected table"""
    return {"selected_table": get_selected_table()}


@app.get("/api/excel-tables/{table_name}/schema")
async def get_table_schema_for_table(table_name: str):
    """Get schema for a specific table"""
    try:
        if not check_table_exists(table_name):
            raise HTTPException(status_code=404, detail="Table not found")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        cursor.close()
        conn.close()
        
        schema = [
            {"name": col[0], "type": col[1], "nullable": col[2]}
            for col in columns
        ]
        
        return {"table_name": table_name, "columns": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/excel-tables/{table_name}")
async def delete_excel_table(table_name: str):
    """Delete an Excel table and its metadata"""
    try:
        global selected_table_name
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists in metadata
        cursor.execute("SELECT id FROM excel_tables WHERE table_name = %s", (table_name,))
        table_record = cursor.fetchone()
        
        if not table_record:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Table not found in metadata")
        
        # Drop the actual table
        if check_table_exists(table_name):
            drop_sql = f'DROP TABLE IF EXISTS "{table_name}"'
            cursor.execute(drop_sql)
        
        # Delete metadata
        cursor.execute("DELETE FROM excel_tables WHERE table_name = %s", (table_name,))
        
        # If this was the selected table, clear selection
        if selected_table_name == table_name:
            selected_table_name = None
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"Table '{table_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting table: {str(e)}")

