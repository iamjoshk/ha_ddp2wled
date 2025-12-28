# WLEDVideoSync Continuous Streaming Implementation

## Overview

This implementation adds **continuous streaming support** to the WLEDVideoSync integration, inspired by the [WLEDVideoSync tool](https://github.com/zak-45/WLEDVideoSync). The integration now supports both connection models:

1. **One-Shot Mode** (existing): Quick connect → send → disconnect
2. **Continuous Streaming Mode** (new): Connect once → send multiple frames → disconnect when done

## What Changed

### 1. Core DDP Protocol Enhancement (`ddp.py`)

**Added streaming session management:**
- `start_streaming()` - Opens persistent UDP socket
- `send_frame()` - Sends frames through open socket
- `stop_streaming()` - Closes socket and cleans up
- `is_streaming()` - Check session status

**Technical improvements:**
- Persistent socket connection (stays open between frames)
- Sequence number tracking for frame ordering
- Thread-safe operations with `asyncio.Lock`
- Proper resource cleanup on errors

### 2. New Services (`services.py`)

Added three new Home Assistant services:

**`pixelmagictool.start_streaming`**
```yaml
service: pixelmagictool.start_streaming
data:
  session_id: "my_stream"
  wled_host: "192.168.1.100"
  segment_id: 0
```

**`pixelmagictool.send_frame`**
```yaml
service: pixelmagictool.send_frame
data:
  session_id: "my_stream"
  image_url: "https://example.com/frame.jpg"
  width: 32
  height: 32
```

**`pixelmagictool.stop_streaming`**
```yaml
service: pixelmagictool.stop_streaming
data:
  session_id: "my_stream"
```

### 3. Image Processing (`converter.py`)

Added `process_image_to_rgb()` method:
- Processes images to RGB24 format
- No network sending (for streaming use)
- Used by `send_frame` service

### 4. Session Management (`__init__.py`)

- Global streaming sessions tracker
- Cleanup on integration unload
- Automatic session termination

### 5. Service Definitions (`services.yaml`)

Complete documentation for all three new services with:
- Parameter descriptions
- Examples
- Field selectors for UI

### 6. Documentation

**Created `STREAMING.md`:**
- Complete streaming guide
- Usage examples (slideshow, camera, weather)
- Best practices
- Troubleshooting
- Comparison table

**Updated `README.md`:**
- Added streaming mode section
- Updated services list
- Connection model comparison
- Links to streaming documentation

## Use Cases

### Continuous Streaming (New)

**Best for:**
- Animations and slideshows
- Frequent updates (>1 per second)
- Camera streams
- Live feeds
- Video-like sequences

**Example: Slideshow**
```yaml
script:
  slideshow:
    sequence:
      - service: pixelmagictool.start_streaming
        data:
          session_id: "slideshow"
          wled_host: "192.168.1.100"
      
      - service: pixelmagictool.send_frame
        data:
          session_id: "slideshow"
          image_path: "/config/www/image1.jpg"
          width: 32
          height: 32
      - delay: 2
      
      - service: pixelmagictool.send_frame
        data:
          session_id: "slideshow"
          image_path: "/config/www/image2.jpg"
          width: 32
          height: 32
      - delay: 2
      
      - service: pixelmagictool.stop_streaming
        data:
          session_id: "slideshow"
```

### One-Shot Mode (Existing)

**Best for:**
- Static images
- Triggered by automations
- Album art, weather icons
- Occasional updates

**Example: Album Art**
```yaml
automation:
  - alias: "Update Album Art"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
```

## Technical Details

### Connection Lifecycle

**One-Shot:**
```
1. Open socket
2. Send DDP packets
3. Close socket immediately
```

**Streaming:**
```
1. start_streaming: Open socket (stays open)
2. send_frame: Send DDP packets (socket remains open)
3. send_frame: Send more DDP packets (socket still open)
4. stop_streaming: Close socket
```

### Performance Comparison

| Metric | One-Shot | Streaming |
|--------|----------|-----------|
| Connection overhead | High per image | Low per frame |
| Best for | <1 update/sec | >1 update/sec |
| Resource usage | Minimal | One socket/session |
| Setup complexity | Simple (1 call) | 3-step process |

### Sequence Numbers

- Each frame gets incremented sequence number
- Wraps at 255 (0xFF)
- Helps WLED order packets correctly
- Important for multi-packet frames

## Backward Compatibility

✅ **Fully backward compatible**
- Existing `send_to_wled_ddp` service unchanged
- No breaking changes to existing automations
- New streaming services are optional
- Default behavior remains one-shot mode

## Testing

All tests pass:
- ✅ Existing DDP tests (test_ddp.py)
- ✅ New streaming tests (test_streaming.py)
- ✅ Code compiles without errors
- ✅ No regressions

## Files Changed

1. `custom_components/pixelmagictool/ddp.py` - Streaming session support
2. `custom_components/pixelmagictool/converter.py` - Frame processing
3. `custom_components/pixelmagictool/services.py` - New services
4. `custom_components/pixelmagictool/services.yaml` - Service documentation
5. `custom_components/pixelmagictool/const.py` - Service constants
6. `custom_components/pixelmagictool/__init__.py` - Session management
7. `STREAMING.md` - New documentation file
8. `README.md` - Updated with streaming info
9. `test_streaming.py` - New test file

## Implementation Status

✅ **Complete and tested**

The integration now properly implements WLEDVideoSync-style continuous streaming as requested, while maintaining full backward compatibility with the existing one-shot connection model.

## Next Steps for Users

1. **Review documentation**: Read [STREAMING.md](STREAMING.md)
2. **Try streaming mode**: Test with a simple slideshow
3. **Evaluate use case**: Choose between one-shot and streaming
4. **Update automations**: Migrate to streaming if beneficial

## Support

For questions or issues with streaming mode:
- See [STREAMING.md](STREAMING.md) for detailed guide
- Check [FAQ.md](FAQ.md) for connection model explanations
- Review examples in STREAMING.md
- Open GitHub issue for bugs
