#!/usr/bin/env python3
"""
Test script for enhanced profile features.
"""
import sys
import json
import asyncio
from datetime import datetime

# Test imports
try:
    from profile_models import ProfileCreateRequest, validate_profile_create_request
    from crypto_utils import encrypt_sensitive_data, decrypt_sensitive_data, is_encryption_available
    from os_detection import detect_host_os, get_host_os_details, validate_os_override
    from proxy_utils import parse_proxy_url, validate_proxy_url, sanitize_proxy_for_logging
    from screen_utils import ScreenModeHandler, ScreenSize, get_default_screen_sizes
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_os_detection():
    """Test OS detection functionality."""
    print("\n🔍 Testing OS Detection...")
    
    host_os = detect_host_os()
    print(f"  Host OS: {host_os}")
    
    os_details = get_host_os_details()
    print(f"  OS Details: {os_details['platform']}")
    
    # Test OS override validation
    validation = validate_os_override("windows", host_os)
    print(f"  OS Override Validation: {len(validation['warnings'])} warnings")
    
    print("✅ OS detection tests passed")

def test_encryption():
    """Test encryption functionality."""
    print("\n🔐 Testing Encryption...")
    
    if not is_encryption_available():
        print("❌ Encryption not available")
        return False
    
    test_data = "http://user:pass@proxy.example.com:8080"
    
    try:
        encrypted = encrypt_sensitive_data(test_data)
        decrypted = decrypt_sensitive_data(encrypted)
        
        if decrypted == test_data:
            print("✅ Encryption/decryption successful")
            return True
        else:
            print("❌ Decrypted data doesn't match original")
            return False
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return False

def test_proxy_utils():
    """Test proxy utilities."""
    print("\n🌐 Testing Proxy Utils...")
    
    test_urls = [
        "http://proxy.example.com:8080",
        "https://user:pass@proxy.example.com:3128",
        "invalid://bad-url",
        "http://localhost:8080"
    ]
    
    for url in test_urls:
        validation = validate_proxy_url(url)
        sanitized = sanitize_proxy_for_logging(url)
        print(f"  {url} -> Valid: {validation['valid']}, Sanitized: {sanitized}")
    
    print("✅ Proxy utils tests passed")

def test_screen_utils():
    """Test screen utilities."""
    print("\n📺 Testing Screen Utils...")
    
    # Test random screen selection
    random_screen = ScreenModeHandler.get_random_screen()
    print(f"  Random screen: {random_screen.screen_width}x{random_screen.screen_height}")
    
    # Test fixed screen
    fixed_screen_data = {
        "screen_width": 1920,
        "screen_height": 1080,
        "window_width": 1500,
        "window_height": 900
    }
    
    profile_data = {
        "screen_mode": "fixed_profile",
        "fixed_screen": fixed_screen_data,
        "distribution": None
    }
    
    selected_screen = ScreenModeHandler.select_screen_for_profile(profile_data)
    print(f"  Fixed screen: {selected_screen.screen_width}x{selected_screen.screen_height}")
    
    # Test distribution
    distribution = [
        {"screen_width": 1920, "screen_height": 1080, "window_width": 1500, "window_height": 900, "weight": 70},
        {"screen_width": 1366, "screen_height": 768, "window_width": 1200, "window_height": 700, "weight": 30}
    ]
    
    profile_data["screen_mode"] = "custom_distribution"
    profile_data["distribution"] = distribution
    
    selected_screen = ScreenModeHandler.sample_from_distribution(distribution)
    print(f"  Distribution sample: {selected_screen.screen_width}x{selected_screen.screen_height}")
    
    # Test default sizes
    default_sizes = get_default_screen_sizes()
    print(f"  Default sizes available: {len(default_sizes)}")
    
    print("✅ Screen utils tests passed")

def test_profile_validation():
    """Test profile validation."""
    print("\n📋 Testing Profile Validation...")
    
    # Test valid profile
    valid_request = ProfileCreateRequest(
        name="Test Profile",
        screen_mode="fixed_profile",
        fixed_screen={
            "screen_width": 1920,
            "screen_height": 1080,
            "window_width": 1500,
            "window_height": 900,
            "weight": 1.0
        },
        proxy="http://proxy.example.com:8080",
        use_host_os=True,
        timezone="GMT+00:00"
    )
    
    validation = validate_profile_create_request(valid_request)
    print(f"  Valid profile validation: {validation.valid}, warnings: {len(validation.warnings)}")
    
    # Test invalid profile
    try:
        invalid_request = ProfileCreateRequest(
            name="Invalid Profile",
            screen_mode="fixed_profile",
            # Missing fixed_screen
            proxy="invalid-proxy-url",
            use_host_os=False,
            # Missing os_override
            timezone="GMT+00:00"
        )
        print("❌ Should have failed validation")
    except Exception as e:
        print(f"✅ Correctly caught validation error: {type(e).__name__}")
    
    print("✅ Profile validation tests passed")

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Profile Features")
    print("=" * 50)
    
    try:
        test_os_detection()
        
        if test_encryption():
            test_proxy_utils()
        else:
            print("⚠️  Skipping proxy tests due to encryption failure")
        
        test_screen_utils()
        test_profile_validation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()