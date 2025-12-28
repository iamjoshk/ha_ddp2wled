# WLED-MM (MoonModules) Compatibility Guide

## Overview

This integration is fully compatible with both **stable WLED** and **WLED-MM** (MoonModules fork). WLED-MM is an enhanced version of WLED with advanced features like sound reactivity, larger installations support, and 2D effects. However, WLED-MM devices running on ESP32/ESP8266 have more constrained memory resources, which can cause loading or freezing issues when receiving large JSON payloads.

## What is WLED-MM?

WLED-MM (MoonModules) is a community-maintained fork of WLED that includes:
- Advanced sound reactive effects
- Support for larger LED installations
- Enhanced 2D matrix capabilities
- Additional audio analysis features
- Experimental features and optimizations

**Website**: https://mm.kno.wled.ge/

## Common Issues with WLED-MM

### Loading/Freezing Issues

WLED-MM devices may experience:
- Device freezing when receiving large JSON payloads
- Slow response times or timeouts
- Web UI becoming unresponsive
- Device rebooting or crashing

These issues are typically caused by:
1. **Limited RAM**: ESP32/ESP8266 devices have constrained memory (especially when running advanced features)
2. **Large payloads**: High-resolution images (32x32, 64x64) generate large JSON payloads (20-30KB+)
3. **JSON processing overhead**: Parsing and applying large JSON objects requires significant memory

## Solutions and Best Practices

### 1. Enable Chunked Sending

Split large payloads into smaller sequential requests:

```yaml
service: pixelmagictool.send_to_wled
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 128
  pattern: "range"
  segment_id: 0
  use_chunks: true          # Enable chunked sending
  chunk_size: 128           # Conservative chunk size for WLED-MM
  chunk_delay: 0.2          # Longer delay for stability
```

### 2. Optimize Chunk Parameters

#### Chunk Size
- **Default**: 128 LEDs per chunk (optimized for WLED-MM)
- **Stable WLED**: Can use up to 256 LEDs per chunk
- **Constrained devices**: Try 64 LEDs for very limited RAM

```yaml
chunk_size: 128    # Good for most WLED-MM devices
chunk_size: 64     # For very constrained devices
chunk_size: 256    # For stable WLED or well-equipped devices
```

#### Chunk Delay
- **Default**: 0.15 seconds (150ms) between chunks
- **WLED-MM**: Increase to 0.2-0.5s for better stability
- **Fast devices**: Can reduce to 0.1s

```yaml
chunk_delay: 0.15   # Default, good balance
chunk_delay: 0.2    # Better for WLED-MM stability
chunk_delay: 0.5    # For very slow/unstable devices
```

### 3. Enable Compression

Reduce payload size before sending:

```yaml
service: pixelmagictool.send_to_wled
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  compression: true         # Enable compression
  compression_level: 5      # 1=gentle, 10=aggressive
```

### 4. Use Colors-Only Mode

Send minimal payload with just color data:

```yaml
service: pixelmagictool.send_to_wled
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  colors_only: true         # Reduces overhead by ~40-60 bytes
```

### 5. Reduce Image Dimensions

Smaller images = smaller payloads:

```yaml
width: 16     # Instead of 32
height: 16    # Instead of 32
```

**Pixel count impact**:
- 16x16 = 256 LEDs (~5-8KB payload)
- 24x24 = 576 LEDs (~12-18KB payload)
- 32x32 = 1,024 LEDs (~20-30KB payload)
- 64x64 = 4,096 LEDs (~80-120KB payload) - **Requires chunking!**

### 6. Use Range Pattern

The "range" pattern is most memory-efficient:

```yaml
pattern: "range"    # Most efficient (recommended)
```

## Complete WLED-MM Example

Here's a complete example optimized for WLED-MM devices:

```yaml
automation:
  - alias: "Display Album Art on WLED-MM"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_to_wled
        data:
          # Image source
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          
          # Image parameters
          width: 32
          height: 32
          brightness: 128
          pattern: "range"
          segment_id: 0
          
          # WLED-MM optimizations
          use_chunks: true        # Split into chunks
          chunk_size: 128         # Conservative size
          chunk_delay: 0.2        # Longer delay for stability
          compression: true       # Reduce payload size
          compression_level: 5    # Balanced compression
          colors_only: true       # Minimal overhead
```

## Troubleshooting

### Device Still Freezing?

1. **Reduce chunk size**: Try `chunk_size: 64` or even `chunk_size: 32`
2. **Increase delay**: Try `chunk_delay: 0.5` or even `chunk_delay: 1.0`
3. **Reduce resolution**: Try 16x16 or 24x24 instead of 32x32
4. **Check WLED-MM version**: Update to the latest version for bug fixes
5. **Disable unused features**: In WLED-MM, disable unused features (MQTT, Alexa, etc.) to free RAM

### Slow Updates?

- This is normal with chunked sending (more chunks = slower)
- Example: 32x32 (1024 LEDs) with chunk_size=128 = 8 chunks
- At 0.2s delay: Total time = ~1.6 seconds
- Trade-off: Slower updates for stability

### Payload Too Large Error?

Even with chunking, individual chunks might be too large:
1. Reduce `chunk_size` further (try 64 or 32)
2. Enable `colors_only: true` to reduce chunk overhead
3. Reduce image dimensions
4. Ensure `compression: true` is enabled

### API Response Timeout?

If chunks are taking too long:
1. Increase `timeout` parameter (default 10s)
2. Reduce total LED count (smaller image)
3. Check network connectivity

## Performance Comparison

### Without Optimization (32x32 image)
```yaml
use_chunks: false
# Result: ~25KB payload, often freezes WLED-MM
```

### With Basic Optimization
```yaml
use_chunks: true
chunk_size: 128
# Result: 8 chunks of ~3KB each, much more stable
```

### With Full Optimization
```yaml
use_chunks: true
chunk_size: 128
chunk_delay: 0.2
compression: true
colors_only: true
# Result: 8 chunks of ~2.5KB each, most stable
```

## Hardware Recommendations

For better WLED-MM performance:
- **ESP32 with PSRAM**: Better memory handling for large installations
- **Wired Ethernet**: More reliable than WiFi for data transfer
- **Quality Power Supply**: Prevents brownouts during intensive processing

## Additional Resources

- **WLED-MM Documentation**: https://mm.kno.wled.ge/
- **WLED-MM GitHub**: https://github.com/MoonModules/WLED-MM
- **WLED-MM Discord**: Community support and troubleshooting
- **Stable WLED**: https://kno.wled.ge/ (for comparison)

## Summary

WLED-MM devices work great with this integration when using the proper settings:
- ✅ Use chunked sending (`use_chunks: true`)
- ✅ Conservative chunk size (128 or less)
- ✅ Adequate delay between chunks (0.15-0.5s)
- ✅ Enable compression when possible
- ✅ Use range pattern for efficiency
- ✅ Consider colors-only mode for minimal overhead
- ✅ Keep image dimensions reasonable (32x32 or less for most devices)

With these optimizations, you can reliably display dynamic images on WLED-MM devices without freezing or crashing!
