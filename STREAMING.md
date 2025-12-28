# Continuous Streaming Mode

## Overview

WLEDVideoSync now supports **continuous streaming mode**, inspired by the [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync) tool. This mode maintains a persistent connection to WLED and allows sending multiple frames without reconnecting each time.

## Connection Models

### One-Shot Mode (Default)

The `send_to_wled_ddp` service uses a one-shot connection model:
- Opens connection
- Sends single image
- Closes connection immediately
- Image persists on WLED until changed
- **Best for:** Static images, triggered by automations

### Continuous Streaming Mode (New)

The new streaming services maintain a persistent connection:
- Opens connection once (`start_streaming`)
- Sends multiple frames (`send_frame`)
- Connection stays open between frames
- Closes when done (`stop_streaming`)
- **Best for:** Live content, frequent updates, video-like sequences

## When to Use Streaming Mode

Use **continuous streaming** when:
- ✅ Sending multiple frames in quick succession
- ✅ Creating animations or slideshows
- ✅ Updating display frequently (>1 update per second)
- ✅ Want to minimize connection overhead
- ✅ Need WLEDVideoSync-style streaming behavior

Use **one-shot mode** when:
- ✅ Sending single images occasionally
- ✅ Triggered by automations (album art, weather, etc.)
- ✅ Don't need persistent connection
- ✅ Simple use cases

## Streaming Services

### 1. Start Streaming Session

Opens a persistent DDP connection to WLED:

```yaml
service: pixelmagictool.start_streaming
data:
  session_id: "my_stream"
  wled_host: "192.168.1.100"
  segment_id: 0
  prepare_device: false
```

**Parameters:**
- `session_id` (required): Unique identifier for this session
- `wled_host` (required): WLED device IP address
- `segment_id` (optional): WLED segment ID (default: 0)
- `timeout` (optional): Socket timeout in seconds (default: 10)
- `prepare_device` (optional): Prepare WLED via HTTP API (default: false; matches WLEDVideoSync)

### 2. Send Frame to Session

Sends a frame to an active streaming session:

```yaml
service: pixelmagictool.send_frame
data:
  session_id: "my_stream"
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  width: 32
  height: 32
  brightness: 255
```

**Parameters:**
- `session_id` (required): Session ID from start_streaming
- `image_url` or `image_path` (required): Image source
- `width` (required): Target width in pixels
- `height` (required): Target height in pixels
- `brightness` (optional): Brightness 0-255 (default: 255)

### 3. Stop Streaming Session

Closes the streaming session:

```yaml
service: pixelmagictool.stop_streaming
data:
  session_id: "my_stream"
```

## Usage Examples

### Example 1: Album Art Streaming

Continuous streaming of album art changes:

```yaml
automation:
  - alias: "Start Album Art Streaming"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: pixelmagictool.start_streaming
        data:
          session_id: "spotify_art"
          wled_host: "192.168.1.100"
  
  - alias: "Update Album Art Frame"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_frame
        data:
          session_id: "spotify_art"
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          width: 32
          height: 32
          brightness: 255
```

### Example 2: Image Slideshow

Create a slideshow with multiple images:

```yaml
script:
  led_slideshow:
    sequence:
      # Start streaming session
      - service: pixelmagictool.start_streaming
        data:
          session_id: "slideshow"
          wled_host: "192.168.1.100"
      
      # Send first frame
      - service: pixelmagictool.send_frame
        data:
          session_id: "slideshow"
          image_path: "/config/www/image1.jpg"
          width: 32
          height: 32
      - delay: 2
      
      # Send second frame
      - service: pixelmagictool.send_frame
        data:
          session_id: "slideshow"
          image_path: "/config/www/image2.jpg"
          width: 32
          height: 32
      - delay: 2
      
      # Send third frame
      - service: pixelmagictool.send_frame
        data:
          session_id: "slideshow"
          image_path: "/config/www/image3.jpg"
          width: 32
          height: 32
      - delay: 2
      
      # Stop streaming
      - service: pixelmagictool.stop_streaming
        data:
          session_id: "slideshow"
```

### Example 3: Weather Animation

Stream weather updates every minute:

```yaml
automation:
  - alias: "Start Weather Streaming"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: pixelmagictool.start_streaming
        data:
          session_id: "weather"
          wled_host: "192.168.1.100"
  
  - alias: "Update Weather Frame"
    trigger:
      - platform: time_pattern
        minutes: "/1"  # Every minute
    action:
      - service: pixelmagictool.send_frame
        data:
          session_id: "weather"
          image_url: "https://example.com/weather/{{ states('weather.home') }}.png"
          width: 16
          height: 16
          brightness: 200
```

### Example 4: Camera Stream

Stream camera snapshots every few seconds:

```yaml
automation:
  - alias: "Start Camera Stream"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      # Start streaming
      - service: pixelmagictool.start_streaming
        data:
          session_id: "camera_feed"
          wled_host: "192.168.1.100"
      
      # Send frames in a loop
      - repeat:
          count: 30  # 30 frames
          sequence:
            - service: camera.snapshot
              target:
                entity_id: camera.front_door
              data:
                filename: /config/www/snapshots/camera.jpg
            - delay: 0.1
            - service: pixelmagictool.send_frame
              data:
                session_id: "camera_feed"
                image_path: "/config/www/snapshots/camera.jpg"
                width: 32
                height: 32
            - delay: 0.5  # 2 FPS
      
      # Stop streaming
      - service: pixelmagictool.stop_streaming
        data:
          session_id: "camera_feed"
```

### Example 5: On-Demand Streaming Control

Manual control of streaming sessions:

```yaml
script:
  start_led_stream:
    sequence:
      - service: pixelmagictool.start_streaming
        data:
          session_id: "{{ session_name }}"
          wled_host: "{{ wled_ip }}"
  
  send_led_frame:
    sequence:
      - service: pixelmagictool.send_frame
        data:
          session_id: "{{ session_name }}"
          image_url: "{{ image }}"
          width: 32
          height: 32
  
  stop_led_stream:
    sequence:
      - service: pixelmagictool.stop_streaming
        data:
          session_id: "{{ session_name }}"
```

## Best Practices

### Session Management

1. **Unique Session IDs**: Use descriptive, unique IDs for each stream
2. **Cleanup**: Always call `stop_streaming` when done
3. **Error Handling**: Handle connection failures gracefully
4. **Resource Limits**: Don't create too many concurrent sessions

### Performance

1. **Frame Rate**: Keep frame rate reasonable (1-10 FPS typically)
2. **Image Size**: Match your WLED matrix dimensions exactly
3. **Brightness**: Adjust for optimal display and power usage
4. **Network**: Use wired Ethernet for best streaming performance

### Automation Patterns

**Start on Home Assistant Start:**
```yaml
automation:
  - alias: "Initialize Streams"
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: pixelmagictool.start_streaming
        data:
          session_id: "main_display"
          wled_host: "192.168.1.100"
```

**Stop on Home Assistant Stop:**
```yaml
automation:
  - alias: "Cleanup Streams"
    trigger:
      - platform: homeassistant
        event: shutdown
    action:
      - service: pixelmagictool.stop_streaming
        data:
          session_id: "main_display"
```

## Troubleshooting

### Session Not Found Error

**Problem**: `send_frame` returns "Streaming session not found"

**Solutions:**
- Ensure `start_streaming` was called first
- Check session_id matches exactly
- Verify session didn't time out or disconnect

### Connection Issues

**Problem**: Frames not displaying or connection errors

**Solutions:**
- Check WLED device is reachable
- Verify UDP port 4048 is accessible
- Ensure no firewall blocking
- Try increasing timeout value
- Check WLED logs for errors

### High CPU/Memory Usage

**Problem**: Resource usage is high

**Solutions:**
- Reduce frame rate
- Decrease image dimensions
- Limit concurrent sessions
- Ensure sessions are properly stopped

### Frames Out of Order

**Problem**: Images appearing in wrong sequence

**Solutions:**
- Add delays between frames
- Don't send frames in parallel
- Check network stability

## Technical Details

### Connection Lifecycle

1. **start_streaming**: Opens UDP socket, keeps it open
2. **send_frame**: Sends DDP packets through open socket
3. **stop_streaming**: Closes UDP socket, cleans up

### Socket Management

- One UDP socket per session
- Socket remains open until stopped
- Sequence numbers track frame order
- Thread-safe with asyncio locks

### Memory and Resources

- Each session maintains one socket
- Frame data is processed on-demand
- No frame buffering (streaming model)
- Sessions cleaned up on integration unload

## Comparison with One-Shot Mode

| Feature | One-Shot (`send_to_wled_ddp`) | Streaming (`start/send/stop`) |
|---------|-------------------------------|-------------------------------|
| Connection | Opens/closes each time | Stays open |
| Overhead | Higher per image | Lower per frame |
| Use Case | Single images | Multiple frames |
| Setup | Simple, one call | Three-step process |
| Performance | Good for occasional | Better for frequent |
| Resource Usage | Minimal | One socket per session |

## Examples in Node-RED

### Start Streaming
```json
{
  "service": "pixelmagictool.start_streaming",
  "data": {
    "session_id": "nodered_stream",
    "wled_host": "192.168.1.100"
  }
}
```

### Send Frame
```json
{
  "service": "pixelmagictool.send_frame",
  "data": {
    "session_id": "nodered_stream",
    "image_url": "{{payload.image_url}}",
    "width": 32,
    "height": 32
  }
}
```

### Stop Streaming
```json
{
  "service": "pixelmagictool.stop_streaming",
  "data": {
    "session_id": "nodered_stream"
  }
}
```

## See Also

- [README.md](README.md) - Main documentation
- [DDP_PROTOCOL.md](DDP_PROTOCOL.md) - DDP protocol details
- [FAQ.md](FAQ.md) - Frequently asked questions
- [WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync) - Inspiration for streaming mode
