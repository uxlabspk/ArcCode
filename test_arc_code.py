#!/usr/bin/env python3
"""
Simple tests for Arc Code CLI
"""

import subprocess
import sys
import os

def test_echo_command():
    """Test echo command"""
    result = subprocess.run(
        ["arc-code", "echo Hello Test"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Echo: Hello Test" in result.stdout
    print("✓ Echo command test passed")

def test_list_files_command():
    """Test list_files command"""
    result = subprocess.run(
        ["arc-code", "list_files ."],
        capture_output=True,
        text=True,
        cwd="/run/media/muhammad/Store/Repository/ArcCode"
    )
    assert result.returncode == 0
    assert "Files in .:" in result.stdout
    print("✓ List files command test passed")

def test_help():
    """Test help output"""
    result = subprocess.run(
        ["arc-code", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Arc Code CLI" in result.stdout
    print("✓ Help test passed")

def test_unknown_command():
    """Test unknown command handling"""
    result = subprocess.run(
        ["arc-code", "unknown_command"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Unknown command" in result.stdout
    print("✓ Unknown command test passed")

if __name__ == "__main__":
    print("Running Arc Code CLI tests...")
    
    try:
        test_echo_command()
        test_list_files_command()
        test_help()
        test_unknown_command()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)