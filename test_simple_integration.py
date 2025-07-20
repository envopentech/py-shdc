#!/usr/bin/env python3
"""
Simple SHDC Integration Test

Test basic SHDC components work together without complex protocol flows.
"""

import asyncio
import logging

from shdc.core.protocol import DeviceRole, SHDCProtocol
from shdc.crypto.encryption import SHDCCrypto
from shdc.crypto.keys import KeyManager
from shdc.network.discovery import HubDiscovery
from shdc.network.transport import UDPTransport


class SimpleIntegrationTest:
    """Simple integration test for SHDC components"""

    def __init__(self):
        self.logger = logging.getLogger("shdc_simple_test")
        self.logger.setLevel(logging.INFO)

    async def test_component_creation(self):
        """Test that all components can be created"""
        print("=== Simple SHDC Integration Test ===\n")

        results = {
            "protocol_creation": False,
            "crypto_operations": False,
            "key_management": False,
            "transport_creation": False,
            "discovery_creation": False,
        }

        try:
            # Test 1: Protocol creation
            print("Test 1: Creating SHDC Protocol instances...")
            hub_protocol = SHDCProtocol(
                DeviceRole.HUB, device_id=0x12345678, port=56700
            )
            sensor_protocol = SHDCProtocol(
                DeviceRole.SENSOR, device_id=0x87654321, port=56701
            )
            results["protocol_creation"] = True
            print("  ✓ Protocol instances created")

            # Test 2: Crypto operations
            print("\nTest 2: Testing crypto operations...")
            crypto = SHDCCrypto()

            # Test key generation
            private_key, public_key = SHDCCrypto.generate_ed25519_keypair()
            print(f"  ✓ Ed25519 keypair generated")

            # Test AES encryption
            plaintext = b"Hello SHDC World!"
            nonce, encrypted = crypto.encrypt_aes_gcm(
                b"0" * 32, plaintext
            )  # 32-byte key
            decrypted = crypto.decrypt_aes_gcm(b"0" * 32, nonce, encrypted)
            assert decrypted == plaintext
            results["crypto_operations"] = True
            print("  ✓ AES-GCM encryption/decryption works")

            # Test 3: Key management
            print("\nTest 3: Testing key management...")
            key_manager = KeyManager(0x12345678)
            device_keys = key_manager.generate_device_keys()
            results["key_management"] = True
            print("  ✓ Key manager works")

            # Test 4: Transport creation
            print("\nTest 4: Testing transport creation...")
            transport1 = UDPTransport(56700, "127.0.0.1")
            transport2 = UDPTransport(56701, "127.0.0.1")
            results["transport_creation"] = True
            print("  ✓ UDP transports created")

            # Test 5: Discovery creation
            print("\nTest 5: Testing discovery creation...")
            discovery = HubDiscovery()
            results["discovery_creation"] = True
            print("  ✓ Hub discovery created")

        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            self.logger.exception("Test failed")
            return results

        return results

    async def test_transport_communication(self):
        """Test basic transport communication"""
        print("\nTest 6: Testing transport communication...")

        transport1 = None
        transport2 = None

        try:
            # Create two transports
            transport1 = UDPTransport(56702, "127.0.0.1")
            transport2 = UDPTransport(56703, "127.0.0.1")

            # Start them
            await transport1.start()
            await transport2.start()

            # Test sending a simple message
            test_message = b"Hello from transport test!"
            await transport1.send_to(test_message, ("127.0.0.1", 56703))

            # Give it a moment to send
            await asyncio.sleep(0.1)

            print("  ✓ Transport communication test completed")
            return True

        except Exception as e:
            print(f"  ✗ Transport test failed: {e}")
            return False

        finally:
            # Clean up
            if transport1:
                try:
                    await transport1.stop()
                except:
                    pass
            if transport2:
                try:
                    await transport2.stop()
                except:
                    pass


async def run_simple_test():
    """Run the simple integration test"""
    test = SimpleIntegrationTest()

    # Run component tests
    results = await test.test_component_creation()

    # Run transport tests
    transport_result = await test.test_transport_communication()
    results["transport_communication"] = transport_result

    # Print results
    print("\n=== Test Results ===")
    passed = 0
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! SHDC components are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

    return passed == total


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(run_simple_test())
