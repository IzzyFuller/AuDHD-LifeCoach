#!/usr/bin/env python3
"""
Script to run tests with coverage and generate a coverage badge.

This script:
1. Runs the full test suite with coverage
2. Generates an HTML coverage report
3. Creates a coverage badge SVG file
4. Displays coverage summary
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error {description}: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

def main():
    """Main function to run coverage analysis."""
    print("📊 Running AuDHD-LifeCoach Test Coverage Analysis")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    print(f"📁 Working directory: {project_root}")
      # Run tests with coverage
    run_command(
        "poetry run pytest tests/ --cov=src/audhd_lifecoach --cov-report=term --cov-report=html --cov-report=xml",
        "Running tests with coverage"
    )
    
    # Generate coverage badge
    run_command(
        "poetry run coverage-badge -f -o coverage.svg",
        "Generating coverage badge"
    )
    
    print("\n✅ Coverage analysis complete!")
    print("📄 Coverage report: htmlcov/index.html")
    print("🏷️  Coverage badge: coverage.svg")
    print("📊 XML report: coverage.xml")

if __name__ == "__main__":
    main()
