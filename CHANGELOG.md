# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **DDP Protocol Support** 🚀 - New recommended method for sending images to WLED
  - Added `send_to_wled_ddp` service for DDP protocol communication
  - Direct UDP streaming to WLED devices on port 4048
  - Better performance and reliability compared to JSON API
  - No payload size limits - handles large matrices efficiently
  - Automatic packet fragmentation for matrices of any size
  - Based on WLEDVideoSync approach
- New `ddp.py` module implementing DDP packet structure
- Image processing with Pillow for DDP (resize, RGB24 conversion, brightness adjustment)
- Comprehensive documentation for DDP protocol
- Test suite for DDP implementation
- Comparison guide for choosing between DDP and JSON API protocols
- WLED JSON now stored in Last Conversion sensor's `wled_json` attribute for easy access in automations
- WLED-MM (MoonModules) compatibility improvements:
  - Added `chunk_delay` parameter to control delay between chunks (default 0.15s)
  - Reduced default `chunk_size` from 256 to 128 LEDs for better WLED-MM compatibility
  - Configurable chunk delay range: 0.05s to 2.0s
  - Enhanced documentation with WLED-MM troubleshooting guide
  - Added example configurations optimized for WLED-MM devices

### Changed
- Updated manifest.json to version 1.1.0
- Added Pillow (PIL) as a dependency
- Enhanced README with DDP protocol information and usage examples
- Updated service definitions with DDP protocol options
- Default chunk size changed from 256 to 128 LEDs for improved compatibility with WLED-MM devices
- Chunk delay is now configurable (was fixed at 0.1s, now default 0.15s)
- Updated documentation to explicitly mention WLED-MM (MoonModules) compatibility

### Fixed
- Fixed issue where WLED JSON shows in web UI preview but device doesn't update
  - Automatically sets `fx=0` (Solid effect) for individual LED control
  - Automatically sets `sel=true` to mark segment as active
  - Automatically sets `live=false` to disable live override mode
  - Applies to both single and chunked payload sending
- **Fixed DDP realtime mode reversion issue** - LEDs no longer freeze/turn off and resume previous settings
  - DDP now prepares WLED device before sending packets
  - Sends HTTP API call to disable live override mode (`live: false`)
  - Sets segment to Solid effect (`fx: 0`) for individual LED control
  - Marks segment as selected/active (`sel: true`)
  - Ensures DDP updates persist as actual LED state, not temporary realtime buffer
  - Handles preparation failures gracefully (continues with DDP if HTTP call fails)
- Improved stability for WLED-MM devices by using more conservative chunking defaults

### Migration Notes
- **Recommended**: Switch from `send_to_wled` to `send_to_wled_ddp` for better performance
- DDP service requires `width` and `height` parameters (no defaults)
- DDP uses brightness 0-255 (255 = full brightness)
- Existing `send_to_wled` and `convert_image` services remain unchanged for backward compatibility
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
