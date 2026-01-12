"""
Test script to verify FTP storage connection
Run this with: python test_ftp_connection.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce.settings')
django.setup()

from django.conf import settings
from e_commerce.storage_backend import FTPStorage
from django.core.files.base import ContentFile

def test_ftp_connection():
    print("=" * 60)
    print("Testing FTP Storage Connection")
    print("=" * 60)
    
    # Display FTP configuration
    print("\nFTP Configuration:")
    print(f"  Host: {settings.FTP_STORAGE_OPTIONS['host']}")
    print(f"  Port: {settings.FTP_STORAGE_OPTIONS['port']}")
    print(f"  Username: {settings.FTP_STORAGE_OPTIONS['username']}")
    print(f"  Base Path: {settings.FTP_STORAGE_OPTIONS['base_path']}")
    print(f"  Passive Mode: {settings.FTP_STORAGE_OPTIONS['passive']}")
    print(f"  Media URL: {settings.MEDIA_URL}")
    
    # Test connection
    print("\n" + "-" * 60)
    print("Step 1: Testing FTP Connection...")
    print("-" * 60)
    
    try:
        storage = FTPStorage()
        ftp = storage._connect()
        print("[OK] Successfully connected to FTP server!")
        
        # Test listing current directory
        print("\nStep 2: Testing directory listing...")
        try:
            files = ftp.nlst()
            print(f"[OK] Current directory contents: {len(files)} items")
            if files:
                print(f"  Sample files/directories: {files[:5]}")
        except Exception as e:
            print(f"[WARNING] Could not list directory: {e}")
        
        # Test creating a test directory
        print("\nStep 3: Testing directory creation...")
        try:
            test_dir = "test_dir"
            try:
                ftp.mkd(test_dir)
                print(f"[OK] Successfully created test directory: {test_dir}")
                # Clean up - remove test directory
                try:
                    ftp.rmd(test_dir)
                    print(f"[OK] Successfully removed test directory: {test_dir}")
                except:
                    print(f"[WARNING] Could not remove test directory (may not exist)")
            except Exception as e:
                if "550" in str(e) or "exists" in str(e).lower():
                    print(f"[WARNING] Directory already exists or permission issue: {e}")
                else:
                    raise
        except Exception as e:
            print(f"[ERROR] Failed to create directory: {e}")
        
        # Test file upload
        print("\nStep 4: Testing file upload...")
        try:
            test_content = ContentFile(b"This is a test file for FTP connection verification.")
            test_filename = "test_ftp_connection.txt"
            saved_name = storage._save(test_filename, test_content)
            print(f"[OK] Successfully uploaded test file: {saved_name}")
            
            # Test file existence
            print("\nStep 5: Testing file existence check...")
            if storage.exists(test_filename):
                print(f"[OK] File exists on FTP server: {test_filename}")
            else:
                print(f"[WARNING] File existence check returned False")
            
            # Test file deletion
            print("\nStep 6: Testing file deletion...")
            try:
                storage.delete(test_filename)
                print(f"[OK] Successfully deleted test file: {test_filename}")
            except Exception as e:
                print(f"[WARNING] Could not delete test file: {e}")
            
        except Exception as e:
            print(f"[ERROR] Failed to upload file: {e}")
            import traceback
            traceback.print_exc()
        
        # Close connection
        ftp.quit()
        print("\n" + "=" * 60)
        print("[OK] FTP Connection Test Completed Successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to FTP server!")
        print(f"  Error: {e}")
        print("\n" + "=" * 60)
        print("[ERROR] FTP Connection Test Failed!")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ftp_connection()
    exit(0 if success else 1)

