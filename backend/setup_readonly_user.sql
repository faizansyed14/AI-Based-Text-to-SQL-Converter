-- ============================================
-- SQL Server Read-Only User Setup Script
-- ============================================
-- This script creates a read-only user for the VikasAI database
-- Run this script as a SQL Server administrator (sa or sysadmin)

USE [master]
GO

-- ============================================
-- Step 1: Create Login (Server-level)
-- ============================================
-- Create a login at the server level
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'vikasai_readonly')
BEGIN
    CREATE LOGIN [vikasai_readonly] 
    WITH PASSWORD = 'Zak@12345',  -- Based on AUTH_PASSWORD, extended to meet SQL Server policy (min 8 chars)
         DEFAULT_DATABASE = [VikasAI],
         CHECK_EXPIRATION = OFF,
         CHECK_POLICY = ON
    PRINT 'Login [vikasai_readonly] created successfully'
END
ELSE
BEGIN
    PRINT 'Login [vikasai_readonly] already exists'
END
GO

-- ============================================
-- Step 2: Create User in VikasAI Database
-- ============================================
USE [VikasAI]
GO

-- Create user mapped to the login
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'vikasai_readonly')
BEGIN
    CREATE USER [vikasai_readonly] FOR LOGIN [vikasai_readonly]
    PRINT 'User [vikasai_readonly] created in VikasAI database'
END
ELSE
BEGIN
    PRINT 'User [vikasai_readonly] already exists in VikasAI database'
END
GO

-- ============================================
-- Step 3: Grant Read-Only Permissions
-- ============================================
-- Grant SELECT permission on all existing tables
-- This grants SELECT on all current tables
EXEC sp_MSforeachtable @command1 = 'GRANT SELECT ON ? TO [vikasai_readonly]'
PRINT 'SELECT permission granted on all tables'

-- Grant SELECT permission on all views
EXEC sp_MSforeachdb @command1 = 'USE [?] EXEC sp_MSforeachview @command1 = "GRANT SELECT ON ? TO [vikasai_readonly]"'
PRINT 'SELECT permission granted on all views'

-- Grant SELECT permission on all future tables (via schema-level permission)
-- This ensures new tables automatically get SELECT permission
GRANT SELECT ON SCHEMA::[dbo] TO [vikasai_readonly]
PRINT 'SELECT permission granted on dbo schema (for future tables)'

-- Grant permission to view database metadata (needed for schema queries)
GRANT VIEW DEFINITION ON SCHEMA::[dbo] TO [vikasai_readonly]
GRANT VIEW ANY DEFINITION TO [vikasai_readonly]
PRINT 'Metadata viewing permissions granted'

-- ============================================
-- Step 4: Deny Write Operations (Extra Safety)
-- ============================================
-- Explicitly deny INSERT, UPDATE, DELETE, CREATE, ALTER, DROP
DENY INSERT ON SCHEMA::[dbo] TO [vikasai_readonly]
DENY UPDATE ON SCHEMA::[dbo] TO [vikasai_readonly]
DENY DELETE ON SCHEMA::[dbo] TO [vikasai_readonly]
DENY ALTER ON SCHEMA::[dbo] TO [vikasai_readonly]
DENY CREATE TABLE TO [vikasai_readonly]
DENY CREATE VIEW TO [vikasai_readonly]
DENY CREATE PROCEDURE TO [vikasai_readonly]
DENY CREATE FUNCTION TO [vikasai_readonly]
PRINT 'Write operations explicitly denied'

-- ============================================
-- Step 5: Verify Permissions
-- ============================================
-- Check user permissions
SELECT 
    dp.name AS UserName,
    dp.type_desc AS UserType,
    p.permission_name,
    p.state_desc AS PermissionState,
    o.name AS ObjectName,
    o.type_desc AS ObjectType
FROM sys.database_permissions p
INNER JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
LEFT JOIN sys.objects o ON p.major_id = o.object_id
WHERE dp.name = 'vikasai_readonly'
ORDER BY o.name, p.permission_name

PRINT ''
PRINT '============================================'
PRINT 'Setup Complete!'
PRINT '============================================'
PRINT 'Username: vikasai_readonly'
PRINT 'Password: Zak@12345'
PRINT ''
PRINT 'Update your .env file with:'
PRINT '  SQLSERVER_USER=vikasai_readonly'
PRINT '  SQLSERVER_PASSWORD=Zak@12345'
PRINT '============================================'
GO

