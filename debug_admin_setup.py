#!/usr/bin/env python3
"""
Debug script to check admin account setup and first-time detection.

Usage:
    python debug_admin_setup.py

Author: ConsultEase Development Team
"""

import sys
import os

# Add the central_system directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'central_system'))

def check_database_state():
    """Check the current state of the database and admin accounts."""
    print("🔍 Checking database state...")
    
    try:
        from models.base import get_db
        from models.admin import Admin
        
        db = get_db()
        
        # Check all admin accounts
        all_admins = db.query(Admin).all()
        print(f"📊 Total admin accounts in database: {len(all_admins)}")
        
        if all_admins:
            print("👥 Admin accounts found:")
            for admin in all_admins:
                print(f"   - ID: {admin.id}")
                print(f"     Username: {admin.username}")
                print(f"     Active: {admin.is_active}")
                print(f"     Force Password Change: {admin.force_password_change}")
                print(f"     Created: {admin.created_at}")
                print()
        else:
            print("❌ No admin accounts found in database")
        
        db.close()
        return len(all_admins)
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return -1

def test_admin_controller():
    """Test the admin controller's first-time setup detection."""
    print("\n🧪 Testing AdminController first-time setup detection...")
    
    try:
        from controllers.admin_controller import AdminController
        
        controller = AdminController()
        
        # Test the methods
        accounts_exist = controller.check_admin_accounts_exist()
        print(f"📋 check_admin_accounts_exist(): {accounts_exist}")
        
        valid_accounts_exist = controller.check_valid_admin_accounts_exist()
        print(f"📋 check_valid_admin_accounts_exist(): {valid_accounts_exist}")
        
        is_first_time = controller.is_first_time_setup()
        print(f"📋 is_first_time_setup(): {is_first_time}")
        
        return is_first_time
        
    except Exception as e:
        print(f"❌ Error testing admin controller: {e}")
        return False

def simulate_admin_login_check():
    """Simulate what happens when admin login window checks for first-time setup."""
    print("\n🎭 Simulating admin login window first-time setup check...")
    
    try:
        from controllers.admin_controller import AdminController
        
        # Create admin controller like the main app does
        admin_controller = AdminController()
        
        # Simulate the check that happens in admin login window
        if admin_controller and admin_controller.is_first_time_setup():
            print("✅ First-time setup would be triggered!")
            print("   Dialog should appear for account creation")
            return True
        else:
            print("❌ First-time setup would NOT be triggered")
            print("   Dialog will not appear")
            return False
            
    except Exception as e:
        print(f"❌ Error simulating admin login check: {e}")
        return False

def clear_admin_accounts():
    """Clear all admin accounts to test first-time setup."""
    print("\n🗑️  Clearing admin accounts for testing...")
    
    try:
        from models.base import get_db
        from models.admin import Admin
        
        db = get_db()
        
        # Count before deletion
        before_count = db.query(Admin).count()
        print(f"📊 Admin accounts before deletion: {before_count}")
        
        # Delete all admin accounts
        db.query(Admin).delete()
        db.commit()
        
        # Count after deletion
        after_count = db.query(Admin).count()
        print(f"📊 Admin accounts after deletion: {after_count}")
        
        db.close()
        
        if after_count == 0:
            print("✅ All admin accounts cleared successfully")
            return True
        else:
            print("❌ Failed to clear all admin accounts")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing admin accounts: {e}")
        return False

def test_database_initialization():
    """Test what happens during database initialization."""
    print("\n🔄 Testing database initialization...")
    
    try:
        from models.base import init_db
        
        print("📋 Running init_db()...")
        init_db()
        print("✅ Database initialization completed")
        
        # Check what was created
        return check_database_state()
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        return -1

def main():
    """Main diagnostic function."""
    print("🚀 Admin Account Setup Diagnostic Tool")
    print("=" * 60)
    
    # Step 1: Check current database state
    admin_count = check_database_state()
    
    # Step 2: Test admin controller
    is_first_time = test_admin_controller()
    
    # Step 3: Simulate admin login check
    would_trigger = simulate_admin_login_check()
    
    # Analysis
    print("\n📊 ANALYSIS")
    print("=" * 30)
    
    if admin_count == 0:
        print("✅ No admin accounts exist - first-time setup should work")
    elif admin_count > 0:
        print(f"⚠️  {admin_count} admin account(s) exist - this prevents first-time setup")
        print("   The database initialization likely created default admin accounts")
    
    if is_first_time:
        print("✅ AdminController correctly detects first-time setup")
    else:
        print("❌ AdminController does NOT detect first-time setup")
    
    if would_trigger:
        print("✅ Admin login window would show account creation dialog")
    else:
        print("❌ Admin login window would NOT show account creation dialog")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 30)
    
    if admin_count > 0 and not would_trigger:
        print("🔧 ISSUE: Database initialization is creating admin accounts")
        print("   This prevents the first-time setup dialog from appearing")
        print()
        print("🛠️  SOLUTIONS:")
        print("   1. Disable automatic admin creation in database initialization")
        print("   2. Clear existing admin accounts to test first-time setup")
        print("   3. Modify first-time setup detection logic")
        print()
        
        # Offer to clear accounts for testing
        response = input("❓ Would you like to clear admin accounts to test first-time setup? (y/N): ")
        if response.lower() == 'y':
            if clear_admin_accounts():
                print("\n🔄 Testing after clearing accounts...")
                would_trigger_after = simulate_admin_login_check()
                if would_trigger_after:
                    print("✅ First-time setup would now work!")
                else:
                    print("❌ First-time setup still not working")
    
    elif admin_count == 0 and would_trigger:
        print("✅ Everything looks good - first-time setup should work")
        print("   Try running the application and clicking 'Admin Login'")
    
    print("\n🎯 NEXT STEPS")
    print("=" * 20)
    print("1. Run the main application: python central_system/main.py")
    print("2. Click 'Admin Login' button")
    print("3. Check if the account creation dialog appears")
    print("4. If not, the database initialization is likely creating admin accounts")

if __name__ == "__main__":
    main()
