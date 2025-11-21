#!/usr/bin/env python3
"""Show schema with descriptions"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.schema_service import get_table_schema
from services.sql_service import schema_to_json
import json

schema_info = get_table_schema()
schema_text = schema_to_json(schema_info)

char_count = len(schema_text)
token_estimate = char_count // 4

print("=" * 80)
print("SCHEMA STATISTICS")
print("=" * 80)
print(f"Tables: {len(schema_info)}")
total_columns = sum(len(cols) for cols in schema_info.values())
print(f"Total Columns: {total_columns}")
print(f"Schema JSON Size: {char_count:,} characters")
print(f"Estimated Tokens: {token_estimate:,} tokens")
print("=" * 80)

if schema_info:
    first_table = list(schema_info.keys())[0]
    table_info = schema_info[first_table]
    
    # Handle both old format (list) and new format (dict with columns/sample_rows)
    if isinstance(table_info, dict) and 'columns' in table_info:
        columns = table_info['columns']
        sample_rows = table_info.get('sample_rows', [])
    else:
        columns = table_info if isinstance(table_info, list) else []
        sample_rows = []
    
    print(f"\nSample: First 5 columns from '{first_table}':")
    print("-" * 80)
    for col in columns[:5]:
        print(f"  {col['name']} ({col['type']})")
        print(f"    Description: {col.get('description', 'N/A')}")
        print()
    
    if sample_rows:
        print(f"\nSample rows from '{first_table}' (first 2 rows):")
        print("-" * 80)
        for i, row in enumerate(sample_rows[:2], 1):
            print(f"  Row {i}:")
            for key, value in list(row.items())[:5]:  # Show first 5 columns
                print(f"    {key}: {value}")
            print()

