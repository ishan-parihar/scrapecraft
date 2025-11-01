#!/usr/bin/env python3
"""
Demo script for OSINT-OS CLI capabilities
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result

def main():
    print("OSINT-OS CLI Demonstration")
    print("="*50)
    
    print("\n1. Showing CLI help...")
    run_command("python osint_cli.py --help")
    
    print("\n2. Showing research command options...")
    run_command("python osint_cli.py research --help")
    
    print("\n3. Listing existing projects...")
    run_command("python osint_cli.py projects")
    
    print("\n4. Creating a new project with custom name...")
    run_command("python osint_cli.py setup --name demo_project_test --intensity comprehensive --output both")
    
    print("\n5. Checking the status of the new project...")
    run_command("python osint_cli.py status demo_project_test")
    
    print("\n6. Showing configuration...")
    run_command("python osint_cli.py config --list")
    
    print("\n7. Demonstrating different naming patterns...")
    print("Running: python -c \"from osint_cli import generate_ai_project_name; [print(generate_ai_project_name()) for _ in range(5)]\"")
    result = subprocess.run([
        sys.executable, "-c", 
        "from osint_cli import generate_ai_project_name; [print(generate_ai_project_name()) for _ in range(5)]"
    ], capture_output=True, text=True)
    print("Output:", result.stdout)
    
    print("\n8. Checking project structure...")
    if Path("demo_project_test").exists():
        run_command("ls -la demo_project_test/")
    
    print("\nDemo completed successfully!")
    print("\nKey features demonstrated:")
    print("- Intelligence-grade project naming")
    print("- Professional project structure")
    print("- Research intensity levels")
    print("- Output format options")
    print("- Project management commands")
    print("- Configuration management")
    print("- Status tracking")
    
    # Clean up demo project if it exists
    if Path("demo_project_test").exists():
        import shutil
        shutil.rmtree("demo_project_test")
        print("\nDemo project cleaned up.")

if __name__ == "__main__":
    main()
