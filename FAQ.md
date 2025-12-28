# Frequently Asked Questions (FAQ)

## Connection and Network Questions

### Does Home Assistant need to keep a constant connection with WLED to stream images?

**No, Home Assistant does NOT need to maintain a constant connection with WLED.**

PixelMagicTool operates differently from continuous streaming tools like [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync):

#### How PixelMagicTool Works

**One-Shot Image Sending:**
- Each service call sends a single image to WLED
- The connection is established, data is sent, then the connection is closed
- WLED displays the image persistently until you send a new one or change the WLED state
- No continuous connection is required between updates

**Connection Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Service Called (send_to_wled_ddp or send_to_wled)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Connection Established                                    │
│    - DDP: UDP socket opened to port 4048                    │
│    - JSON API: HTTP connection to /json/state              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Image Data Sent                                          │
│    - DDP: RGB pixel data in UDP packets                    │
│    - JSON API: JSON payload via HTTP POST                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Connection Closed                                        │
│    - Socket/HTTP connection is immediately closed           │
│    - Home Assistant is no longer connected to WLED          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. WLED Displays Image                                      │
│    - Image persists on WLED until changed                   │
│    - No connection to Home Assistant needed                 │
└─────────────────────────────────────────────────────────────┘
```

#### Comparison with WLEDVideoSync

| Feature | PixelMagicTool | WLEDVideoSync |
|---------|----------------|---------------|
| **Connection Type** | One-shot per image | Continuous streaming |
| **Use Case** | Static images (album art, icons) | Video/live content |
| **Network Usage** | Minimal - only when sending | Constant during streaming |
| **Home Assistant Required** | Only during send | Required while streaming |
| **WLED State** | Persists after send | Reverts when streaming stops |
| **Best For** | Automations, periodic updates | Real-time video casting |

#### Protocol-Specific Details

**DDP Protocol (Recommended):**
- Opens UDP socket on port 4048
- Sends RGB pixel data directly
- Automatically prepares WLED via quick HTTP call first
- Closes socket immediately after sending
- **Total connection time: < 100ms typically**

**JSON API Protocol:**
- Makes HTTP POST to `/json/state` endpoint
- Sends JSON with pixel color data
- Connection closes after response received
- **Total connection time: < 500ms typically**

#### Network Requirements

**While Sending:**
- Home Assistant must be able to reach WLED's IP address
- DDP: UDP port 4048 must be accessible
- JSON API: HTTP port 80 must be accessible

**After Sending:**
- No network connection needed between Home Assistant and WLED
- WLED displays the image independently
- WLED can even be on a different network after the image is sent

#### Example Automation

This automation only connects to WLED when the album art changes:

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

**What happens:**
1. Spotify album art changes
2. Home Assistant triggers automation
3. Service connects to WLED (~50-100ms)
4. Image data is sent
5. Connection closes
6. Album art displays on LED matrix
7. **No further connection until next update**

### When Would You Need WLEDVideoSync Instead?

Use [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync) if you need:
- **Live video streaming** to LED matrix
- **Screen casting** from computer to WLED
- **Camera feed streaming** (continuous, not snapshots)
- **Real-time animations** generated on PC

Use PixelMagicTool if you need:
- **Static images** triggered by Home Assistant events
- **Album art** from media players
- **Weather icons** or status indicators
- **Camera snapshots** (periodic captures)
- **Home Assistant automation** integration

## Performance Questions

### How fast is image sending?

**DDP Protocol (Recommended):**
- Small images (16x16): ~10-20ms
- Medium images (32x32): ~30-50ms
- Large images (64x64): ~80-120ms
- Very large (128x128): ~300-500ms

**JSON API:**
- Small images (16x16): ~50-100ms
- Medium images (32x32): ~100-200ms
- Large images (64x64): ~500-1000ms
- Very large may fail due to size limits

### Can I send multiple images rapidly?

Yes, but with considerations:

**Recommended Approach:**
```yaml
# Good: Sequential sends with small delay
script:
  slideshow:
    sequence:
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "http://example.com/image1.png"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
      - delay: 
          milliseconds: 500
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "http://example.com/image2.png"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
```

**Things to Avoid:**
- Sending faster than 100ms intervals (WLED processing time)
- Parallel sends to same WLED device (use sequential)
- Updates every few seconds without reason (network overhead)

### What happens if Home Assistant restarts?

**No Problem!**
- Images already sent to WLED persist
- WLED continues displaying the last image
- After Home Assistant restarts, automations work normally
- Next automation trigger will send a new image

### Does WLED need internet access?

**No, WLED does not need internet access to display images.**

Requirements:
- ✅ WLED needs network connection to Home Assistant
- ✅ Home Assistant needs network connection to WLED
- ✅ Home Assistant may need internet to download images (if using external URLs)
- ❌ WLED does NOT need internet access itself

Example scenarios:

**Local Network Only:**
```yaml
# This works without internet
service: pixelmagictool.send_to_wled_ddp
data:
  image_path: "/config/www/local-image.png"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
```

**Internet Required for Home Assistant:**
```yaml
# Home Assistant needs internet to download Spotify image
# But WLED itself doesn't need internet
service: pixelmagictool.send_to_wled_ddp
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
```

## Troubleshooting

### Image doesn't persist after sending

**DDP Protocol:**
The integration automatically prepares WLED to ensure images persist. If you still have issues:

1. Check WLED firmware version (0.14.0+ recommended)
2. Verify segment is configured correctly in WLED
3. Ensure no other automations are changing WLED state
4. Check WLED logs for errors

**JSON API:**
Ensure you're not using `live: true` or `lor: 1` in custom JSON, as these cause temporary display.

### Connection fails intermittently

Common causes:
- **WiFi interference**: Use wired Ethernet for WLED if possible
- **ESP32/8266 stability**: Ensure adequate power supply (5V 2A+)
- **Network congestion**: Reduce other network traffic during sends
- **WLED busy**: Wait longer between updates

Check connectivity:
```bash
# Test basic connectivity
ping 192.168.1.100

# Test DDP port (UDP 4048)
nc -zvu 192.168.1.100 4048

# Test HTTP API
curl http://192.168.1.100/json/state
```

### Home Assistant becomes unresponsive during sending

This should not happen with normal usage. If it does:

**Possible Causes:**
- Very large images (>128x128) with JSON API
- Sending to many WLED devices in parallel
- Network timeout issues

**Solutions:**
1. Switch to DDP protocol: `send_to_wled_ddp`
2. Reduce image dimensions
3. Send to devices sequentially, not in parallel
4. Increase timeout value in service call

## Setup Questions

### Do I need to configure anything on WLED?

**For DDP Protocol:**
- DDP is enabled by default on WLED
- Just ensure your matrix is configured (Settings → LED Preferences → 2D Configuration)
- No special sync settings needed

**For JSON API:**
- No special configuration needed
- JSON API is always available on WLED
- Just ensure HTTP access is enabled (default)

### Can I use both protocols simultaneously?

**Not recommended.** Pick one:

**Use DDP (Recommended):**
- Better performance
- More reliable
- Handles large images
- No payload size limits

**Use JSON API if:**
- You need WLED JSON format for debugging
- You want to store conversions in sensor
- You need advanced WLED features

**Don't mix:**
```yaml
# Bad: Don't do this
- service: pixelmagictool.send_to_wled  # JSON API
  data: {...}
- service: pixelmagictool.send_to_wled_ddp  # DDP
  data: {...}
```

### How do I update multiple WLED devices?

**Sequential (Recommended):**
```yaml
script:
  update_all_displays:
    sequence:
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "{{ image }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
      - service: pixelmagictool.send_to_wled_ddp
        data:
          image_url: "{{ image }}"
          wled_host: "192.168.1.101"
          width: 32
          height: 32
```

**Parallel (Advanced):**
```yaml
script:
  update_all_displays_fast:
    sequence:
      - parallel:
          - service: pixelmagictool.send_to_wled_ddp
            data:
              image_url: "{{ image }}"
              wled_host: "192.168.1.100"
              width: 32
              height: 32
          - service: pixelmagictool.send_to_wled_ddp
            data:
              image_url: "{{ image }}"
              wled_host: "192.168.1.101"
              width: 32
              height: 32
```

## Integration Questions

### Does this work with HACS?

**Yes!** This integration is designed for HACS:

1. Add custom repository: `https://github.com/iamjoshk/PixelMagicTool`
2. Search for "Pixel Magic Tool"
3. Install
4. Restart Home Assistant
5. Add integration via UI

### What Home Assistant version is required?

**Minimum: Home Assistant 2023.3.0**

Features used:
- Modern config flow
- Service response data
- Template rendering
- Async/await patterns

### Does this work with WLED-MM (MoonModules)?

**Yes, with special considerations:**

WLED-MM has more limited RAM, so:
- Use DDP protocol (recommended)
- Or use smaller chunk sizes with JSON API
- See [WLED_MM.md](WLED_MM.md) for details

## Image Handling Questions

### Can I use local file paths?

**Yes!** Use `image_path` instead of `image_url`:

```yaml
service: pixelmagictool.send_to_wled_ddp
data:
  image_path: "/config/www/images/album-art.png"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
```

### What image formats are supported?

**All common formats:**
- PNG (recommended for transparency)
- JPEG/JPG
- GIF (static and animated)
- BMP
- WebP

### How are images resized?

**Automatic resizing** to specified width and height:
- Maintains aspect ratio when possible
- Uses high-quality resampling
- Performed by Pixel Magic Tool API (for JSON API)
- Or by integration directly (for DDP)

### Can I control brightness per image?

**Yes!** Use the `brightness` parameter:

```yaml
service: pixelmagictool.send_to_wled_ddp
data:
  image_url: "https://example.com/bright-image.png"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 128  # 0-255, where 255 is full brightness
```

This multiplies each RGB value by `brightness/255`, effectively dimming the image.

## Advanced Topics

### Can I create animations?

**Yes, but with limitations:**

PixelMagicTool is designed for static images. For animations:

**Simple Animation (Sequential Images):**
```yaml
script:
  simple_animation:
    sequence:
      - repeat:
          count: 10
          sequence:
            - service: pixelmagictool.send_to_wled_ddp
              data:
                image_url: "http://example.com/frame{{ repeat.index }}.png"
                wled_host: "192.168.1.100"
                width: 32
                height: 32
            - delay:
                milliseconds: 100
```

**For Complex Animations:**
Use WLED's built-in effects or consider WLEDVideoSync for real-time video.

### Can I use this with ESPHome?

**Yes, indirectly:**

ESPHome devices can run WLED firmware. Flash WLED onto your ESPHome device, then use PixelMagicTool normally.

Alternatively, if you want to keep ESPHome:
1. Use PixelMagicTool to convert image to RGB data
2. Use service response to get the data
3. Send via ESPHome's native LED component

### How do I debug sending issues?

**Enable Debug Logging:**

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.pixelmagictool: debug
```

This logs:
- Service calls and parameters
- Image download progress
- DDP packet sending details
- WLED API responses
- Error details

**Check Logs:**
1. Settings → System → Logs
2. Look for entries from `custom_components.pixelmagictool`
3. Check for network errors, timeouts, or WLED responses

### Can I integrate with Node-RED?

**Yes!** Use Home Assistant service call nodes:

```json
{
  "domain": "pixelmagictool",
  "service": "send_to_wled_ddp",
  "data": {
    "image_url": "https://example.com/image.png",
    "wled_host": "192.168.1.100",
    "width": 32,
    "height": 32,
    "brightness": 255
  }
}
```

## Contributing

Have more questions? 

- [Open an issue](https://github.com/iamjoshk/PixelMagicTool/issues)
- [Start a discussion](https://github.com/iamjoshk/PixelMagicTool/discussions)
- [Submit a PR](https://github.com/iamjoshk/PixelMagicTool/pulls) to improve this FAQ

## Related Documentation

- [README.md](README.md) - Main documentation
- [DDP_PROTOCOL.md](DDP_PROTOCOL.md) - DDP protocol details
- [WLED_API.md](WLED_API.md) - JSON API details
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [WLED_MM.md](WLED_MM.md) - WLED-MM compatibility
