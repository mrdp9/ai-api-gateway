#!/usr/bin/env python3
"""
Quick test script to validate the AI API Gateway setup
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report status."""
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"   {result.stdout[:200]}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_file(filepath, description):
    """Check if a file exists."""
    print(f"\n📄 {description}...")
    if os.path.exists(filepath):
        print(f"✅ {description} - FOUND")
        return True
    else:
        print(f"❌ {description} - NOT FOUND")
        return False

def main():
    print("=" * 60)
    print("🔧 AI API Gateway - Setup Validation")
    print("=" * 60)
    
    checks = []
    
    # Check Python version
    print(f"\n📌 Python Version: {sys.version.split()[0]}")
    checks.append(sys.version_info >= (3, 8))
    
    # Check required files
    checks.append(check_file("api/main.py", "FastAPI app"))
    checks.append(check_file("api/requirements.txt", "Requirements file"))
    checks.append(check_file("docker-compose.yml", "Docker Compose config"))
    checks.append(check_file(".env.example", "Environment template"))
    checks.append(check_file("SETUP_GUIDE.md", "Setup guide"))
    checks.append(check_file("context.md", "Project context"))
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    checks.append(run_command("python -m pip show fastapi > /dev/null 2>&1", "FastAPI installed"))
    checks.append(run_command("python -m pip show docker > /dev/null 2>&1", "Docker SDK installed"))
    
    # Check Docker
    print("\n🐳 Checking Docker...")
    checks.append(run_command("docker --version", "Docker CLI"))
    checks.append(run_command("docker-compose --version", "Docker Compose"))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"✨ Validation Results: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ All checks passed! Ready to deploy.")
        print("\nNext steps:")
        print("1. Create .env file: cp .env.example .env")
        print("2. Configure CloudFlare tunnel token in .env")
        print("3. Configure Gmail credentials in .env")
        print("4. Run: docker-compose up --build")
        print("5. Check your email for tunnel URL")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please review the output above.")
        print("\nFor help, see SETUP_GUIDE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
