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
from services.analysis_service import detect_analysis_request, analyze_data_with_gpt
from services.visualization_service import detect_visualization_request, determine_chart_type, prepare_chart_data
from decimal import Decimal
from models.schemas import (
    ChatMessage, ChatRequest, ChatResponse, ChatSessionResponse,
    ChatMessageResponse, ExcelTableResponse, TableSelectionRequest, HealthResponse,
    VisualizationRequest
)
from routes import health, schema, auth, analytics

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
app.include_router(analytics.router)


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
        
        # Initialize formatted_result and total_count
        formatted_result = None
        total_count = None
        data = None
        error = None
        show_visualization = False
        chart_config = None
        
        # Get model from request (default to gpt-4o-mini)
        # Ensure model is valid, fallback to default if not provided or invalid
        model = request.model if request.model and request.model.strip() else "gpt-4o-mini"
        
        # Validate model is in supported models list
        from services.model_service import SUPPORTED_MODELS
        if model not in SUPPORTED_MODELS:
            print(f"⚠️ Warning: Model '{model}' not in supported models, defaulting to 'gpt-4o-mini'")
            model = "gpt-4o-mini"
        
        # Check if user is requesting analysis of previous response
        is_analysis_request = detect_analysis_request(request.message)
        
        # Check if user is requesting visualization of previous response
        is_visualization_request = detect_visualization_request(request.message)
        
        # Log model selection
        print(f"\n{'='*60}")
        print(f"📝 User Query: {request.message[:100]}")
        print(f"🤖 Selected Model: {model}")
        print(f"📥 Received Model from Request: {request.model}")
        if is_analysis_request:
            print(f"📊 Analysis Request Detected")
        if is_visualization_request:
            print(f"📈 Visualization Request Detected")
        print(f"{'='*60}\n")
        
        # If this is a visualization request (pure visualization, not combined with query), get the last assistant message's data
        # Check if message is ONLY visualization (no query keywords)
        query_keywords = ['top', 'all', 'list', 'find', 'get', 'select', 'how many', 'what', 'which', 'where', 'when', 'show me', 'show all']
        has_query_keywords = any(keyword in request.message.lower() for keyword in query_keywords)
        is_pure_visualization = is_visualization_request and not has_query_keywords
        
        if is_pure_visualization and not is_analysis_request:
            # Get the last assistant message from the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT content, sql_query, data 
                   FROM chat_messages 
                   WHERE session_id = %s AND role = 'assistant' 
                   ORDER BY id DESC 
                   LIMIT 1""",
                (session_id,)
            )
            last_message = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if last_message and last_message[2]:  # last_message[2] is the data field
                try:
                    # Parse the data (it's stored as JSONB string)
                    last_data_raw = last_message[2]
                    print(f"📊 Raw data type: {type(last_data_raw)}")
                    
                    if isinstance(last_data_raw, str):
                        last_data = json.loads(last_data_raw)
                    elif isinstance(last_data_raw, (list, dict)):
                        last_data = last_data_raw
                    else:
                        # Try to parse if it's bytes or other type
                        try:
                            last_data = json.loads(str(last_data_raw))
                        except:
                            last_data = last_data_raw
                    
                    last_sql_query = last_message[1]  # The SQL query that generated the data
                    
                    # Ensure last_data is a list
                    if not isinstance(last_data, list):
                        if isinstance(last_data, dict):
                            last_data = [last_data]
                        else:
                            last_data = []
                    
                    print(f"📊 Parsed data: {len(last_data) if isinstance(last_data, list) else 0} rows")
                    print(f"📊 First row sample: {last_data[0] if last_data else 'No data'}")
                    
                    if last_data and len(last_data) > 0:
                        print(f"📊 Visualizing {len(last_data)} rows from previous response...")
                        
                        # Determine chart type and prepare chart data
                        # Column selection is now handled via UI dropdown, so we don't extract from text
                        chart_type = determine_chart_type(last_data)
                        print(f"📊 Determined chart type: {chart_type}")
                        
                        if chart_type:
                            chart_config = prepare_chart_data(last_data, chart_type, None, None, None)
                            show_visualization = True
                            print(f"📊 Chart config prepared: {chart_config.get('type') if chart_config else 'None'}")
                            print(f"📊 Selected numeric columns: {chart_config.get('numericColumns', []) if chart_config else 'None'}")
                            
                            # Format results
                            formatted_result = format_results(last_data)
                            
                            # Return visualization response
                            response_message = f"📈 **Visualization of previous query results**"
                            sql_query = last_sql_query
                            data = last_data
                            error = None
                        else:
                            response_message = "I couldn't determine an appropriate chart type for this data. The data may not be suitable for visualization."
                            sql_query = last_sql_query
                            data = last_data
                            error = None
                            show_visualization = False
                            chart_config = None
                    else:
                        response_message = "I couldn't find any data from the previous response to visualize. Please ask a question first to get some data."
                        sql_query = None
                        data = None
                        formatted_result = None
                        error = None
                        show_visualization = False
                        chart_config = None
                except Exception as e:
                    print(f"Error visualizing previous data: {e}")
                    response_message = f"Sorry, I encountered an error while visualizing the previous data: {str(e)}"
                    sql_query = None
                    data = None
                    formatted_result = None
                    error = None
                    show_visualization = False
                    chart_config = None
            else:
                response_message = "I couldn't find any previous response with data to visualize. Please ask a question first to get some data, then ask me to visualize it."
                sql_query = None
                data = None
                formatted_result = None
                error = None
                show_visualization = False
                chart_config = None
        
        # If this is an analysis request, get the last assistant message's data
        elif is_analysis_request:
            # Get the last assistant message from the database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """SELECT content, sql_query, data 
                   FROM chat_messages 
                   WHERE session_id = %s AND role = 'assistant' 
                   ORDER BY id DESC 
                   LIMIT 1""",
                (session_id,)
            )
            last_message = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if last_message and last_message[2]:  # last_message[2] is the data field
                try:
                    # Parse the data (it's stored as JSONB string)
                    last_data = json.loads(last_message[2]) if isinstance(last_message[2], str) else last_message[2]
                    last_sql_query = last_message[1]  # The SQL query that generated the data
                    
                    # Get the original user question that generated this data
                    # Look for the user message before this assistant message
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """SELECT content 
                           FROM chat_messages 
                           WHERE session_id = %s AND role = 'user' 
                           AND id < (SELECT id FROM chat_messages WHERE session_id = %s AND role = 'assistant' ORDER BY id DESC LIMIT 1)
                           ORDER BY id DESC 
                           LIMIT 1""",
                        (session_id, session_id)
                    )
                    original_question_row = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    original_question = original_question_row[0] if original_question_row else "the previous query"
                    
                    if last_data and len(last_data) > 0:
                        print(f"📊 Analyzing {len(last_data)} rows from previous response...")
                        print(f"📝 Original Question: {original_question}")
                        print(f"📝 New Analysis Question: {request.message}")
                        
                        try:
                            # Analyze the data - pass both the original question and the new analysis question
                            analysis_text = analyze_data_with_gpt(
                                data=last_data,
                                user_question=original_question,
                                analysis_question=request.message,  # The NEW question the user is asking
                                model=model
                            )
                            
                            print(f"✅ Analysis completed")
                            
                            # Return analysis as response
                            response_message = f"📊 **Data Analysis:**\n\n{analysis_text}"
                            sql_query = None
                            data = None
                            formatted_result = None
                            error = None
                        except Exception as analysis_error:
                            print(f"❌ Error during analysis: {analysis_error}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
                            # Return error message instead of crashing
                            response_message = f"Sorry, I encountered an error while analyzing the data: {str(analysis_error)}. Please try again."
                            sql_query = None
                            data = None
                            formatted_result = None
                            error = str(analysis_error)
                    else:
                        response_message = "I couldn't find any data from the previous response to analyze. Please ask a question first to get some data."
                        sql_query = None
                        data = None
                        formatted_result = None
                        error = None
                except Exception as e:
                    print(f"Error analyzing previous data: {e}")
                    response_message = f"Sorry, I encountered an error while analyzing the previous data: {str(e)}"
                    sql_query = None
                    data = None
                    formatted_result = None
                    error = None
            else:
                response_message = "I couldn't find any previous response with data to analyze. Please ask a question first to get some data, then ask me to analyze it."
                sql_query = None
                data = None
                formatted_result = None
                error = None
        else:
            # Check if message contains a direct SQL query (e.g., "Execute this query and show all results: SELECT...")
            # This handles the "Show All Records" button case
            direct_sql_match = None
            if "execute this query" in request.message.lower() or "show all results:" in request.message.lower():
                # Try to extract SQL query from message
                import re
                # Look for SELECT statement in the message
                select_match = re.search(r'(SELECT\s+.*?)(?:\s*;|$)', request.message, re.IGNORECASE | re.DOTALL)
                if select_match:
                    direct_sql_match = select_match.group(1).strip()
                    # Remove TOP clause if present to get all records
                    direct_sql_match = re.sub(r'\bTOP\s+\d+\b', '', direct_sql_match, flags=re.IGNORECASE).strip()
                    print(f"📋 Extracted direct SQL query: {direct_sql_match[:100]}...")
            
            if direct_sql_match:
                # Use the extracted SQL directly
                sql_query = direct_sql_match
            else:
                # Generate SQL query (normal flow)
                sql_query = generate_sql_query(request.message, request.conversation_history, model=model)
            
            # Check if response is a logical answer (explanation, comparison, etc.)
            if sql_query and sql_query.strip().startswith("LOGICAL_ANSWER:"):
                logical_text = sql_query.replace("LOGICAL_ANSWER:", "").strip()
                response_message = logical_text
                sql_query = None  # No SQL query for logical answers
                data = None
                formatted_result = None
                error = None
            # Check if response is a clarification request
            elif sql_query and sql_query.strip().startswith("CLARIFICATION_NEEDED:"):
                clarification_text = sql_query.replace("CLARIFICATION_NEEDED:", "").strip()
                response_message = clarification_text
                sql_query = None  # No SQL query for clarification
                data = None
                formatted_result = None
                error = None
            # Check if query is invalid
            elif sql_query is None:
                response_message = "I'm sorry, but that doesn't seem to be a valid database query. Please ask me questions about your VikasAI database, such as:\n- 'Show me all brands'\n- 'How many products are there?'\n- 'List products with their categories'\n- 'What are the top 10 products?'"
            elif sql_query == "INVALID_QUERY" or not sql_query.strip():
                response_message = "I couldn't understand your question as a database query. Could you please rephrase it? For example:\n- 'Show me all brands'\n- 'How many products are in the database?'\n- 'List all categories'"
            elif sql_query == "READ_ONLY_ERROR":
                response_message = "⚠️ **Read-Only Access**: You only have read-only access to the VikasAI database. Write operations like DELETE, UPDATE, INSERT, TRUNCATE, DROP, or ALTER are not allowed.\n\nYou can only query and view data using SELECT statements. Please ask questions like:\n- 'Show me all brands'\n- 'How many products are there?'\n- 'List products with their categories'"
                error = "Read-only access: Write operations are not allowed"
            else:
                # Check if user is requesting all records (explicit request)
                request_all = "show all" in request.message.lower() or "execute this query and show all" in request.message.lower()
                limit = 0 if request_all else 1000  # 0 means no limit
                
                # Execute SQL query
                data, error, total_count = execute_sql_query(sql_query, limit=limit)
                
                # Format results if data exists
                if data and not error:
                    formatted_result = format_results(data)
                
                # Check if user requested visualization in the same query (e.g., "show top 10 products in graph")
                # This is different from "show me in graph" which visualizes previous response
                if data and not error and detect_visualization_request(request.message):
                    # Only visualize if this wasn't already handled as a "visualize previous" request
                    # Check if the message contains actual query keywords (not just visualization keywords)
                    query_keywords = ['show', 'list', 'find', 'get', 'select', 'top', 'all', 'how many', 'what']
                    has_query_keywords = any(keyword in request.message.lower() for keyword in query_keywords)
                    
                    # If message has query keywords, it's a combined query+visualization request
                    # If it only has visualization keywords, it should have been handled above
                    if has_query_keywords:
                        # Column selection is now handled via UI dropdown, so we don't extract from text
                        show_visualization = True
                        chart_type = determine_chart_type(data)
                        if chart_type:
                            chart_config = prepare_chart_data(data, chart_type, None, None, None)
                            print(f"📊 Visualization requested in query: Chart type = {chart_type}")
                
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
                        # Check if there are more records than displayed
                        if len(data) >= 1000:
                            if total_count and total_count > 1000:
                                response_message = f"Showing 1,000 of {total_count:,} results. Would you like to see all records?"
                            else:
                                response_message = f"Showing 1,000 results. There may be more records. Would you like to see all?"
                        else:
                            response_message = f"Found {len(data):,} result{'s' if len(data) != 1 else ''}."
        
        # Save assistant message
        # Serialize data properly for JSONB (handle datetime, decimal, and other non-serializable types)
        data_json = None
        if data:
            try:
                # Convert datetime objects and decimal objects to strings/numbers
                def json_serializer(obj):
                    if hasattr(obj, 'isoformat'):  # datetime objects
                        return obj.isoformat()
                    # Handle decimal.Decimal from SQL Server
                    if isinstance(obj, Decimal):
                        return float(obj)
                    raise TypeError(f"Type {type(obj)} not serializable")
                data_json = json.dumps(data, default=json_serializer)
            except Exception as e:
                print(f"Error serializing data: {e}")
                # Fallback: convert decimals manually
                try:
                    import copy
                    data_copy = copy.deepcopy(data)
                    for row in data_copy:
                        for key, value in row.items():
                            if isinstance(value, Decimal):
                                row[key] = float(value)
                    data_json = json.dumps(data_copy, default=lambda obj: obj.isoformat() if hasattr(obj, 'isoformat') else str(obj))
                except Exception as e2:
                    print(f"Error in fallback serialization: {e2}")
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
        
        # Determine if there are more records
        has_more = False
        if data and len(data) >= 1000:
            has_more = True
        
        # Ensure chart_config is JSON serializable
        chart_config_serializable = None
        if chart_config:
            try:
                # Convert chart_config to a dict that's JSON serializable
                chart_config_serializable = {
                    'type': chart_config.get('type'),
                    'dateColumn': chart_config.get('dateColumn'),
                    'numericColumns': chart_config.get('numericColumns', []),
                    'categoryColumns': chart_config.get('categoryColumns', []),
                    'columns': chart_config.get('columns', []),
                    'xAxisColumn': chart_config.get('xAxisColumn'),
                    'yAxisColumn': chart_config.get('yAxisColumn')
                }
                print(f"📊 Chart config serialized: {chart_config_serializable}")
            except Exception as e:
                print(f"⚠️ Error serializing chart_config: {e}")
                chart_config_serializable = None
        
        # Extract available columns from data for visualization selector
        available_columns = None
        if data and len(data) > 0:
            available_columns = list(data[0].keys())
        
        print(f"📊 Final response - show_visualization: {show_visualization}, chart_config: {chart_config_serializable is not None}, data length: {len(data) if data else 0}")
        
        return ChatResponse(
            message=response_message,
            sql_query=sql_query if sql_query and sql_query != "INVALID_QUERY" else None,
            data=data if data is not None else [],
            formatted_html=formatted_result.get("formatted_html") if formatted_result else None,
            summary=formatted_result.get("summary") if formatted_result else None,
            session_id=session_id,
            error=error,
            model_name=model,  # Include which model was actually used
            has_more_records=has_more,
            total_count=total_count if total_count else None,
            show_visualization=show_visualization,
            chart_config=chart_config_serializable,
            available_columns=available_columns
        )
    except Exception as e:
        # Get model from request for error response too
        model = request.model if hasattr(request, 'model') and request.model and request.model.strip() else "gpt-4o-mini"
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}",
            error=str(e),
            session_id=request.session_id,
            model_name=model
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


@app.post("/api/visualize", response_model=ChatResponse)
async def create_visualization(request: VisualizationRequest):
    """Create visualization from last response data with selected columns"""
    try:
        # Get the last assistant message from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT content, sql_query, data 
               FROM chat_messages 
               WHERE session_id = %s AND role = 'assistant' 
               ORDER BY id DESC 
               LIMIT 1""",
            (request.session_id,)
        )
        last_message = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not last_message or not last_message[2]:
            raise HTTPException(status_code=404, detail="No previous data found to visualize")
        
        # Parse the data
        last_data_raw = last_message[2]
        if isinstance(last_data_raw, str):
            last_data = json.loads(last_data_raw)
        elif isinstance(last_data_raw, (list, dict)):
            last_data = last_data_raw
        else:
            last_data = json.loads(str(last_data_raw))
        
        # Ensure last_data is a list
        if not isinstance(last_data, list):
            if isinstance(last_data, dict):
                last_data = [last_data]
            else:
                last_data = []
        
        if not last_data or len(last_data) == 0:
            raise HTTPException(status_code=404, detail="No data available for visualization")
        
        # Prepare chart data with selected columns
        chart_type = request.chart_type or determine_chart_type(last_data) or "trend"
        chart_config = prepare_chart_data(
            last_data, 
            chart_type, 
            None, 
            request.x_axis_column, 
            request.y_axis_column
        )
        
        # Format results
        formatted_result = format_results(last_data)
        
        # Serialize chart config
        chart_config_serializable = {
            'type': chart_config.get('type'),
            'dateColumn': chart_config.get('dateColumn'),
            'numericColumns': chart_config.get('numericColumns', []),
            'categoryColumns': chart_config.get('categoryColumns', []),
            'columns': chart_config.get('columns', []),
            'xAxisColumn': chart_config.get('xAxisColumn'),
            'yAxisColumn': chart_config.get('yAxisColumn')
        }
        
        # Get available columns
        available_columns = list(last_data[0].keys()) if last_data else None
        
        return ChatResponse(
            message="📈 **Visualization with selected columns**",
            sql_query=last_message[1],
            data=last_data,
            formatted_html=formatted_result.get("formatted_html") if formatted_result else None,
            summary=formatted_result.get("summary") if formatted_result else None,
            session_id=request.session_id,
            error=None,
            model_name="visualization",
            has_more_records=False,
            total_count=len(last_data),
            show_visualization=True,
            chart_config=chart_config_serializable,
            available_columns=available_columns
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating visualization: {str(e)}")

