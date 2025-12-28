![PixelMagicTool](https://github.com/ajotanc/PixelMagicTool/assets/47322034/300b240b-40a3-4a9a-a6f0-925631919d9b)

# Pixel Magic Tool - Home Assistant Integration

[![Home Assistant Integration](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![HACS Compatible](https://img.shields.io/badge/HACS-Compatible-brightgreen.svg)](https://hacs.xyz/)

A Home Assistant custom integration that sends images to WLED devices for HUB75 and 2D Matrix LED panels. Perfect for displaying album art, weather icons, or any dynamic images on your LED displays!

## What This Does

This integration provides **Home Assistant services** that can:
- 🔄 Convert images from URLs (including sensor attributes) to WLED format
- 📤 **Send images directly to WLED devices using DDP protocol or WLED JSON API**
- ⚡ **DDP protocol support for better performance and reliability** (recommended)
- ✅ **Automatically ensures device updates** (not just preview) by setting correct WLED parameters
- 🎨 Work with album art from media players, weather icons, camera snapshots, and more
- 🤖 Be called from automations, scripts, and Node-RED flows
- 💾 Store conversions in a sensor for later reuse

## Communication Protocols

The integration supports two protocols for sending images to WLED:

### DDP Protocol (Recommended) 🚀

**NEW!** DDP (Distributed Display Protocol) is now supported and is the **recommended method** for sending images to WLED. Used by tools like [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync), DDP provides:

- ⚡ **Better performance** - Direct UDP streaming, no HTTP overhead
- 🎯 **More reliable** - Purpose-built for LED pixel streaming
- 📦 **Simpler payloads** - Raw RGB24 data, no JSON parsing required
- 🔄 **Real-time streaming** - Ideal for live updates and animations
- 💪 **Better for large matrices** - Handles larger displays more efficiently

**Use the `send_to_wled_ddp` service for DDP protocol.**

### JSON API Protocol

The traditional WLED JSON API (`/json/state` endpoint) is still supported:

- 🔄 Uses the Pixel Magic Tool API for conversion
- 📤 Sends JSON payloads to WLED
- 🗜️ Supports compression and chunking for large images
- 📋 More configuration options (patterns, segments, etc.)

**Use the `send_to_wled` service for JSON API protocol.**

## Use Cases

- **Media Display**: Show album art from Spotify/Plex on your LED matrix
- **Weather Icons**: Display current weather conditions as pixel art
- **Notifications**: Show status icons for doorbell, alarm, etc.
- **Dynamic Art**: Display images from sensors or external APIs
- **Camera Feeds**: Convert camera snapshots to LED display

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/iamjoshk/PixelMagicTool`
6. Select category: "Integration"
7. Click "Add"
8. Find "Pixel Magic Tool" in the integration list
9. Click "Download"
10. Restart Home Assistant
11. Go to Settings → Devices & Services
12. Click "+ Add Integration"
13. Search for "Pixel Magic Tool" and add it

### Manual Installation

1. Copy the `custom_components/pixelmagictool` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services
4. Click "+ Add Integration"
5. Search for "Pixel Magic Tool" and add it

## Quick Start

Once installed, the integration provides three services and a sensor:

### Services

1. **`pixelmagictool.send_to_wled_ddp`** - ⚡ **Recommended**: Send images via DDP protocol for best performance
2. **`pixelmagictool.send_to_wled`** - Send images via WLED JSON API (traditional method)
3. **`pixelmagictool.convert_image`** - Convert image to WLED JSON format only (no sending)

### Sensor

The integration creates a sensor `sensor.pixel_magic_tool_last_conversion` that tracks:
- The last converted image URL
- The WLED JSON from the last conversion (stored in `wled_json` attribute)
- Segment ID, brightness, and dimensions used

**Note:** For very large images, the WLED JSON attribute may increase database size. Consider using compression or smaller image dimensions if database performance becomes a concern. Service responses are also available for accessing conversion data without storing it.

**👉 See [WLED_API.md](WLED_API.md) for details on the WLED JSON API integration!**

**👉 See [WLED_MM.md](WLED_MM.md) for WLED-MM (MoonModules) compatibility guide!**

**👉 See [EXAMPLES.md](EXAMPLES.md) for complete automation examples!**

**👉 See [JSON_FORMAT.md](JSON_FORMAT.md) for JSON format specifications and validation!**

## Usage Examples

### Example 1: Display Spotify Album Art (DDP - Recommended)

```yaml
automation:
  - alias: "Update WLED with Album Art via DDP"
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
          brightness: 255
```

### Example 2: Display Spotify Album Art (JSON API)

```yaml
automation:
  - alias: "Update WLED with Album Art"
    trigger:
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
          brightness: 128
          pattern: "range"
          segment_id: 0
```

### Example 2: Display with Compression (for larger images)

```yaml
automation:
  - alias: "Update WLED with Album Art (Compressed)"
    trigger:
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
          brightness: 128
          pattern: "range"
          segment_id: 0
          compression: true
          compression_level: 5
```

### Example 3: Large Images with Chunked Sending

For very large images (e.g., 64x64 or larger), use chunked sending to split the payload:

```yaml
automation:
  - alias: "Update WLED with Large Album Art"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 64
          height: 64
          brightness: 128
          pattern: "range"
          segment_id: 0
          compression: true
          compression_level: 7
          use_chunks: true
          chunk_size: 128  # Conservative size for WLED-MM (use 256 for standard WLED)
          chunk_delay: 0.15  # Delay between chunks (increase for WLED-MM if needed)
```

### Example 4: Minimal Payload with Colors Only

For applications where you want the smallest possible payload, use the `colors_only` parameter:

```yaml
automation:
  - alias: "Update WLED with Album Art (Minimal Payload)"
    trigger:
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
          brightness: 128
          pattern: "range"
          segment_id: 0
          colors_only: true  # Reduces payload size by removing metadata
```

**Note**: The `colors_only` parameter sends only the essential color data (`seg.i` and `seg.id`), reducing payload size by approximately 40-60 bytes. This is useful when every byte counts, though it omits some WLED parameters like `fx`, `sel`, `on`, `bri`, and `live`. WLED will use default or existing values for these fields.

### Example 5: Weather Icon Display

```yaml
automation:
  - alias: "Show Weather on LED Matrix"
    trigger:
      - platform: state
        entity_id: weather.home
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "https://example.com/weather/{{ states('weather.home') }}.png"
          wled_host: "192.168.1.100"
          width: 16
          height: 16
          brightness: 200
```

### Example 6: Use Service Response Data

Services now return the converted WLED JSON as a response, which you can use in scripts:

```yaml
script:
  convert_and_store:
    sequence:
      - service: pixelmagictool.convert_image
        data:
          image_url: "{{ state_attr('sensor.doorbell_snapshot', 'url') }}"
          width: 64
          height: 64
          brightness: 255
          segment_id: 1
        response_variable: conversion_result
      
      # Use the response data
      - service: rest_command.send_to_wled
        data:
          wled_host: "192.168.1.100"
          payload: "{{ conversion_result.wled_json }}"
```

Or use it in automations:

```yaml
automation:
  - alias: "Convert and Use Response"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.convert_image
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          width: 32
          height: 32
        response_variable: result
      
      - service: notify.persistent_notification
        data:
          message: "Converted image with {{ result.wled_json.seg.i | length }} color values"
```

### Example 7: Camera Snapshot (DDP)

```yaml
automation:
  - alias: "Show Camera on LED Display via DDP"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      - service: camera.snapshot
        target:
          entity_id: camera.front_door
        data:
          filename: /config/www/snapshots/front_door.jpg
      - delay: 1
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "http://homeassistant.local:8123/local/snapshots/front_door.jpg"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
          brightness: 255
```

## Service Parameters

### `pixelmagictool.send_to_wled_ddp` (Recommended)

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `image_url` | Yes | - | URL of image (supports Jinja2 templates) |
| `wled_host` | Yes | - | IP address or hostname of WLED device |
| `width` | Yes | - | Target width in pixels |
| `height` | Yes | - | Target height in pixels |
| `brightness` | No | 255 | LED brightness multiplier (0-255) |
| `timeout` | No | 10 | Request timeout in seconds |

**Service Response:**
Returns a dictionary containing:
- `success` - Boolean indicating if the send was successful
- `image_url` - The processed image URL
- `wled_host` - The WLED device host
- `protocol` - Protocol used ("ddp")
- `width` - Image width
- `height` - Image height
- `brightness` - Brightness level used

**Benefits of DDP:**
- ⚡ Faster than JSON API - direct UDP streaming
- 🎯 More reliable - no HTTP overhead
- 💪 Better for real-time updates
- 📦 Handles large matrices efficiently
- 🔄 No payload size limits like JSON API

### `pixelmagictool.convert_image`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `image_url` | Yes | - | URL of image (supports Jinja2 templates) |
| `width` | No | API default (16) | Target width in pixels |
| `height` | No | API default (16) | Target height in pixels |
| `brightness` | No | 128 | LED brightness (0-255) |
| `pattern` | No | `range` | Pattern type: `individual`, `index`, or `range` |
| `segment_id` | No | 0 | WLED segment ID |
| `transparent_color` | No | - | Hex color for transparent pixels |
| `api_url` | No | pixelmagictool.vercel.app | API endpoint |
| `compression` | No | false | Enable compression to reduce payload size |
| `compression_level` | No | 5 | Compression strength (1-10, 1=gentlest, 10=most aggressive) |

**Service Response:**
Returns a dictionary containing:
- `image_url` - The processed image URL
- `wled_json` - The complete WLED JSON payload
- `segment_id` - Segment ID used
- `brightness` - Brightness level used
- `pattern` - Pattern type used

### `pixelmagictool.send_to_wled`

Same as `convert_image` plus:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `wled_host` | Yes | - | IP address or hostname of WLED device |
| `timeout` | No | 10 | Request timeout in seconds |
| `use_chunks` | No | false | Split large payloads into multiple sequential requests |
| `chunk_size` | No | 128 | Number of LEDs per chunk (128 for WLED-MM, standard WLED can use 256) |
| `chunk_delay` | No | 0.15 | Delay in seconds between chunks (0.15s for stability, increase for WLED-MM) |
| `colors_only` | No | false | Send minimal payload with only color data (reduces size by ~40-60 bytes) |

**Service Response:**
Returns a dictionary containing:
- `success` - Boolean indicating if the send was successful
- `image_url` - The processed image URL
- `wled_host` - The WLED device host
- `wled_json` - The complete WLED JSON payload
- `segment_id` - Segment ID used
- `brightness` - Brightness level used
- `pattern` - Pattern type used

## Sensor Attributes

The `sensor.pixel_magic_tool_last_conversion` entity provides these attributes:

- `last_image_url` - The URL of the last converted image
- `wled_json` - The complete WLED JSON payload from the last conversion
- `segment_id` - Segment ID used
- `brightness` - Brightness level used
- `dimensions` - Image dimensions (if available)

**Note:** For very large images, the `wled_json` attribute may increase database size. Consider using compression, smaller image dimensions, or service responses if database performance becomes a concern.

## Features

- 🎨 Converts any type of image to WLED JSON format using the Pixel Magic Tool API
- 📋 Automatic conversion triggered by sensor state changes
- 🎭 Pattern selection (Individual, Index, Range)
- 💡 Adjustable brightness control
- 📐 Image resizing capabilities
- 🌈 Convert transparent pixels to chosen color
- 📊 Sensor that stores the last conversion for reuse
- 🔗 Works with any image URL including Home Assistant sensor attributes
- 🤖 Perfect for automations with media players, weather, cameras, and more
- 💾 Can convert-only or convert-and-send in one action
- ⚡ **DDP protocol support for better performance** (NEW!)
- 🗜️ Compression support to reduce payload size (JSON API)
- 📦 Chunked sending for very large images that exceed WLED's payload limits (JSON API)
- 🎯 Colors-only mode for minimal payload size (JSON API)

## When to Use DDP vs JSON API

### Use DDP Protocol (Recommended) ⚡

The `send_to_wled_ddp` service is **recommended** for most use cases:

- ✅ **Real-time image updates** - album art, camera feeds, live content
- ✅ **Large LED matrices** - 64x64 and larger
- ✅ **Best performance** - fastest and most reliable
- ✅ **Simple setup** - just specify image URL, host, width, and height
- ✅ **No payload size limits** - handles any matrix size
- ✅ **Based on WLEDVideoSync** - proven approach for image casting

### Use JSON API

The `send_to_wled` service is best for:

- 📋 **Advanced WLED features** - custom patterns, segments, effects
- 🔄 **Need WLED JSON format** - for debugging or custom integrations
- 📊 **Storing conversions** - want JSON in sensor attributes
- 🎨 **Fine-grained control** - compression levels, chunking options

**Note:** For most users, especially those experiencing issues with JSON API payloads, **switch to DDP protocol** (`send_to_wled_ddp`) for better results.

## Pattern Types Explained (JSON API Only)

- **Range**: Most efficient, groups consecutive identical colors `[start, end, color]`
- **Index**: Explicit positioning `[0, color0, 1, color1, ...]`  
- **Individual**: Simple list of colors `[color0, color1, color2, ...]`

For HUB75 panels, **Range** pattern typically provides the best balance of size and compatibility.

## Tips for Best Results

### DDP Protocol Tips

- **Image URLs**: Use full URLs or Home Assistant local URLs (`http://homeassistant.local:8123/...`)
- **Jinja2 Templates**: The `image_url` parameter supports Jinja2 templates (e.g., `{{ state_attr('media_player.spotify', 'entity_picture') }}`)
- **Dimensions**: Must specify exact width and height matching your WLED matrix configuration
- **Brightness**: Set to 255 for maximum brightness, lower values will dim the image
- **Performance**: DDP automatically handles packet fragmentation for large matrices
- **Network**: WLED listens on UDP port 4048 - ensure your firewall allows this

### JSON API Tips

- **Image URLs**: Use full URLs or Home Assistant local URLs (`http://homeassistant.local:8123/...`)
- **Jinja2 Templates**: The `image_url` parameter supports Jinja2 templates (e.g., `{{ state_attr('media_player.spotify', 'entity_picture') }}`)
- **Service Responses**: Use `response_variable` to capture and use the converted WLED JSON in scripts and automations
- **Dimensions**: Match your WLED segment configuration (e.g., 32x32, 64x32)
- **Pattern Selection**: Use "Range" pattern for most efficient data transfer
- **Brightness**: Adjust based on ambient lighting (128 is a good starting point)
- **Transparent Backgrounds**: Specify a color to replace transparency
- **Compression**: Enable compression for large images to reduce payload size. Start with level 5 and adjust as needed.
- **Colors-Only Mode**: Enable `colors_only: true` to send minimal payloads with just the color data, reducing overhead by ~40-60 bytes. This is useful when every byte counts, though it omits some WLED parameters (fx, sel, on, bri, live) and WLED will use default or existing values for these fields.
- **Chunked Sending**: For very large images that still exceed WLED's limits even with compression, enable `use_chunks: true` to split the payload into multiple smaller requests sent sequentially. Default chunk size is 128 LEDs for WLED-MM compatibility (standard WLED can use up to 256).
- **WLED-MM Devices**: If using WLED-MM (MoonModules), use smaller chunks (128 or 64) and longer delays (0.2s or more) due to limited ESP32 RAM. See troubleshooting section for details.
- **Payload Size Limits**: WLED devices typically have a limit of ~20-30KB for JSON payloads. WLED-MM devices may have tighter limits due to limited RAM on ESP32. If you get "Payload too large" errors:
  - **Best solution**: Switch to DDP protocol with `send_to_wled_ddp` service
  - Enable colors-only mode with `colors_only: true` (saves ~40-60 bytes overhead)
  - Enable chunked sending with `use_chunks: true` (recommended for payloads > 15KB)
  - Enable compression with `compression: true` and adjust `compression_level` (1-10)
  - Adjust `chunk_size` (default 128 for WLED-MM, 256 for standard WLED) - smaller values = more requests but better compatibility
  - Adjust `chunk_delay` (default 0.15s, increase to 0.2-0.5s for WLED-MM stability)
  - Reduce image dimensions (e.g., use 16x16 or 24x24 instead of 32x32)
  - Try the "range" pattern type (most efficient)

## Advanced Usage

### Using Service Responses

The modern way to use the conversion data is via service responses:

```yaml
script:
  convert_and_use:
    sequence:
      - service: pixelmagictool.convert_image
        data:
          image_url: "https://example.com/image.png"
          width: 32
          height: 32
        response_variable: result
      
      # Now use result.wled_json in subsequent steps
      - service: rest_command.custom_wled_send
        data:
          payload: "{{ result.wled_json }}"
```

### Using with Node-RED

You can call the services from Node-RED:

```json
{
    "domain": "pixelmagictool",
    "service": "send_to_wled",
    "data": {
        "image_url": "{{payload.image_url}}",
        "wled_host": "192.168.1.100",
        "width": 32,
        "height": 32
    }
}
```

### Using Sensor Data in REST Commands

Define a REST command to send stored conversions:

```yaml
rest_command:
  send_wled_json:
    url: "http://{{ wled_host }}/json/state"
    method: POST
    content_type: "application/json"
    payload: "{{ wled_json }}"
```

Then call it:

```yaml
service: rest_command.send_wled_json
data:
  wled_host: "192.168.1.100"
  wled_json: "{{ state_attr('sensor.pixel_magic_tool_last_conversion', 'wled_json') }}"
```

## Configuration

The integration has minimal configuration. After adding it through the UI, it will:
- Create a sensor entity for storing conversions
- Register two services for converting and sending images
- Be ready to use in your automations

See [DOCS.md](DOCS.md) for more detailed documentation about the web interface (available at `pxmagic.htm` and `inpxmagic.htm`).

## Troubleshooting

### Integration Not Loading

1. Check Home Assistant logs: Settings → System → Logs
2. Verify the `custom_components/pixelmagictool` directory is in the correct location
3. Restart Home Assistant after installation
4. Ensure you have an active internet connection (for API access)

### Service Call Fails

- **"Image download failed"**: Check that the image URL is accessible from your Home Assistant instance
- **"API error"**: The Pixel Magic Tool API at pixelmagictool.vercel.app may be unavailable
- **"WLED connection failed"**: Verify WLED device IP/hostname and network connectivity
- **"Payload too large" or "413 Request Entity Too Large"**: The converted WLED JSON exceeds WLED's size limit (~20-30KB). Solutions:
  - **Enable chunked sending**: Set `use_chunks: true` (recommended for large images)
  - **Enable compression**: Set `compression: true` and adjust `compression_level`
  - **Adjust chunk size**: Lower `chunk_size` value (default 256 per WLED recommendation) if chunks are still too large
  - Reduce image dimensions (try 16x16 or 24x24)
  - Use the "range" pattern type (most efficient)
  - Combine multiple approaches (compression + chunking) for best results

### Image Not Displaying Correctly on WLED

- Check segment configuration in WLED matches width/height parameters
- Try different pattern types (range, index, individual)
- Verify your WLED version supports JSON state API
- For HUB75 panels, ensure 2D configuration is set up correctly in WLED
- **For WLED-MM (MoonModules) devices**: See special considerations below

### WLED-MM (MoonModules) Compatibility

If you're running **WLED-MM** (MoonModules fork) instead of stable WLED, you may encounter loading or freezing issues due to limited RAM on ESP32 devices. WLED-MM has the same JSON API but stricter memory constraints.

**Solutions for WLED-MM devices:**
- **Enable chunked sending**: Set `use_chunks: true` to split payloads into smaller requests
- **Use smaller chunk size**: Set `chunk_size: 128` or even `chunk_size: 64` for very constrained devices (default is 128)
- **Increase chunk delay**: Set `chunk_delay: 0.2` or higher (default is 0.15s) to give the device more time between chunks
- **Enable compression**: Set `compression: true` to reduce payload size before chunking
- **Use colors-only mode**: Set `colors_only: true` to minimize overhead
- **Reduce image dimensions**: Use smaller images (16x16 or 24x24 instead of 32x32)
- **Use range pattern**: The "range" pattern is most memory-efficient

**Example for WLED-MM devices:**
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
  use_chunks: true
  chunk_size: 128        # Smaller chunks for WLED-MM
  chunk_delay: 0.2       # Longer delay for stability
  compression: true      # Enable compression
  compression_level: 5
  colors_only: true      # Minimal payload
```

### Sensor Not Updating

- Check that the service call completed successfully in Home Assistant logs
- The sensor updates via events - if the conversion fails, the sensor won't update
- Verify the integration is properly set up in Settings → Devices & Services

## Requirements

- Home Assistant 2023.3.0 or newer
- WLED device with 2D Matrix or HUB75 configuration (supports both stable WLED and WLED-MM/MoonModules)
- Network access to both your WLED device and pixelmagictool.vercel.app
- For media player integration: Media player that provides `entity_picture` attribute

**Note**: This integration is compatible with both stable WLED and WLED-MM (MoonModules fork). For WLED-MM devices, use the chunked sending options with smaller chunk sizes and longer delays for best results.

## Credits & Acknowledgments

- Original Pixel Magic Tool web interface and API by [@ajotanc](https://github.com/ajotanc)
- Apollo Automation's maintained fork: [@ApolloAutomation/PixelMagicTool](https://github.com/ApolloAutomation/PixelMagicTool)
- Home Assistant custom integration and HACS packaging
- WLED project by [@Aircoookie](https://github.com/Aircoookie/WLED)

**Note**: The Home Assistant add-on automatically fetches the latest version of the Pixel Magic Tool web interface from [Apollo Automation's repository](https://github.com/ApolloAutomation/PixelMagicTool) at build time, ensuring you always have the most recent version.

## Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/iamjoshk/PixelMagicTool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iamjoshk/PixelMagicTool/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

Pull requests are welcome! Please feel free to contribute improvements.

## License

See [LICENSE](LICENSE) file for details.

---

## Standalone Web Interface

The repository also includes standalone HTML tools that can be used independently. These are maintained by Apollo Automation:

### Interface Version (`pxmagic.htm`)
- Full-featured web interface with preview and simulation
- Can be saved locally or uploaded to WLED's filesystem
- Access at `http://[WLED-IP]/pxmagic.htm` if uploaded to WLED

[Download Interface Version](https://raw.githubusercontent.com/ApolloAutomation/PixelMagicTool/main/pxmagic.htm)

### Inline Version (`inpxmagic.htm`)
- URL parameter-based conversion
- Useful for direct links and automation scripts

[Download Inline Version](https://raw.githubusercontent.com/ApolloAutomation/PixelMagicTool/main/inpxmagic.htm)

### Direct API Usage

You can also use the Pixel Magic Tool API directly:

```bash
# Convert local image
curl -X POST -F "file=@image.png" \
  "https://pixelmagictool.vercel.app/api/wled/image?id=0&output=json&brightness=255&pattern=range&width=32&height=32"

# Convert from URL
curl -X POST -F "file=@-;filename=image.png" \
  "https://pixelmagictool.vercel.app/api/wled/image?id=0&output=json&brightness=255&pattern=range" \
  < <(curl -s "https://example.com/image.png")
```

See the API documentation in the original repository for full parameter details.

---

**Enjoying this integration? Give it a ⭐ on [GitHub](https://github.com/iamjoshk/PixelMagicTool)!**

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
