# Troubleshooting Guide

## Common Issues and Solutions

### No Entities Created

**Question**: Why don't I see any entities in Home Assistant after installing the integration?

**Answer**: This is normal and expected. The WLEDVideoSync (PixelMagicTool) integration is a **service-only integration**. It does not create any entities like sensors, switches, or lights.

Instead, you use the integration through service calls:
- `pixelmagictool.send_to_wled_ddp` - Send images via DDP protocol
- `pixelmagictool.start_streaming` - Start streaming session
- `pixelmagictool.send_frame` - Send frame to active session
- `pixelmagictool.stop_streaming` - Stop streaming session

To use the integration:
1. Go to Developer Tools → Services
2. Select the service you want to use (e.g., `pixelmagictool.send_to_wled_ddp`)
3. Fill in the required parameters
4. Click "Call Service"

Or use it in automations:
```yaml
automation:
  - alias: "Display Album Art"
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

### No Debug Logging / Can't See What's Happening

**Question**: I'm not seeing any log messages from the integration. How do I enable debug logging?

**Answer**: The integration uses standard Python logging. By default, Home Assistant only shows `INFO` level and above. To see detailed debug information:

1. Add this to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.pixelmagictool: debug
   ```

2. Restart Home Assistant

3. Check the logs:
   - Settings → System → Logs
   - Or use the command line: `ha core logs`

With debug logging enabled, you'll see messages like:
```
[custom_components.pixelmagictool.services] send_to_wled_ddp service called: host=192.168.1.100, source_type=url, dimensions=32x32, brightness=255, segment=0
[custom_components.pixelmagictool.converter] Loading image from URL: https://example.com/image.png
[custom_components.pixelmagictool.ddp] Skipping HTTP API preparation - sending DDP packets directly (matching WLEDVideoSync web UI behavior)
[custom_components.pixelmagictool.ddp] Sending 32x32 image (1024 pixels, 3072 bytes) via DDP to 192.168.1.100:4048
[custom_components.pixelmagictool.services] Successfully sent image via DDP to WLED
```

### Image Tries to Load but Reverts to Previous Setting

**Question**: When I send an image, the screen briefly shows something then goes back to the previous display. What's wrong?

**Answer**: This was a common issue that has been **fixed in the latest version**. The problem was caused by HTTP API preparation interfering with DDP data.

**Solution**: Make sure you're using the latest version of the integration. The fix:
- HTTP API preparation is now **disabled by default**
- DDP packets are sent directly to WLED (matching WLEDVideoSync web UI behavior)
- This prevents the device state conflict that caused images to revert

If you still experience this issue:

1. **Verify WLED is not in a conflicting mode**:
   - Open WLED web UI
   - Check that no effects are running
   - Ensure the segment is set to "Solid" effect

2. **Test with a simple solid color image**:
   ```yaml
   service: pixelmagictool.send_to_wled_ddp
   data:
     image_url: "https://via.placeholder.com/32x32/FF0000/FF0000.png"
     wled_host: "192.168.1.100"
     width: 32
     height: 32
     brightness: 255
   ```

3. **Check your WLED version**:
   - Ensure you're running WLED 0.13.0 or later
   - Update WLED if needed

4. **Try with prepare_device=True** (advanced):
   - In rare cases, you might need HTTP API preparation
   - This is not recommended and should only be used as a last resort
   - The service doesn't expose this parameter, but it can be set in custom code

### Connection Refused / Network Errors

**Question**: I get "Connection refused" or "Network error" when trying to send images.

**Answer**: This indicates network connectivity issues between Home Assistant and your WLED device.

**Troubleshooting steps**:

1. **Verify WLED IP address**:
   ```bash
   ping 192.168.1.100
   ```

2. **Check UDP port 4048 is accessible**:
   ```bash
   nc -zvu 192.168.1.100 4048
   ```

3. **Ensure WLED device is powered on and connected to network**

4. **Check firewall settings**:
   - Make sure UDP port 4048 is not blocked
   - Check both Home Assistant and WLED device firewalls

5. **Test from WLED web UI**:
   - Open WLED settings
   - Go to Sync Interfaces
   - Ensure DDP is enabled (default is enabled)

### Matrix Dimensions Don't Match

**Question**: The image appears distorted or only partially displayed.

**Answer**: The width and height parameters must match your WLED matrix configuration.

**Solution**:

1. **Check your WLED matrix configuration**:
   - Open WLED web UI
   - Go to Settings → LED Preferences → 2D Configuration
   - Note the width and height values

2. **Use the same dimensions in service call**:
   ```yaml
   service: pixelmagictool.send_to_wled_ddp
   data:
     image_url: "{{ your_image_url }}"
     wled_host: "192.168.1.100"
     width: 32  # Must match WLED config
     height: 32  # Must match WLED config
     brightness: 255
   ```

### Brightness Too Low / Too High

**Question**: The image is too dim or too bright on my matrix.

**Answer**: Adjust the `brightness` parameter (0-255).

**Tips**:
- Start with `brightness: 128` (50%)
- Increase for brighter: `brightness: 200` or `brightness: 255`
- Decrease for dimmer: `brightness: 64` or `brightness: 32`
- Note: This is applied during image processing, not via WLED's global brightness setting

### Image Won't Load from URL

**Question**: I get "Failed to process image" error when using image_url.

**Answer**: This usually means the URL is not accessible from Home Assistant.

**Troubleshooting**:

1. **Verify the URL is correct and accessible**:
   - Try opening the URL in your browser
   - Check for typos in the URL

2. **Check URL is reachable from Home Assistant**:
   ```bash
   curl -I "https://example.com/image.png"
   ```

3. **For template URLs** (like album art):
   ```yaml
   # Make sure the template renders correctly
   image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
   ```

4. **Try with a known-good URL first**:
   ```yaml
   image_url: "https://via.placeholder.com/32x32/FF0000/FF0000.png"
   ```

### Image File Not Found

**Question**: I get "Image file not found" error when using image_path.

**Answer**: The file path must be accessible from within Home Assistant.

**Solution**:

1. **Use absolute paths within Home Assistant**:
   ```yaml
   # Correct - using /config directory
   image_path: "/config/www/my_image.jpg"
   
   # Incorrect - relative paths don't work
   image_path: "www/my_image.jpg"
   ```

2. **Recommended locations**:
   - `/config/www/` - For images you want to serve via HTTP
   - `/config/images/` - For private images

3. **Verify file exists and permissions are correct**:
   ```bash
   ls -la /config/www/my_image.jpg
   ```

## Getting Help

If you're still experiencing issues:

1. **Enable debug logging** (see above)
2. **Check the logs** for error messages
3. **Try with a simple test**:
   ```yaml
   service: pixelmagictool.send_to_wled_ddp
   data:
     image_url: "https://via.placeholder.com/32x32/FF0000/FF0000.png"
     wled_host: "192.168.1.100"
     width: 32
     height: 32
     brightness: 255
   ```
4. **Verify your WLED device works** with other DDP senders (like WLEDVideoSync web UI)
5. **Open an issue on GitHub** with:
   - Your Home Assistant version
   - Your WLED version and device type
   - Complete log output with debug logging enabled
   - Service call parameters you're using

## Advanced Topics

### Using prepare_device Parameter

In most cases, you should NOT need to enable HTTP API preparation. However, if you have specific requirements:

**Note**: The `prepare_device` parameter is not exposed in the service schema by default. It can only be set programmatically in custom components or scripts that call the underlying API directly.

The default behavior (`prepare_device=False`) matches WLEDVideoSync web UI and works correctly for the vast majority of WLED devices.

### Continuous Streaming Mode

For high-frequency updates (e.g., video streaming, animations):

1. **Start streaming session**:
   ```yaml
   service: pixelmagictool.start_streaming
   data:
     session_id: "my_stream"
     wled_host: "192.168.1.100"
     segment_id: 0
   ```

2. **Send frames**:
   ```yaml
   service: pixelmagictool.send_frame
   data:
     session_id: "my_stream"
     image_url: "{{ frame_url }}"
     width: 32
     height: 32
     brightness: 255
   ```

3. **Stop streaming**:
   ```yaml
   service: pixelmagictool.stop_streaming
   data:
     session_id: "my_stream"
   ```

Streaming keeps the UDP socket open, reducing overhead for rapid updates.
