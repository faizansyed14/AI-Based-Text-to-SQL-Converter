#!/usr/bin/env python3
"""
Python script to set up SQL Server read-only user
Uses pymssql to connect and execute the SQL script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymssql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQL Server admin credentials (to create the readonly user)
SQLSERVER_HOST = os.getenv("SQLSERVER_HOST", "localhost")
SQLSERVER_PORT = int(os.getenv("SQLSERVER_PORT", "1433"))
SQLSERVER_DB = os.getenv("SQLSERVER_DB", "VikasAI")
SQL_ADMIN_USER = "sa"
SQL_ADMIN_PASSWORD = "YourStrong@Passw0rd"  # Current admin password

# Read-only user credentials (from .env)
READONLY_USER = "vikasai_readonly"
READONLY_PASSWORD = "Zak@12345"  # Based on AUTH_PASSWORD, extended to meet SQL Server policy (min 8 chars)

def execute_sql(conn, sql, description):
    """Execute SQL statement and print result"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print(f"✓ {description}")
        cursor.close()
        return True
    except Exception as e:
        print(f"✗ {description}: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("SQL Server Read-Only User Setup")
    print("=" * 50)
    print()
    print(f"Connecting to: {SQLSERVER_HOST}:{SQLSERVER_PORT}")
    print(f"Database: {SQLSERVER_DB}")
    print(f"Admin User: {SQL_ADMIN_USER}")
    print(f"Creating Read-Only User: {READONLY_USER}")
    print(f"Read-Only Password: {READONLY_PASSWORD}")
    print()
    
    try:
        # Connect as admin
        conn = pymssql.connect(
            server=SQLSERVER_HOST,
            port=SQLSERVER_PORT,
            user=SQL_ADMIN_USER,
            password=SQL_ADMIN_PASSWORD,
            database="master",
            timeout=10
        )
        print("✓ Connected to SQL Server")
        print()
        
        # Step 1: Create Login
        print("Step 1: Creating login...")
        create_login_sql = f"""
        IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{READONLY_USER}')
        BEGIN
            CREATE LOGIN [{READONLY_USER}] 
            WITH PASSWORD = '{READONLY_PASSWORD}',
                 DEFAULT_DATABASE = [{SQLSERVER_DB}],
                 CHECK_EXPIRATION = OFF,
                 CHECK_POLICY = ON
        END
        """
        execute_sql(conn, create_login_sql, "Login created")
        
        # Step 2: Switch to VikasAI database
        conn.close()
        conn = pymssql.connect(
            server=SQLSERVER_HOST,
            port=SQLSERVER_PORT,
            user=SQL_ADMIN_USER,
            password=SQL_ADMIN_PASSWORD,
            database=SQLSERVER_DB,
            timeout=10
        )
        
        # Step 3: Create User
        print()
        print("Step 2: Creating user in database...")
        create_user_sql = f"""
        IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{READONLY_USER}')
        BEGIN
            CREATE USER [{READONLY_USER}] FOR LOGIN [{READONLY_USER}]
        END
        """
        execute_sql(conn, create_user_sql, "User created")
        
        # Step 4: Grant SELECT permissions
        print()
        print("Step 3: Granting SELECT permissions...")
        
        # Grant SELECT on schema (for all current and future tables)
        execute_sql(conn, f"GRANT SELECT ON SCHEMA::[dbo] TO [{READONLY_USER}]", "SELECT granted on schema")
        
        # Grant SELECT on all existing tables
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 'GRANT SELECT ON [' + TABLE_SCHEMA + '].[' + TABLE_NAME + '] TO [{READONLY_USER}]'
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        grant_statements = cursor.fetchall()
        
        for (grant_stmt,) in grant_statements:
            try:
                cursor.execute(grant_stmt)
                conn.commit()
            except Exception as e:
                print(f"  ⚠ Warning: {str(e)}")
        
        print(f"✓ SELECT permission granted on {len(grant_statements)} tables")
        cursor.close()
        
        # Step 5: Grant metadata viewing permissions
        print()
        print("Step 4: Granting metadata permissions...")
        execute_sql(conn, f"GRANT VIEW DEFINITION ON SCHEMA::[dbo] TO [{READONLY_USER}]", "VIEW DEFINITION granted")
        execute_sql(conn, f"GRANT VIEW ANY DEFINITION TO [{READONLY_USER}]", "VIEW ANY DEFINITION granted")
        
        # Step 6: Deny write operations
        print()
        print("Step 5: Denying write operations...")
        execute_sql(conn, f"DENY INSERT ON SCHEMA::[dbo] TO [{READONLY_USER}]", "INSERT denied")
        execute_sql(conn, f"DENY UPDATE ON SCHEMA::[dbo] TO [{READONLY_USER}]", "UPDATE denied")
        execute_sql(conn, f"DENY DELETE ON SCHEMA::[dbo] TO [{READONLY_USER}]", "DELETE denied")
        execute_sql(conn, f"DENY ALTER ON SCHEMA::[dbo] TO [{READONLY_USER}]", "ALTER denied")
        execute_sql(conn, f"DENY CREATE TABLE TO [{READONLY_USER}]", "CREATE TABLE denied")
        
        conn.close()
        
        print()
        print("=" * 50)
        print("✓ Setup completed successfully!")
        print("=" * 50)
        print()
        print(f"Read-Only User Created:")
        print(f"  Username: {READONLY_USER}")
        print(f"  Password: {READONLY_PASSWORD}")
        print()
        print("Your .env file is already configured with these credentials.")
        print("Restart the backend to use the new readonly connection:")
        print("  docker-compose restart backend")
        print()
        
    except Exception as e:
        print()
        print("=" * 50)
        print("✗ Setup failed!")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print()
        print("Please check:")
        print("  1. SQL Server is running")
        print("  2. Admin credentials are correct (sa / YourStrong@Passw0rd)")
        print("  3. SQL Server allows SQL authentication")
        print("  4. You have permission to create logins and users")
        sys.exit(1)

if __name__ == "__main__":
    main()

