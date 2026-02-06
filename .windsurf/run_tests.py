#!/usr/bin/env python3
"""
Windsurf hook script to run pytest after code changes.
This script runs tests and provides clear output about any failures.
"""
import json
import subprocess
import sys
from pathlib import Path

def main():
    # Read the hook context from stdin
    try:
        context = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("Error: Could not parse hook context JSON")
        sys.exit(1)
    
    # Get the file that was changed
    file_path = context.get("tool_info", {}).get("file_path", "")
    
    # Only run tests for Python files
    if not file_path.endswith(".py"):
        print(f"Skipping tests for non-Python file: {file_path}")
        sys.exit(0)
    
    print(f"\n🧪 Running tests after changes to: {Path(file_path).name}")
    print("=" * 60)
    
    # Run pytest with clear output
    try:
        # Run pytest with verbose output and short traceback
        result = subprocess.run(
            ["uv", "run", "pytest", "-v", "--tb=short", "--color=yes"],
            capture_output=False,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            print("\nPlease fix the failing tests above.")
            print("The test output shows which specific tests are failing and why.")
        
        # Exit with the same code as pytest so Windsurf knows if tests passed
        sys.exit(result.returncode)
        
    except subprocess.CalledProcessError as e:
        print(f"\n💥 Error running pytest: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n💥 Error: 'uv' command not found. Make sure uv is installed and in PATH.")
        sys.exit(1)

if __name__ == "__main__":
    main()
