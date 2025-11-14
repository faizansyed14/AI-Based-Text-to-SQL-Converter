#!/usr/bin/env python3
"""
SQL Server Backup File Reader
Reads and extracts information from SQL Server .bak files
"""

import struct
import sys
from datetime import datetime, timedelta
from pathlib import Path

class SQLServerBackupReader:
    """Parser for SQL Server backup files"""
    
    # SQL Server backup file signatures
    BACKUP_SIGNATURE = b'TAPE'
    MTF_SIGNATURE = b'TAPE'
    
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.file_size = self.filepath.stat().st_size
        self.metadata = {}
        
    def read_header(self):
        """Read the backup file header"""
        with open(self.filepath, 'rb') as f:
            # Read first block (usually 512 bytes or more)
            header = f.read(512)
            
            if len(header) < 512:
                return None, "File too small to be a valid backup"
            
            # Check for SQL Server backup signature
            if header[0:4] == self.BACKUP_SIGNATURE:
                return self.parse_sql_backup_header(f, header)
            else:
                # Try to detect if it's still a SQL backup with different format
                return self.analyze_unknown_format(f, header)
    
    def parse_sql_backup_header(self, file_handle, initial_header):
        """Parse SQL Server native backup header"""
        info = {
            'format': 'SQL Server Native Backup',
            'signature': initial_header[0:4].decode('ascii', errors='ignore')
        }
        
        # SQL Server backups use a media family header
        # The structure varies by version, but we can extract some common fields
        
        try:
            # Seek to different known offsets for metadata
            file_handle.seek(0)
            data = file_handle.read(8192)  # Read larger chunk
            
            # Look for database name (usually in Unicode)
            db_name = self.extract_unicode_string(data, 100, 512)
            if db_name:
                info['database_name'] = db_name
            
            # Look for server name
            server_name = self.extract_unicode_string(data, 512, 1024)
            if server_name:
                info['server_name'] = server_name
            
            # Try to find backup date
            # SQL Server stores dates as days since 1/1/1900
            backup_date = self.find_backup_date(data)
            if backup_date:
                info['backup_date'] = backup_date
            
            # Look for version info
            info['sql_version'] = self.detect_sql_version(data)
            
        except Exception as e:
            info['parsing_notes'] = f'Partial parsing: {str(e)}'
        
        return info, None
    
    def analyze_unknown_format(self, file_handle, initial_header):
        """Analyze file with unknown format"""
        info = {
            'format': 'Unknown - Analysis Results',
            'file_size_mb': round(self.file_size / (1024*1024), 2)
        }
        
        # Read more data for analysis
        file_handle.seek(0)
        sample = file_handle.read(16384)
        
        # Look for common strings
        strings_found = self.extract_strings(sample)
        if strings_found:
            info['detected_strings'] = strings_found[:10]  # First 10 strings
        
        # Check for database-related keywords
        keywords = [b'DATABASE', b'BACKUP', b'RESTORE', b'TABLE', b'master', b'msdb']
        found_keywords = []
        for keyword in keywords:
            if keyword in sample:
                found_keywords.append(keyword.decode('ascii'))
        
        if found_keywords:
            info['found_keywords'] = found_keywords
        
        # Check entropy (compressed/encrypted files have high entropy)
        entropy = self.calculate_entropy(sample)
        info['entropy'] = round(entropy, 2)
        if entropy > 7.5:
            info['note'] = 'High entropy - file may be compressed or encrypted'
        
        return info, None
    
    def extract_unicode_string(self, data, start, end):
        """Extract Unicode string from binary data"""
        try:
            # Look for Unicode strings (UTF-16LE)
            for i in range(start, min(end, len(data) - 2), 2):
                # Find null-terminated Unicode string
                if data[i] != 0 and data[i+1] == 0:
                    string_bytes = bytearray()
                    j = i
                    while j < len(data) - 1 and not (data[j] == 0 and data[j+1] == 0):
                        if data[j+1] == 0 and 32 <= data[j] <= 126:
                            string_bytes.append(data[j])
                        j += 2
                    
                    if len(string_bytes) > 3:
                        result = string_bytes.decode('ascii', errors='ignore').strip()
                        if result and len(result) > 3:
                            return result
        except:
            pass
        return None
    
    def extract_strings(self, data, min_length=4):
        """Extract ASCII strings from binary data"""
        strings = []
        current_string = bytearray()
        
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                current_string.append(byte)
            else:
                if len(current_string) >= min_length:
                    strings.append(current_string.decode('ascii'))
                current_string = bytearray()
        
        # Don't forget the last string
        if len(current_string) >= min_length:
            strings.append(current_string.decode('ascii'))
        
        return strings
    
    def find_backup_date(self, data):
        """Try to find backup date in the data"""
        # SQL Server dates are stored as days since 1/1/1900
        # Look for reasonable date values
        try:
            for i in range(0, len(data) - 4, 4):
                days = struct.unpack('<I', data[i:i+4])[0]
                # Check if it's a reasonable date (between 1990 and 2030)
                if 32874 < days < 47482:  # Approximate range
                    base_date = datetime(1900, 1, 1)
                    calculated_date = base_date + timedelta(days=days)
                    if 1990 <= calculated_date.year <= 2030:
                        return calculated_date.strftime('%Y-%m-%d')
        except:
            pass
        return None
    
    def detect_sql_version(self, data):
        """Try to detect SQL Server version"""
        version_strings = {
            b'SQL Server 2019': '2019 (15.x)',
            b'SQL Server 2017': '2017 (14.x)',
            b'SQL Server 2016': '2016 (13.x)',
            b'SQL Server 2014': '2014 (12.x)',
            b'SQL Server 2012': '2012 (11.x)',
            b'SQL Server 2008': '2008/2008R2 (10.x)',
        }
        
        for version_bytes, version_name in version_strings.items():
            if version_bytes in data:
                return version_name
        
        return 'Unknown'
    
    def calculate_entropy(self, data):
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        # Count byte frequencies
        frequencies = {}
        for byte in data:
            frequencies[byte] = frequencies.get(byte, 0) + 1
        
        # Calculate entropy
        entropy = 0
        data_len = len(data)
        for count in frequencies.values():
            probability = count / data_len
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def extract_backup_info(self):
        """Main method to extract all available information"""
        print(f"\n{'='*60}")
        print(f"SQL Server Backup File Analysis")
        print(f"{'='*60}\n")
        print(f"File: {self.filepath.name}")
        print(f"Size: {self.file_size:,} bytes ({round(self.file_size / (1024*1024), 2)} MB)\n")
        
        info, error = self.read_header()
        
        if error:
            print(f"Error: {error}")
            return False
        
        if info:
            print("Backup Information:")
            print("-" * 60)
            for key, value in info.items():
                if isinstance(value, list):
                    print(f"{key.replace('_', ' ').title()}:")
                    for item in value:
                        print(f"  - {item}")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
            print()
        
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python sql_backup_reader.py <backup_file.bak>")
        print("\nThis tool analyzes SQL Server backup files and extracts metadata.")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    if not Path(backup_file).exists():
        print(f"Error: File '{backup_file}' not found")
        sys.exit(1)
    
    reader = SQLServerBackupReader(backup_file)
    success = reader.extract_backup_info()
    
    if success:
        print("\n" + "="*60)
        print("Note: To fully restore this backup, you need:")
        print("  1. SQL Server instance (matching or newer version)")
        print("  2. Use SQL Server Management Studio (SSMS), or")
        print("  3. Use sqlcmd with RESTORE DATABASE command, or")
        print("  4. Use Python libraries like pymssql/pyodbc with restore")
        print("="*60)


if __name__ == "__main__":
    main()
