# WLED JSON API Integration

## Overview

This integration **already uses the WLED JSON API** to send converted images to your WLED devices. The `pixelmagictool.send_to_wled` service:

1. Converts your image using the Pixel Magic Tool API
2. Generates WLED-compatible JSON
3. **Sends it directly to WLED's `/json/state` endpoint**
4. Verifies the response from WLED

## How It Works

```
┌─────────────────────────┐
│ Home Assistant Service  │
│ pixelmagictool.         │
│ send_to_wled            │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Pixel Magic Tool API    │
│ pixelmagictool.         │
│ vercel.app              │
│ (Image Conversion)      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ WLED JSON Generated     │
│ {                       │
│   "on": true,           │
│   "bri": 128,           │
│   "seg": {              │
│     "id": 0,            │
│     "i": [...]          │
│   }                     │
│ }                       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ HTTP POST to WLED       │
│ http://[WLED-IP]/       │
│ json/state              │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ WLED Device Updates     │
│ LED Matrix Display      │
└─────────────────────────┘
```

## WLED JSON API Endpoint

The integration posts to: **`http://[WLED-IP]/json/state`**

This is WLED's primary JSON API endpoint for controlling device state.

## Example JSON Sent to WLED

The integration sends JSON in this format (includes parameters for reliable device updates):

```json
{
  "on": true,
  "bri": 128,
  "liv": false,
  "seg": {
    "id": 0,
    "fx": 0,
    "sel": true,
    "i": [
      0, 5, "FF0000",
      6, 10, "00FF00",
      11, 15, "0000FF"
    ]
  }
}
```

Where:
- `on`: Turn WLED on/off
- `bri`: Brightness (0-255)
- `liv`: Live override (false = apply changes immediately to device)
- `seg.id`: Segment ID
- `seg.fx`: Effect ID (0 = Solid, required for individual LED control)
- `seg.sel`: Mark segment as selected/active
- `seg.i`: Individual LED color data (pattern-based)

## Using the Services

### Option 1: Direct Send (Recommended)

Use `pixelmagictool.send_to_wled` - it does everything in one call:

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
```

### Option 2: Convert First, Then Send

Convert and store in sensor, then use the JSON later:

```yaml
# Step 1: Convert and store
service: pixelmagictool.convert_image
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  width: 32
  height: 32
  brightness: 128

# Step 2: Use stored JSON (from sensor)
# The JSON is stored in: sensor.pixel_magic_tool_last_conversion.attributes.wled_json
```

## Manual WLED API Calls

If you want to manually send JSON to WLED (using stored conversions), you can use REST commands:

### Setup REST Command

Add to `configuration.yaml`:

```yaml
rest_command:
  send_to_wled:
    url: "http://{{ wled_host }}/json/state"
    method: POST
    content_type: "application/json"
    payload: "{{ wled_json }}"
```

### Use in Automation

```yaml
automation:
  - alias: "Manual WLED Send"
    trigger:
      - platform: state
        entity_id: input_button.update_display
    action:
      # Get JSON from sensor
      - service: rest_command.send_to_wled
        data:
          wled_host: "192.168.1.100"
          wled_json: "{{ state_attr('sensor.pixel_magic_tool_last_conversion', 'wled_json') }}"
```

## WLED JSON API Features

### Full State Control

You can also control other WLED features by modifying the JSON:

```yaml
# Turn on with specific effect
{
  "on": true,
  "bri": 200,
  "seg": {
    "id": 0,
    "fx": 0,    # Effect ID
    "sx": 128,  # Effect speed
    "i": [...]  # Your pixel data
  }
}
```

### Multiple Segments

Update multiple segments:

```yaml
{
  "on": true,
  "seg": [
    {
      "id": 0,
      "i": [...] # Segment 0 data
    },
    {
      "id": 1,
      "i": [...] # Segment 1 data
    }
  ]
}
```

## Advanced: Using WLED Integration

If you have the official WLED integration installed, you can combine both:

```yaml
automation:
  - alias: "Combined WLED Control"
    action:
      # First set the image via Pixel Magic Tool
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ image_url }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
      
      # Then adjust other settings via WLED integration
      - service: light.turn_on
        target:
          entity_id: light.wled_matrix
        data:
          effect: "Solid"  # Ensure solid effect
```

## WLED JSON API Reference

The Pixel Magic Tool integration uses these WLED JSON API features:

### POST to `/json/state`
- Updates WLED state and LED colors
- Returns: `{"success": true}` on success

### GET from `/json/state` (for verification)
- Retrieves current WLED state
- Can be used to verify changes

### Key WLED Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `on` | boolean | Turn WLED on/off |
| `bri` | int (0-255) | Master brightness |
| `seg.id` | int | Segment ID to update |
| `seg.i` | array | Individual LED data |
| `seg.col` | array | Color palette (optional) |
| `seg.fx` | int | Effect ID (0 = Solid, required for individual LED control) |
| `seg.sx` | int | Effect speed |
| `seg.ix` | int | Effect intensity |
| `seg.sel` | boolean | Mark segment as selected/active |
| `liv` | boolean | Live override mode |

### Important Parameters for Device Updates

The integration automatically includes these critical parameters to ensure the WLED device updates properly:

- **`seg.fx: 0`** - Sets the effect to "Solid" mode, which is required for individual LED control. Without this, WLED may not display the custom pixel data.
- **`seg.sel: true`** - Marks the segment as selected and active, ensuring WLED applies the changes to the physical LEDs.
- **`liv: false`** - Disables live override mode, ensuring updates are applied immediately to the device rather than just showing in the preview.

These parameters fix the common issue where JSON updates show in the WLED web UI preview but the actual device doesn't update.

## Pattern Formats Explained

The `seg.i` array can use different patterns:

### Individual Pattern
```json
["FF0000", "00FF00", "0000FF", ...]
```
Simple list of hex colors.

### Index Pattern
```json
[0, "FF0000", 1, "00FF00", 2, "0000FF", ...]
```
Explicit positioning: [index, color, index, color, ...]

### Range Pattern (Most Efficient)
```json
[0, 5, "FF0000", 5, 10, "00FF00", 10, 15, "0000FF"]
```
Ranges: [start, end, color, start, end, color, ...]

## Troubleshooting WLED API Calls

### Check WLED API is Accessible

```bash
# Test WLED is responding
curl http://192.168.1.100/json/state

# Should return current WLED state JSON
```

### Common Issues

1. **Connection Refused**
   - Verify WLED IP address
   - Check firewall settings
   - Ensure WLED device is powered on

2. **`success: false` Response**
   - Check segment ID exists in WLED
   - Verify segment configuration (2D matrix setup)
   - Check JSON size isn't too large (WLED has buffer limits)

3. **Timeout Errors**
   - WLED device may be busy
   - Increase timeout parameter
   - Check network latency

4. **No Visual Change / Preview Shows but Device Doesn't Update**
   - **FIXED**: The integration now automatically sets the correct parameters (`fx=0`, `sel=true`, `liv=false`) to ensure device updates
   - If using older versions, verify segment is active
   - Check brightness isn't 0
   - Ensure LEDs are properly connected
   - Verify 2D matrix configuration in WLED
   - Make sure WLED is not in live mode (now disabled automatically)
   - Verify the segment effect is set to "Solid" (now set automatically)

### Debug Logging

Enable debug logging for the integration:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.pixelmagictool: debug
```

Check logs at: Settings → System → Logs

## WLED API Documentation

For more details on WLED's JSON API:
- Official Docs: https://kno.wled.ge/interfaces/json-api/
- WLED GitHub: https://github.com/Aircoookie/WLED
- WLED Discourse: https://wled.discourse.group/

## Example: Complete Workflow

Here's a complete example showing the full workflow:

```yaml
automation:
  - alias: "Album Art to WLED via JSON API"
    description: "Complete workflow: image URL → conversion → WLED JSON API"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    condition:
      - condition: state
        entity_id: media_player.spotify
        state: "playing"
    action:
      # Single service call does it all:
      # 1. Gets image from URL
      # 2. Converts via Pixel Magic Tool API
      # 3. Generates WLED JSON
      # 4. POSTs to http://192.168.1.100/json/state
      # 5. Verifies success response
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
          brightness: 200
          pattern: "range"
          segment_id: 0
          timeout: 10
```

## Summary

✅ **Yes, the integration already uses the WLED JSON API!**

The `pixelmagictool.send_to_wled` service:
- Converts images to WLED format
- Automatically sends to `http://[WLED-IP]/json/state`
- Handles the HTTP POST request
- Verifies the response
- Logs any errors

You don't need to do anything extra - it's all built-in and working! 🎉
