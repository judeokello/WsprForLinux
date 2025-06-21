#!/usr/bin/env python3
"""
Simple test script to verify all imports work correctly.
"""

def test_imports():
    """Test all the imports that were causing errors."""
    print("Testing imports...")
    
    try:
        # Test config imports
        from src.config.settings import Settings
        print("✅ Settings import successful")
        
        from src.config.logging_config import setup_logging
        print("✅ Logging config import successful")
        
        # Test utils imports
        from src.utils.error_handler import ErrorHandler
        print("✅ Error handler import successful")
        
        # Test main application class (without starting Qt)
        from src.main import W4LApplication
        print("✅ W4LApplication import successful")
        
        # Test creating instances
        settings = Settings()
        print("✅ Settings instance created")
        
        error_handler = ErrorHandler()
        print("✅ Error handler instance created")
        
        print("\n🎉 All imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1) 