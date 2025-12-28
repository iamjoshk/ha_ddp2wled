# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- WLED JSON now stored in Last Conversion sensor's `wled_json` attribute for easy access in automations
- WLED-MM (MoonModules) compatibility improvements:
  - Added `chunk_delay` parameter to control delay between chunks (default 0.15s)
  - Reduced default `chunk_size` from 256 to 128 LEDs for better WLED-MM compatibility
  - Configurable chunk delay range: 0.05s to 2.0s
  - Enhanced documentation with WLED-MM troubleshooting guide
  - Added example configurations optimized for WLED-MM devices

### Changed
- Default chunk size changed from 256 to 128 LEDs for improved compatibility with WLED-MM devices
- Chunk delay is now configurable (was fixed at 0.1s, now default 0.15s)
- Updated documentation to explicitly mention WLED-MM (MoonModules) compatibility

### Fixed
- Fixed issue where WLED JSON shows in web UI preview but device doesn't update
  - Automatically sets `fx=0` (Solid effect) for individual LED control
  - Automatically sets `sel=true` to mark segment as active
  - Automatically sets `live=false` to disable live override mode (was `liv`, now `live`)
  - Applies to both single and chunked payload sending
- Improved stability for WLED-MM devices by using more conservative chunking defaults

## [1.0.0] - 2025-12-27

### Added
- Initial release as Home Assistant add-on
- HACS compatibility
- Web interface accessible through Home Assistant
- Support for all architectures (armhf, armv7, aarch64, amd64, i386)
- Ingress support for seamless integration with Home Assistant
- Complete feature set from original Pixel Magic Tool:
  - Image to WLED JSON conversion
  - Multiple output formats (JSON, Home Assistant YAML, CURL)
  - Pattern options (Individual, Index, Range)
  - Brightness control
  - Animated GIF support
  - Image resizing
  - Transparent pixel handling
  - Compression for large images
  - Preview and simulation capabilities
