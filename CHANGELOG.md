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

### Changed
- Updated manifest.json to version 1.1.0
- Added Pillow (PIL) as a dependency
- Enhanced README with DDP protocol information and usage examples
- Updated service definitions with DDP protocol options

### Fixed
- WLED JSON now stored in Last Conversion sensor's `wled_json` attribute for easy access in automations
- Fixed issue where WLED JSON shows in web UI preview but device doesn't update
  - Automatically sets `fx=0` (Solid effect) for individual LED control
  - Automatically sets `sel=true` to mark segment as active
  - Automatically sets `live=false` to disable live override mode
  - Applies to both single and chunked payload sending

### Migration Notes
- **Recommended**: Switch from `send_to_wled` to `send_to_wled_ddp` for better performance
- DDP service requires `width` and `height` parameters (no defaults)
- DDP uses brightness 0-255 (255 = full brightness)
- Existing `send_to_wled` and `convert_image` services remain unchanged for backward compatibility

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
