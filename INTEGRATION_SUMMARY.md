# Pixel Magic Tool - Home Assistant Integration Summary

## Overview

This repository has been transformed into a Home Assistant custom integration that allows you to **convert images from sensor attributes (like album art URLs) to pixel art for WLED HUB75 devices**.

## Architecture

```
┌─────────────────────┐
│  Home Assistant     │
│  ─────────────────  │
│  Sensor Attribute   │ (e.g., media_player.spotify.entity_picture)
│  (Image URL)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Service Call       │
│  pixelmagictool.*   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  API Client         │ Downloads image and sends to:
│  (converter.py)     │ pixelmagictool.vercel.app/api/wled/image
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  WLED JSON Result   │
└──────────┬──────────┘
           │
           ├──► Stored in sensor.pixel_magic_tool_last_conversion
           │
           └──► Sent directly to WLED device (if using send_to_wled)
```

## Key Components

### 1. Custom Integration (`custom_components/pixelmagictool/`)

- **`manifest.json`**: Integration metadata and dependencies
- **`__init__.py`**: Setup and platform loading
- **`const.py`**: Constants and configuration defaults
- **`config_flow.py`**: UI configuration flow
- **`converter.py`**: API client for pixelmagictool.vercel.app
- **`sensor.py`**: Sensor entity to store last conversion
- **`services.py`**: Service handlers
- **`services.yaml`**: Service definitions for HA UI
- **`translations/en.json`**: UI strings

### 2. Services

#### `pixelmagictool.convert_image`
Converts an image URL to WLED JSON and stores it in the sensor.

```yaml
service: pixelmagictool.convert_image
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  width: 32
  height: 32
  brightness: 128
  pattern: "range"
  segment_id: 0
```

#### `pixelmagictool.send_to_wled`
Converts an image URL and sends it directly to a WLED device.

```yaml
service: pixelmagictool.send_to_wled
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 128
  pattern: "range"
```

### 3. Sensor Entity

**`sensor.pixel_magic_tool_last_conversion`**

Attributes:
- `last_image_url`: URL of the last converted image
- `wled_json`: Complete WLED JSON payload (as string)
- `segment_id`: Segment ID used
- `brightness`: Brightness level used

## Installation

### Via HACS (Recommended)
1. Add custom repository: `https://github.com/iamjoshk/PixelMagicTool`
2. Category: Integration
3. Install "Pixel Magic Tool"
4. Restart Home Assistant
5. Add integration via UI: Settings → Devices & Services → Add Integration

### Manual
1. Copy `custom_components/pixelmagictool/` to your HA `custom_components/` directory
2. Restart Home Assistant
3. Add integration via UI

## Common Use Cases

### 1. Album Art Display
Automatically show current playing album art on LED matrix:
```yaml
automation:
  - trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
```

### 2. Weather Icons
Display current weather as pixel art:
```yaml
automation:
  - trigger:
      - platform: state
        entity_id: weather.home
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "https://example.com/weather/{{ states('weather.home') }}.png"
          wled_host: "192.168.1.100"
```

### 3. Camera Snapshots
Show doorbell camera on LED when motion detected:
```yaml
automation:
  - trigger:
      - platform: state
        entity_id: binary_sensor.doorbell_motion
        to: "on"
    action:
      - service: camera.snapshot
        target:
          entity_id: camera.doorbell
        data:
          filename: /config/www/doorbell.jpg
      - delay: 2
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/doorbell.jpg"
          wled_host: "192.168.1.100"
```

## Technical Details

### API Integration
The integration uses the existing **pixelmagictool.vercel.app** API:
- No local image processing needed
- Proven, reliable conversion engine
- Supports all standard image formats
- Handles resizing and color conversion
- Returns WLED-compatible JSON

### Pattern Types
- **`range`**: Most efficient (default) - groups consecutive colors
- **`index`**: Explicit pixel addressing
- **`individual`**: Simple color list

### Sensor Updates
The sensor updates via Home Assistant event bus:
1. Service called
2. Image converted via API
3. Event fired: `pixelmagictool_conversion_complete`
4. Sensor catches event and updates attributes

## Files Included

### Integration Files
- `/custom_components/pixelmagictool/` - Full integration code
- `/hacs.json` - HACS metadata

### Documentation
- `/README.md` - Main documentation with quick start
- `/EXAMPLES.md` - Comprehensive automation examples
- `/DOCS.md` - Additional documentation
- `/CHANGELOG.md` - Version history
- `/INTEGRATION_SUMMARY.md` - This file

### Legacy Web Interface (Still Available)
- `/pxmagic.htm` - Full-featured web interface
- `/inpxmagic.htm` - Inline/URL-parameter version
- Can be uploaded to WLED or used standalone

### Add-on Files (Alternative Approach - Not Required)
- `/Dockerfile`, `/config.yaml`, `/build.yaml`, `/run.sh` - For add-on approach
- Not needed for the custom integration approach

## Requirements

- Home Assistant 2023.3.0 or newer
- WLED device with 2D Matrix or HUB75 configuration
- Network access to pixelmagictool.vercel.app API
- Image sources (media players, weather, cameras, etc.)

## Benefits of This Approach

1. ✅ **Leverages Existing API**: Uses proven pixelmagictool.vercel.app conversion
2. ✅ **Template Support**: Can read from any sensor attribute
3. ✅ **Automation Ready**: Perfect for media players, weather, cameras
4. ✅ **Sensor Storage**: Reuse conversions without re-converting
5. ✅ **HACS Compatible**: Easy installation and updates
6. ✅ **No Dependencies**: No PIL/Pillow or local image processing
7. ✅ **Cloud-based**: Offloads conversion work from HA instance

## Support

- Issues: https://github.com/iamjoshk/PixelMagicTool/issues
- Examples: See EXAMPLES.md
- Documentation: See README.md and DOCS.md

---

**Transformation Complete!** 🎉

Your PixelMagicTool is now a fully-functional Home Assistant integration for converting sensor image URLs to WLED pixel art!
