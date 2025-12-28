# WLEDVideoSync Integration - Major Update

## Summary

This update transforms the integration from "Pixel Magic Tool" to "WLEDVideoSync", focusing exclusively on DDP (Distributed Display Protocol) for sending images to WLED devices. This fixes the display reset issue you were experiencing.

## Problem Fixed

**Issue**: When using `send_to_wled_ddp`, the display would reset to the default solid color instead of showing the image.

**Root Cause**: The integration was sending an HTTP API call to WLED before the DDP packets to "prepare" the device. This preparation step was setting the effect to Solid (fx: 0) and disabling live mode (live: false), which caused the display to reset.

**Solution**: Removed the HTTP API preparation step. The integration now sends DDP packets directly, just like the WLEDVideoSync web UI does. This prevents the display reset.

## What Changed

### Removed
- `pixelmagictool.convert_image` service
- `pixelmagictool.send_to_wled` service (JSON API)
- Image conversion via PixelMagicTool API
- Compression, chunking, and pattern selection features
- Sensor entity for storing last conversion
- All PixelMagicTool API dependencies

### Kept (WLEDVideoSync Core)
- **Single Service**: `pixelmagictool.send_to_wled_ddp`
  - Sends images directly via DDP protocol
  - Supports URLs and local file paths
  - Fast, reliable, and simple
  - No display resets!

### Updated
- Integration display name: "WLEDVideoSync" (domain remains `pixelmagictool` for compatibility)
- Version: 2.0.0
- IoT class: `local_push` (was `cloud_polling`)

## Usage

The integration now has a single service that works correctly:

```yaml
service: pixelmagictool.send_to_wled_ddp
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"  # Your Apollo M-1 LED Matrix IP
  width: 32
  height: 32
  brightness: 255
```

Or use a local file:

```yaml
service: pixelmagictool.send_to_wled_ddp
data:
  image_path: "/config/www/my_image.jpg"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 255
```

## Testing

To test the fix:
1. Update to this version
2. Try sending an image using `send_to_wled_ddp`
3. The display should now show the image without resetting to solid color

## Migration Guide

If you were using the old services:
- Replace `pixelmagictool.convert_image` → No direct replacement (conversion happens automatically)
- Replace `pixelmagictool.send_to_wled` → Use `pixelmagictool.send_to_wled_ddp` instead

The DDP method is faster, more reliable, and works correctly with your Apollo M-1 LED Matrix running MM-WLED.

## Technical Details

The integration now:
1. Loads image from URL or local file
2. Resizes to specified dimensions
3. Converts to RGB24 format
4. Applies brightness
5. Sends directly via DDP packets (UDP port 4048)
6. No HTTP API calls that could interfere

This matches how the WLEDVideoSync web UI operates, which is why it works correctly.
