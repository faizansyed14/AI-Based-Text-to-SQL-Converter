#!/usr/bin/env python3
"""
Quick script to restore VikasAI.Bak file to SQL Server
This is a simplified version that automates the restore process
"""

import subprocess
import sys
from pathlib import Path

def main():
    backup_file = "VikasAI.Bak"
    
    if not Path(backup_file).exists():
        print(f"Error: {backup_file} not found in current directory")
        print(f"Current directory: {Path.cwd()}")
        sys.exit(1)
    
    print("="*60)
    print("SQL Server Backup Restore Tool")
    print("="*60)
    print(f"\nBackup file: {backup_file}")
    print(f"File size: {Path(backup_file).stat().st_size / (1024*1024):.2f} MB\n")
    
    # Import the restore tool
    restore_tool_path = Path(__file__).parent / 'files' / 'sql_restore_tool.py'
    if not restore_tool_path.exists():
        print(f"Error: sql_restore_tool.py not found at {restore_tool_path}")
        sys.exit(1)
    
    # Run the restore tool
    print("Starting interactive restore tool...\n")
    subprocess.run([sys.executable, str(restore_tool_path), backup_file])

if __name__ == "__main__":
    main()

