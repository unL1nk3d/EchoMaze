#!/usr/bin/env python
"""
Example script demonstrating log import functionality.

Run: python logimporter_example.py
"""

import json
import tempfile
import os
from logimporter import LogImporter, LogImportManager


def example_plaintext():
    """Example 1: Import plain text log."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Plain Text Log Import")
    print("="*60)
    
    content = """
2024-01-15 10:30:45 | whoami
2024-01-15 10:31:00 | ls -la /home
2024-01-15 10:31:15 | id
2024-01-15 10:32:00 | cat /etc/passwd
    """.strip()
    
    events, report = LogImporter.import_from_content(content)
    print(report)
    
    print("\nParsed Events:")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.command} (timestamp: {event.timestamp})")


def example_json():
    """Example 2: Import JSON log."""
    print("\n" + "="*60)
    print("EXAMPLE 2: JSON Log Import")
    print("="*60)
    
    content = json.dumps([
        {
            "command": "whoami",
            "timestamp": "2024-01-15T10:30:45Z",
            "operator": "admin",
            "user": "root",
            "shell": "/bin/bash"
        },
        {
            "command": "ls -la /etc",
            "timestamp": "2024-01-15T10:31:00Z",
            "operator": "admin",
            "user": "root"
        },
        {
            "command": "grep -r 'password' /etc",
            "timestamp": "2024-01-15T10:32:00Z",
            "operator": "admin",
            "user": "root"
        }
    ], indent=2)
    
    events, report = LogImporter.import_from_content(content, format_hint="JSON")
    print(report)
    
    print("\nParsed Events:")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.command}")
        print(f"     Operator: {event.operator}, User: {event.user}, Shell: {event.shell}")


def example_csv():
    """Example 3: Import CSV log."""
    print("\n" + "="*60)
    print("EXAMPLE 3: CSV Log Import")
    print("="*60)
    
    content = """command,timestamp,operator,user,hostname
whoami,2024-01-15 10:30:45,admin,root,target-01
ls -la /etc,2024-01-15 10:31:00,admin,root,target-01
find / -type f -name "*.conf",2024-01-15 10:32:00,admin,root,target-01
cat /etc/shadow,2024-01-15 10:33:00,admin,root,target-01"""
    
    events, report = LogImporter.import_from_content(content, format_hint="CSV")
    print(report)
    
    print("\nParsed Events:")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.command} (host: {event.hostname})")


def example_bash_history():
    """Example 4: Import Bash History."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Bash History Import")
    print("="*60)
    
    content = """#1705316445
whoami
#1705316460
ls -la /etc
#1705316475
cat /etc/passwd
id
hostname"""
    
    events, report = LogImporter.import_from_content(content, format_hint="BashHistory")
    print(report)
    
    print("\nParsed Events:")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.command}")


def example_zsh_history():
    """Example 5: Import Zsh History."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Zsh History Import")
    print("="*60)
    
    content = """: 1705316445:0;whoami
: 1705316460:0;ls -la /etc
: 1705316475:0;cat /etc/passwd
: 1705316490:0;grep -i root /etc/shadow
: 1705316505:0;find / -type f -name "*.key" 2>/dev/null"""
    
    events, report = LogImporter.import_from_content(content, format_hint="ZshHistory")
    print(report)
    
    print("\nParsed Events:")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event.command}")


def example_auto_detect():
    """Example 6: Auto-detect format."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Auto-Detect Format")
    print("="*60)
    
    # JSON content
    json_content = json.dumps([
        {"command": "whoami", "operator": "admin"},
        {"command": "id", "operator": "admin"}
    ])
    
    print("\nDetecting JSON content...")
    events, report = LogImporter.import_from_content(json_content)
    print(f"Detected format: {report.format_detected}")
    print(f"Imported: {report.imported_commands} commands")
    
    # Plain text content
    plaintext_content = "whoami\nls -la\nid"
    
    print("\nDetecting PlainText content...")
    events, report = LogImporter.import_from_content(plaintext_content)
    print(f"Detected format: {report.format_detected}")
    print(f"Imported: {report.imported_commands} commands")


def example_file_import():
    """Example 7: Import from file."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Import from File")
    print("="*60)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("""whoami
ls -la /home
cat /etc/hosts
ping -c 4 8.8.8.8
traceroute example.com""")
        fname = f.name
    
    try:
        print(f"\nImporting from: {fname}")
        events, report = LogImporter.import_from_file(fname)
        print(report)
        
        print(f"\nSuccessfully imported {len(events)} events")
    finally:
        os.unlink(fname)


def example_error_handling():
    """Example 8: Error handling."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Error Handling")
    print("="*60)
    
    # JSON with errors
    content = json.dumps([
        {"command": "whoami", "operator": "admin"},  # OK
        {"operator": "admin"},  # Missing command
        {"command": "ls -la"},  # OK
        {},  # Empty
        {"command": "id"}  # OK
    ])
    
    events, report = LogImporter.import_from_content(content)
    print(report)
    
    print("\nProcessed successfully despite errors:")
    print(f"  Events parsed: {report.imported_commands}")
    print(f"  Errors encountered: {len(report.errors)}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("EchoMaze Log Importer Examples")
    print("="*60)
    
    example_plaintext()
    example_json()
    example_csv()
    example_bash_history()
    example_zsh_history()
    example_auto_detect()
    example_file_import()
    example_error_handling()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Try: python launch.py --import-log <your-file.log>")
    print("  2. View the logimporter/README.md for full documentation")
    print("  3. Run tests: python -m unittest test.test_logimporter -v")
    print()
