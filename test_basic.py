#!/usr/bin/env python3
"""
Simple SHDC Test

Basic test to verify the SHDC package imports and CLI tools work correctly.
"""

import sys
import subprocess


def test_imports():
    """Test that all main modules can be imported"""
    print("Testing module imports...")
    
    try:
        import shdc
        print("  ✓ shdc package imported")
        
        from shdc.core.protocol import SHDCProtocol, DeviceRole
        print("  ✓ Protocol classes imported")
        
        from shdc.crypto.encryption import SHDCCrypto
        print("  ✓ Crypto classes imported")
        
        from shdc.crypto.keys import KeyManager
        print("  ✓ Key management imported")
        
        from shdc.network.transport import UDPTransport
        print("  ✓ Transport classes imported")
        
        from shdc.network.discovery import HubDiscovery
        print("  ✓ Discovery classes imported")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_cli_tools():
    """Test that CLI tools are available and show help"""
    print("\nTesting CLI tools...")
    
    try:
        # Test hub CLI
        result = subprocess.run(['/root/EOSL/.venv/bin/shdc-hub', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✓ shdc-hub CLI works")
        else:
            print(f"  ✗ shdc-hub failed: {result.stderr}")
            return False
        
        # Test sensor CLI
        result = subprocess.run(['/root/EOSL/.venv/bin/shdc-sensor', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✓ shdc-sensor CLI works")
        else:
            print(f"  ✗ shdc-sensor failed: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ✗ CLI test failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of key components"""
    print("\nTesting basic functionality...")
    
    try:
        # Test crypto operations
        from shdc.crypto.encryption import SHDCCrypto
        
        # Test key generation
        private_key, public_key = SHDCCrypto.generate_ed25519_keypair()
        print("  ✓ Ed25519 key generation works")
        
        # Test AES operations
        key = SHDCCrypto.generate_aes_key()
        plaintext = b"Hello SHDC!"
        nonce, ciphertext = SHDCCrypto.encrypt_aes_gcm(key, plaintext)
        decrypted = SHDCCrypto.decrypt_aes_gcm(key, nonce, ciphertext)
        
        if decrypted == plaintext:
            print("  ✓ AES-GCM encryption/decryption works")
        else:
            print("  ✗ AES-GCM test failed")
            return False
        
        # Test key manager
        from shdc.crypto.keys import KeyManager
        km = KeyManager(0x12345678)
        device_private, device_public = km.generate_device_keys()
        print("  ✓ Key manager works")
        
        # Test transport creation
        from shdc.network.transport import UDPTransport
        transport = UDPTransport(0, "127.0.0.1")
        print("  ✓ Transport creation works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=== SHDC Basic Test Suite ===\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("CLI Tools", test_cli_tools),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED\n")
        else:
            print(f"✗ {test_name} FAILED\n")
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! SHDC implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
