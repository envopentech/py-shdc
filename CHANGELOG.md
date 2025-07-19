# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-20

### Added
- Initial production release of py-shdc
- Complete SHDC v1.0 protocol implementation
- Ed25519 cryptographic signatures for device authentication
- AES-256-GCM encryption for secure data transmission
- Key management system with automatic rotation
- UDP transport layer with multicast support
- Hub discovery service for device auto-configuration
- CLI tools: `shdc-hub` and `shdc-sensor`
- Comprehensive test suite with >95% coverage
- Example implementations:
  - Temperature sensor simulation
  - Home monitoring system
- Full type annotations for mypy compatibility
- Production-ready packaging and distribution

### Security
- Implemented SHDC security model with end-to-end encryption
- Device fingerprinting for identity verification
- Secure session establishment with forward secrecy
- Protection against replay attacks with timestamps
- Cryptographically secure random number generation

### Documentation
- Complete API documentation
- Protocol specification implementation
- Usage examples and tutorials
- Installation and deployment guides

## [Unreleased]

### Planned
- WebSocket transport layer
- MQTT bridge integration
- Device management dashboard
- Configuration management tools
- Performance monitoring and metrics
