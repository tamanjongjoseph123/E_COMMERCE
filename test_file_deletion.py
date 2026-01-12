"""
Test script to verify file deletion from FTP server
Run this with: python test_file_deletion.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce.settings')
django.setup()

from django.core.files.base import ContentFile
from e_commerce.storage_backend import FTPStorage
from api.models import Product, User, Seller
from django.contrib.auth import get_user_model

def test_file_deletion():
    print("=" * 60)
    print("Testing File Deletion from FTP Server")
    print("=" * 60)
    
    storage = FTPStorage()
    
    # Test 1: Upload and delete a test file directly
    print("\nTest 1: Direct file deletion via storage backend")
    print("-" * 60)
    try:
        test_content = ContentFile(b"Test file for deletion")
        test_filename = "test_deletion_file.txt"
        
        # Upload file
        saved_name = storage._save(test_filename, test_content)
        print(f"[OK] File uploaded: {saved_name}")
        
        # Check if file exists
        if storage.exists(test_filename):
            print(f"[OK] File exists on FTP server")
        else:
            print(f"[WARNING] File existence check failed")
        
        # Delete file
        storage.delete(test_filename)
        print(f"[OK] Delete command executed")
        
        # Verify deletion
        if not storage.exists(test_filename):
            print(f"[OK] File successfully deleted from FTP server")
        else:
            print(f"[WARNING] File still exists after deletion")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Create and delete a Product (with image)
    print("\nTest 2: Product deletion with image")
    print("-" * 60)
    try:
        # Create a test user (seller)
        User = get_user_model()
        test_seller = User.objects.filter(role='seller', email='test_seller@test.com').first()
        if not test_seller:
            print("[INFO] Creating test seller user...")
            test_seller = User.objects.create_user(
                username='test_seller@test.com',
                email='test_seller@test.com',
                name='Test Seller',
                role='seller',
                password='testpass123'
            )
        
        # Create a test product with image
        print("[INFO] Creating test product...")
        test_image_content = ContentFile(b"fake image content")
        test_image_content.name = "test_product_image.jpg"
        
        product = Product.objects.create(
            seller=test_seller,
            category_id=1,  # Assuming category with id=1 exists
            name="Test Product for Deletion",
            description="This product will be deleted",
            price=99.99,
            stock=10
        )
        product.image.save("test_product_image.jpg", test_image_content, save=True)
        product_image_path = product.image.name
        print(f"[OK] Product created with image: {product_image_path}")
        
        # Verify image exists
        if storage.exists(product_image_path):
            print(f"[OK] Product image exists on FTP server")
        else:
            print(f"[WARNING] Product image not found on FTP server")
        
        # Delete the product (this should trigger signal to delete image)
        print("[INFO] Deleting product...")
        product.delete()
        print(f"[OK] Product deleted from database")
        
        # Verify image is deleted
        if not storage.exists(product_image_path):
            print(f"[OK] Product image successfully deleted from FTP server")
        else:
            print(f"[WARNING] Product image still exists on FTP server after deletion")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("File Deletion Test Completed")
    print("=" * 60)

if __name__ == "__main__":
    test_file_deletion()

