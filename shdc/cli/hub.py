#!/usr/bin/env python3
"""
SHDC Hub CLI Tool

Command-line interface for running an SHDC hub device.
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from shdc.core.protocol import SHDCProtocol, DeviceRole
from shdc.crypto.keys import KeyManager
from shdc.network.transport import UDPTransport


class SHDCHubCLI:
    """SHDC Hub command-line interface"""
    
    def __init__(self):
        self.protocol: Optional[SHDCProtocol] = None
        self.running = False
        
    async def run_hub(self, device_id: int, interface: str = "0.0.0.0", 
                     port: int = 56700, debug: bool = False):
        """
        Run SHDC hub.
        
        Args:
            device_id: Hub device ID
            interface: Network interface to bind to
            port: UDP port to listen on
            debug: Enable debug logging
        """
        # Set up logging
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger = logging.getLogger('shdc.hub')
        
        try:
            # Initialize key manager
            logger.info(f"Initializing hub {device_id:08X}")
            key_manager = KeyManager(device_id)
            
            # Generate or load device keys
            private_key, public_key = key_manager.generate_device_keys()
            logger.info(f"Device keys ready")
            
            # Initialize transport
            transport = UDPTransport(port, interface)
            await transport.start()
            logger.info(f"UDP transport started on {interface}:{port}")
            
            # Initialize protocol
            self.protocol = SHDCProtocol(
                device_id=device_id,
                device_role=DeviceRole.HUB,
                private_key=private_key,
                key_manager=key_manager,
                transport=transport
            )
            
            # Start protocol
            await self.protocol.start()
            logger.info(f"SHDC hub started - ID: {device_id:08X}")
            
            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info("Received shutdown signal")
                self.running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Main loop
            self.running = True
            while self.running:
                try:
                    await asyncio.sleep(1)
                    
                    # Periodic maintenance
                    key_manager.cleanup_expired_keys()
                    
                    # Log connected devices
                    connected_devices = self.protocol.get_connected_devices()
                    if debug and connected_devices:
                        logger.debug(f"Connected devices: {len(connected_devices)}")
                        for device_info in connected_devices:
                            logger.debug(f"  Device {device_info.device_id:08X}: {device_info.device_type}")
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    if debug:
                        import traceback
                        traceback.print_exc()
        
        except Exception as e:
            logger.error(f"Failed to start hub: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            return 1
        
        finally:
            # Cleanup
            if self.protocol:
                logger.info("Shutting down hub")
                await self.protocol.stop()
            
            logger.info("Hub stopped")
        
        return 0
    
    def show_status(self, device_id: int):
        """Show hub status"""
        print(f"SHDC Hub Status - Device ID: {device_id:08X}")
        
        # Check if keys exist
        key_manager = KeyManager(device_id)
        keys = key_manager.list_keys()
        
        print(f"Stored keys: {len(keys)}")
        for key_info in keys:
            status = "EXPIRED" if key_info.is_expired() else "VALID"
            print(f"  {key_info.key_id}: {key_info.key_type} ({status})")
        
        # Show storage path
        print(f"Key storage: {key_manager.storage_path}")
    
    def reset_keys(self, device_id: int, confirm: bool = False):
        """Reset all keys for device"""
        if not confirm:
            print("This will delete all stored keys for the device.")
            response = input(f"Are you sure you want to reset keys for device {device_id:08X}? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled")
                return
        
        key_manager = KeyManager(device_id)
        
        # Remove all keys
        for key_info in key_manager.list_keys():
            key_manager._delete_key(key_info.key_id)
        
        print(f"All keys reset for device {device_id:08X}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SHDC Hub - Smart Home Device Communications Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shdc-hub run 0x12345678                    # Run hub with device ID
  shdc-hub run 0x12345678 --debug            # Run with debug logging
  shdc-hub run 0x12345678 -i eth0 -p 56700   # Specify interface and port
  shdc-hub status 0x12345678                 # Show hub status
  shdc-hub reset-keys 0x12345678             # Reset all keys
        """
    )
    
    parser.add_argument('--version', action='version', version='SHDC Hub 1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run SHDC hub')
    run_parser.add_argument('device_id', help='Hub device ID (hex format, e.g., 0x12345678)')
    run_parser.add_argument('-i', '--interface', default='0.0.0.0',
                           help='Network interface to bind to (default: 0.0.0.0)')
    run_parser.add_argument('-p', '--port', type=int, default=56700,
                           help='UDP port to listen on (default: 56700)')
    run_parser.add_argument('-d', '--debug', action='store_true',
                           help='Enable debug logging')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show hub status')
    status_parser.add_argument('device_id', help='Hub device ID (hex format)')
    
    # Reset keys command
    reset_parser = subparsers.add_parser('reset-keys', help='Reset all keys')
    reset_parser.add_argument('device_id', help='Hub device ID (hex format)')
    reset_parser.add_argument('-y', '--yes', action='store_true',
                             help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Parse device ID
    try:
        if args.device_id.startswith('0x') or args.device_id.startswith('0X'):
            device_id = int(args.device_id, 16)
        else:
            device_id = int(args.device_id)
        
        if not (0 <= device_id <= 0xFFFFFFFF):
            print("Error: Device ID must be a 32-bit unsigned integer")
            return 1
    except ValueError:
        print("Error: Invalid device ID format")
        return 1
    
    # Create CLI instance
    cli = SHDCHubCLI()
    
    # Execute command
    if args.command == 'run':
        try:
            return asyncio.run(cli.run_hub(
                device_id=device_id,
                interface=args.interface,
                port=args.port,
                debug=args.debug
            ))
        except KeyboardInterrupt:
            print("\nShutdown requested")
            return 0
    
    elif args.command == 'status':
        cli.show_status(device_id)
        return 0
    
    elif args.command == 'reset-keys':
        cli.reset_keys(device_id, confirm=args.yes)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
