# HA DDP2WLED — DDP Sender for WLED
<img width="256" height="256" alt="ha_ddp2wled_icon" src="https://github.com/user-attachments/assets/3ed3db34-920a-4487-8c24-278185451c60" />

This started as a fork of https://github.com/ApolloAutomation/PixelMagicTool but I was not satisfied with the result of the image. I found https://github.com/zak-45/WLEDVideoSync and leveraged that instead.

## What it does
- Loads an image from a URL or local path
- Resizes it to your matrix dimensions
- Converts it to RGB24
- Sends it to a WLED device over DDP (UDP port 4048)

## Installation

### Option 1: HACS (Recommended)
1. Go to HACS
2. Click the three dots menu (⋮) in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/iamjoshk/ha_ddp2wled`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "HA DDP2WLED" in HACS and install it
8. Restart Home Assistant
9. Go to Settings → Devices & Services → Add Integration
10. Search for "HA DDP2WLED" and add it (name-only config flow)

### Option 2: Manual Installation
1. Copy `custom_components/ha_ddp2wled` into your Home Assistant `custom_components` folder
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "HA DDP2WLED" and add it (name-only config flow)

## Service: `ha_ddp2wled.send_to_wled_ddp`
Required fields:
- `wled_host`: IP/hostname of the WLED device
- `width`: target width in pixels
- `height`: target height in pixels
- Either `image_url` **or** `image_path` (templatable)

Optional fields:
- `brightness` (0-255, default 255), templateable
- `segment_id` (default 0)
- `timeout` seconds (default 10)
- `keepalive_seconds` (default 0) — keep re-sending the frame so WLED does not revert after its realtime timeout
- `keepalive_interval` (default 1) — seconds between keepalive sends

### Example
```yaml
service: ha_ddp2wled.send_to_wled_ddp
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 200

```

Examples of templates for setting the brightness:
- `brightness: {{ 10 if now().hour <= 8 or now().hour >= 22 else 128 }}` would change the dim the display from 10pm to 8am.
- `brightness: {{ states('input_number.display_brightness') }}` would let you change the brightness from an independent slider.


## Reference: WLEDVideoSync upstream architecture
This integration is derived from the upstream [zak-45/WLEDVideoSync](https://github.com/zak-45/WLEDVideoSync) project. The relevant pieces there include:
- `src/net/ddp_queue.py`: `DDPDevice` handles UDP socket creation, queuing, retry logic, and packetizing RGB data into DDP-compliant packets.
- `src/cst/media.py`: `CASTMedia` prepares and streams media sources (images, videos, USB cameras) to DDP devices, using queues to avoid latency and supporting previews.
- `src/gui/videoplayer.py`: GUI helpers for uploading GIFs and wiring UI actions to the media/DDP sending backend.
- `WLEDVideoSync.py`: Entry point that wires configuration, NiceGUI UI, and background tasks together.
- `README`: Documents configuration such as FPS, scaling, and device IP settings for DDP targets.

Overall flow: media sources are prepared by `CASTMedia`, packetized by `DDPDevice`, and streamed over DDP to WLED devices.

## License
See [LICENSE](LICENSE).
