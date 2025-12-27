![PixelMagicTool](https://github.com/ajotanc/PixelMagicTool/assets/47322034/300b240b-40a3-4a9a-a6f0-925631919d9b)

# Pixel Magic Tool - Home Assistant Integration

[![Home Assistant Integration](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![HACS Compatible](https://img.shields.io/badge/HACS-Compatible-brightgreen.svg)](https://hacs.xyz/)

A Home Assistant custom integration that converts images to WLED JSON format for HUB75 and 2D Matrix LED panels. Perfect for displaying album art, weather icons, or any dynamic images on your LED displays!

## What This Does

This integration provides **Home Assistant services** that can:
- 🔄 Convert images from URLs (including sensor attributes) to WLED format
- 📤 **Send converted images directly to WLED devices using the WLED JSON API** (`/json/state` endpoint)
- 🎨 Work with album art from media players, weather icons, camera snapshots, and more
- 🤖 Be called from automations, scripts, and Node-RED flows
- 💾 Store conversions in a sensor for later reuse

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

Once installed, the integration provides two services and a sensor:

### Services

Both services support **service responses**, allowing you to retrieve the converted WLED JSON directly without storing it in the database:

1. **`pixelmagictool.convert_image`** - Converts an image URL to WLED JSON and returns it as a service response
2. **`pixelmagictool.send_to_wled`** - Converts and sends directly to your WLED device via the **WLED JSON API** (`http://[WLED-IP]/json/state`), also returns the conversion result

### Sensor

The integration creates a sensor `sensor.pixel_magic_tool_last_conversion` that tracks:
- The last converted image URL
- Segment ID, brightness, and dimensions used

**Note:** The WLED JSON is no longer stored in sensor attributes to avoid database performance issues. Use service responses to access the conversion data (see examples below).

**👉 See [WLED_API.md](WLED_API.md) for details on the WLED JSON API integration!**

**👉 See [EXAMPLES.md](EXAMPLES.md) for complete automation examples!**

## Usage Examples

### Example 1: Display Spotify Album Art

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
          chunk_size: 512
```

### Example 4: Weather Icon Display

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

### Example 5: Use Service Response Data

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

### Example 6: Camera Snapshot

```yaml
automation:
  - alias: "Show Camera on LED Display"
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
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/snapshots/front_door.jpg"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
```

## Service Parameters

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
| `use_chunks` | No | false | Split large payloads into multiple smaller requests |
| `chunk_size` | No | 512 | Number of LEDs per chunk when using chunked sending |

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
- `segment_id` - Segment ID used
- `brightness` - Brightness level used
- `dimensions` - Image dimensions (if available)

**Note:** The `wled_json` attribute is no longer stored in the sensor to avoid database performance issues with large payloads. Use service responses to access the converted WLED JSON data.

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
- 🗜️ Compression support to reduce payload size
- 📦 Chunked sending for very large images that exceed WLED's payload limits

## Pattern Types Explained

- **Range**: Most efficient, groups consecutive identical colors `[start, end, color]`
- **Index**: Explicit positioning `[0, color0, 1, color1, ...]`  
- **Individual**: Simple list of colors `[color0, color1, color2, ...]`

For HUB75 panels, **Range** pattern typically provides the best balance of size and compatibility.

## Tips for Best Results

- **Image URLs**: Use full URLs or Home Assistant local URLs (`http://homeassistant.local:8123/...`)
- **Jinja2 Templates**: The `image_url` parameter supports Jinja2 templates (e.g., `{{ state_attr('media_player.spotify', 'entity_picture') }}`)
- **Service Responses**: Use `response_variable` to capture and use the converted WLED JSON in scripts and automations
- **Dimensions**: Match your WLED segment configuration (e.g., 32x32, 64x32)
- **Pattern Selection**: Use "Range" pattern for most efficient data transfer
- **Brightness**: Adjust based on ambient lighting (128 is a good starting point)
- **Transparent Backgrounds**: Specify a color to replace transparency
- **Compression**: Enable compression for large images to reduce payload size. Start with level 5 and adjust as needed.
- **Chunked Sending**: For very large images that still exceed WLED's limits even with compression, enable `use_chunks: true` to split the payload into multiple smaller requests sent sequentially.
- **Payload Size Limits**: WLED devices typically have a limit of ~20-30KB for JSON payloads. If you get "Payload too large" errors:
  - Enable chunked sending with `use_chunks: true` (recommended for payloads > 15KB)
  - Enable compression with `compression: true` and adjust `compression_level` (1-10)
  - Adjust `chunk_size` (default 512 LEDs) - smaller values = more requests but better compatibility
  - Reduce image dimensions (e.g., use 16x16 or 24x24 instead of 32x32)
  - Try the "range" pattern type (most efficient)
  - Use the `convert_image` service to get the JSON, then use alternative upload methods if needed

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
  - **Adjust chunk size**: Lower `chunk_size` value (default 512) if chunks are still too large
  - Reduce image dimensions (try 16x16 or 24x24)
  - Use the "range" pattern type (most efficient)
  - Combine multiple approaches (compression + chunking) for best results

### Image Not Displaying Correctly on WLED

- Check segment configuration in WLED matches width/height parameters
- Try different pattern types (range, index, individual)
- Verify your WLED version supports JSON state API
- For HUB75 panels, ensure 2D configuration is set up correctly in WLED

### Sensor Not Updating

- Check that the service call completed successfully in Home Assistant logs
- The sensor updates via events - if the conversion fails, the sensor won't update
- Verify the integration is properly set up in Settings → Devices & Services

## Requirements

- Home Assistant 2023.3.0 or newer
- WLED device with 2D Matrix or HUB75 configuration
- Network access to both your WLED device and pixelmagictool.vercel.app
- For media player integration: Media player that provides `entity_picture` attribute

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
