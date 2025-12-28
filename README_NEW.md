# WLEDVideoSync - Home Assistant Integration

[![Home Assistant Integration](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![HACS Compatible](https://img.shields.io/badge/HACS-Compatible-brightgreen.svg)](https://hacs.xyz/)

A Home Assistant custom integration for sending images to WLED devices via DDP (Distributed Display Protocol). Perfect for displaying album art, camera snapshots, or any dynamic images on LED matrices like the Apollo M-1 running MM-WLED.

> **Note**: This is a **service-only integration** - it does not create entities. You interact with it through service calls. See [Troubleshooting](TROUBLESHOOTING.md) for more information.

## What This Does

This integration provides a **simple and reliable service** to send images directly to WLED devices using the DDP protocol - the same method used by [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync).

### Key Features

- ⚡ **Fast & Reliable** - Direct UDP streaming via DDP protocol
- 🎯 **No Size Limits** - Automatic packet fragmentation for any matrix size
- 🖼️ **Flexible Input** - Supports both URLs and local file paths
- 💡 **Brightness Control** - Adjustable LED brightness (0-255)
- 🎨 **Works with Apollo M-1** - Tested with MM-WLED firmware
- 🔄 **Real-time Updates** - Perfect for album art, camera feeds, weather icons

## Why DDP?

DDP (Distributed Display Protocol) is specifically designed for LED pixel streaming:
- **Better Performance** - Direct UDP, no HTTP overhead
- **More Reliable** - Purpose-built for LED displays
- **Simpler** - Raw RGB24 data, no complex payloads
- **Universal** - Works with standard WLED and WLED-MM

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/iamjoshk/PixelMagicTool`
6. Select category: "Integration"
7. Click "Add"
8. Find "WLEDVideoSync" in the integration list
9. Click "Download"
10. Restart Home Assistant
11. Go to Settings → Devices & Services
12. Click "+ Add Integration"
13. Search for "WLEDVideoSync" and add it

### Manual Installation

1. Copy the `custom_components/pixelmagictool` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services
4. Click "+ Add Integration"
5. Search for "WLEDVideoSync" and add it

## Quick Start

Once installed, use the `pixelmagictool.send_to_wled_ddp` service to send images:

### Example 1: Display Album Art

```yaml
automation:
  - alias: "Update LED Matrix with Album Art"
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

### Example 2: Camera Snapshot

```yaml
automation:
  - alias: "Show Doorbell Camera on LED Matrix"
    trigger:
      - platform: state
        entity_id: binary_sensor.doorbell
        to: "on"
    action:
      - service: camera.snapshot
        target:
          entity_id: camera.front_door
        data:
          filename: /config/www/snapshots/doorbell.jpg
      - delay: 1
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_path: "/config/www/snapshots/doorbell.jpg"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
          brightness: 200
```

### Example 3: Weather Icon

```yaml
automation:
  - alias: "Display Weather Icon"
    trigger:
      - platform: state
        entity_id: weather.home
    action:
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "https://example.com/weather/{{ states('weather.home') }}.png"
          wled_host: "192.168.1.100"
          width: 16
          height: 16
          brightness: 255
```

## Service Parameters

### `pixelmagictool.send_to_wled_ddp`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `image_url` | One of url/path | - | URL of image (supports Jinja2 templates) |
| `image_path` | One of url/path | - | Local file path (e.g., /config/www/image.png) |
| `wled_host` | Yes | - | IP address or hostname of WLED device |
| `width` | Yes | - | Target width in pixels (must match your matrix) |
| `height` | Yes | - | Target height in pixels (must match your matrix) |
| `brightness` | No | 255 | LED brightness (0-255, 255=full brightness) |
| `timeout` | No | 10 | Request timeout in seconds |

**Note**: Provide either `image_url` OR `image_path`, not both.

### Service Response

The service returns:
- `success`: Boolean indicating if the send was successful
- `image_source`: The image URL or path used
- `source_type`: Either "url" or "path"
- `wled_host`: The WLED device host
- `protocol`: Always "ddp"
- `width`: Image width used
- `height`: Image height used
- `brightness`: Brightness level applied

## Use Cases

- **Media Display**: Album art from Spotify/Plex on your LED matrix
- **Security**: Camera snapshots on doorbell/motion events
- **Weather**: Current weather conditions as pixel art
- **Notifications**: Status icons for various home events
- **Dynamic Art**: Images from sensors or external APIs

## Requirements

- Home Assistant 2023.3.0 or newer
- WLED device with 2D Matrix configuration
  - Standard WLED firmware, or
  - WLED-MM (MoonModules) firmware
  - Apollo M-1 LED Matrix with MM-WLED (tested ✓)
- Network access between Home Assistant and WLED device
- UDP port 4048 accessible on WLED device (DDP default port)

## Troubleshooting

### Image Not Displaying

1. **Check network connectivity**
   ```bash
   ping <wled-ip>
   nc -zvu <wled-ip> 4048
   ```

2. **Verify matrix dimensions**
   - Width and height must match your WLED configuration
   - Check WLED → Settings → LED Preferences → 2D Configuration

3. **Test with simple image**
   - Use a solid color first: `https://via.placeholder.com/32x32/FF0000/FF0000.png`

4. **Check WLED logs**
   - Look for DDP packets being received on port 4048

### Display Resets to Solid Color

This issue has been fixed in version 2.0.0+. The integration now sends DDP packets directly without HTTP API preparation, matching WLEDVideoSync web UI behavior.

### No Entities Created / No Debug Logging

This is normal - the integration is service-only and doesn't create entities. For detailed troubleshooting including how to enable debug logging, see the **[Troubleshooting Guide](TROUBLESHOOTING.md)**.

### Performance Issues

- Use wired Ethernet instead of WiFi when possible
- Reduce image dimensions if updates are slow
- Lower brightness can improve responsiveness

## Upgrade from v1.x

If you're upgrading from version 1.x (Pixel Magic Tool):

- The old `convert_image` and `send_to_wled` services have been removed
- Use `send_to_wled_ddp` for all image sending
- The sensor entity is no longer created
- See [UPGRADE_TO_V2.md](UPGRADE_TO_V2.md) for details

## Credits & Acknowledgments

- DDP protocol implementation inspired by [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync)
- WLED project by [@Aircoookie](https://github.com/Aircoookie/WLED)
- Apollo Automation for the M-1 LED Matrix hardware
- Original Pixel Magic Tool concept by [@ajotanc](https://github.com/ajotanc)

## Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/iamjoshk/PixelMagicTool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/iamjoshk/PixelMagicTool/discussions)

Pull requests are welcome!

## License

See [LICENSE](LICENSE) file for details.

---

**Enjoying this integration? Give it a ⭐ on [GitHub](https://github.com/iamjoshk/PixelMagicTool)!**
