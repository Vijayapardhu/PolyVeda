#!/usr/bin/env python3
"""
Verification script for PolyVeda Django setup.
"""
import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (NOT FOUND)")
        return False

def main():
    print("🔍 PolyVeda Setup Verification")
    print("=" * 40)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check essential files
    files_to_check = [
        ('manage.py', 'Django management script'),
        ('requirements.txt', 'Python dependencies'),
        ('polyveda/settings/base.py', 'Django base settings'),
        ('polyveda/settings/production.py', 'Django production settings'),
        ('polyveda/urls.py', 'Main URL configuration'),
        ('accounts/models.py', 'Accounts models'),
        ('academics/models.py', 'Academics models'),
    ]
    
    all_files_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_files_exist = False
    
    # Check Python environment
    print(f"\n🐍 Python Environment:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python path: {sys.path[:3]}...")
    
    # Check if we can import Django
    try:
        import django
        print(f"✅ Django is available: {django.get_version()}")
    except ImportError:
        print("❌ Django is NOT available (not installed)")
        all_files_exist = False
    
    # Summary
    print(f"\n📋 Summary:")
    if all_files_exist:
        print("✅ All essential files are present")
        print("✅ Setup looks good for deployment")
    else:
        print("❌ Some files are missing")
        print("❌ Setup needs attention")
    
    return all_files_exist

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)