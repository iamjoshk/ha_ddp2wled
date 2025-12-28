# Pixel Magic Tool — DDP Sender for WLED

This repository now contains a **single Home Assistant service**: `pixelmagictool.send_to_wled_ddp`. All other PixelMagicTool features, streaming helpers, and standalone web tools have been removed.

## What it does
- Loads an image from a URL or local path
- Resizes it to your matrix dimensions
- Converts it to RGB24
- Sends it to a WLED device over DDP (UDP port 4048)

## Installation
1. Copy `custom_components/pixelmagictool` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant and add the integration (name-only config flow).

## Service: `pixelmagictool.send_to_wled_ddp`
Required fields:
- `wled_host`: IP/hostname of the WLED device
- `width`: target width in pixels
- `height`: target height in pixels
- Either `image_url` **or** `image_path`

Optional fields:
- `brightness` (0-255, default 255)
- `segment_id` (default 0)
- `timeout` seconds (default 10)

### Example
```yaml
service: pixelmagictool.send_to_wled_ddp
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 200
```

## License
See [LICENSE](LICENSE).
