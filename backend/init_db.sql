-- Database schema for Text to SQL application
-- This PostgreSQL database is used ONLY for app metadata (chat sessions, messages, Excel uploads)
-- The actual business data is stored in SQL Server (VikasAI database)

-- Note: All dummy/test data tables have been removed
-- The application now connects to SQL Server for business data queries

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    sql_query TEXT,
    data JSONB,
    error TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create excel_tables table to track uploaded Excel sheets
CREATE TABLE IF NOT EXISTS excel_tables (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) UNIQUE NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    columns JSONB NOT NULL,
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);