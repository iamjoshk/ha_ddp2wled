# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- WLED JSON now stored in Last Conversion sensor's `wled_json` attribute for easy access in automations

### Fixed
- Fixed issue where WLED JSON shows in web UI preview but device doesn't update
  - Automatically sets `fx=0` (Solid effect) for individual LED control
  - Automatically sets `sel=true` to mark segment as active
  - Automatically sets `liv=false` to disable live override mode
  - Applies to both single and chunked payload sending

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
