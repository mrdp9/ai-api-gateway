#!/usr/bin/env python3
"""
Frontend Testing Quick Start
Run this script to test the frontend locally before deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check required dependencies"""
    print_header("Checking Dependencies")
    
    required = ['fastapi', 'uvicorn']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Install with: pip install {package}")
            missing.append(package)
    
    return len(missing) == 0

def check_files():
    """Check that all frontend files exist"""
    print_header("Checking Frontend Files")
    
    base_path = Path(__file__).parent
    files = {
        "HTML Template": base_path / "api" / "templates" / "index.html",
        "CSS Stylesheet": base_path / "api" / "static" / "style.css",
        "JavaScript Module": base_path / "api" / "static" / "dashboard.js",
        "FastAPI App": base_path / "api" / "main.py",
        "Tests": base_path / "tests" / "test_frontend.py",
    }
    
    all_exist = True
    for name, path in files.items():
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {name:20} - {size:6} bytes - {path.relative_to(base_path)}")
        else:
            print(f"❌ {name:20} - MISSING - {path}")
            all_exist = False
    
    return all_exist

def run_unit_tests():
    """Run unit tests"""
    print_header("Running Unit Tests")
    
    base_path = Path(__file__).parent
    test_file = base_path / "tests" / "test_frontend.py"
    
    if not test_file.exists():
        print("❌ Test file not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            cwd=str(base_path)
        )
        
        # Print last 30 lines of output
        lines = result.stdout.split('\n')
        for line in lines[-30:]:
            if line.strip():
                if 'OK' in line or 'PASSED' in line or 'Successes' in line:
                    print(f"✅ {line}")
                elif 'FAILED' in line or 'ERROR' in line or 'Error' in line:
                    print(f"❌ {line}")
                else:
                    print(f"   {line}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def check_static_mount():
    """Check FastAPI static mount configuration"""
    print_header("Checking FastAPI Configuration")
    
    base_path = Path(__file__).parent
    main_py = base_path / "api" / "main.py"
    
    if not main_py.exists():
        print("❌ main.py not found")
        return False
    
    content = main_py.read_text(encoding='utf-8')
    
    checks = {
        "StaticFiles import": "from fastapi.staticfiles import StaticFiles" in content,
        "Static mount": 'app.mount("/static"' in content,
        "Static directory": 'StaticFiles(directory="static")' in content,
        "Updated API endpoints": '@app.post("/api/create")' in content,
        "DELETE endpoint": '@app.delete("/api/delete/' in content,
    }
    
    all_good = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_good = all_good and result
    
    return all_good

def print_testing_guide():
    """Print manual testing guide"""
    print_header("Manual Testing Guide")
    
    guide = """
1. START FASTAPI SERVER
   cd api
   python -m uvicorn main:app --reload --port 8000

2. OPEN IN BROWSER
   http://localhost:8000

3. LOGIN
   Username: admin
   Password: adminpass

4. TEST FUNCTIONALITY
   - Create a new API key (set expiration date)
   - Copy the API key
   - Verify tunnel URL displays (if configured)
   - Try revoking a key
   - Check responsive design (F12 → toggle device toolbar)

5. CHECK BROWSER CONSOLE (F12)
   - No JavaScript errors
   - Check Network tab:
     * style.css loads (200 status)
     * dashboard.js loads (200 status)
     * /api/tunnel-url GET succeeds
     * /api/create POST succeeds
     * /api/delete/* DELETE succeeds

6. VERIFY CSS LOADING
   - Inspect element (F12)
   - Check that styles are applied
   - Verify CSS variables used (--primary-color, etc.)

7. TEST RESPONSIVE DESIGN
   - F12 → Device toolbar toggle
   - Test at 480px (mobile)
   - Test at 768px (tablet)
   - Test at 1024px+ (desktop)
"""
    
    print(guide)

def print_summary(results):
    """Print summary of checks"""
    print_header("Summary")
    
    all_passed = all(results.values())
    
    print("Checks Performed:")
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status:8} - {check_name}")
    
    print()
    if all_passed:
        print("🎉 All checks passed! Frontend is ready for testing.")
        print("\nNext: Run manual tests using the guide above.")
    else:
        print("⚠️  Some checks failed. Please fix the issues before testing.")
    
    return all_passed

def main():
    """Main testing orchestration"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "FRONTEND TESTING QUICK START" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    
    results = {}
    
    # Run checks
    results["Python Version"] = check_python()
    results["Dependencies"] = check_dependencies()
    results["Frontend Files"] = check_files()
    results["Unit Tests"] = run_unit_tests()
    results["FastAPI Config"] = check_static_mount()
    
    # Print guides
    print_testing_guide()
    
    # Summary
    all_passed = print_summary(results)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
