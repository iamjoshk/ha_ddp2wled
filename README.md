# HA DDP2WLED — DDP Sender for WLED
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/iamjoshk/ha_ddp2wled)](https://github.com/iamjoshk/ha_ddp2wled/releases)
![GitHub Release](https://img.shields.io/github/v/release/iamjoshk/ha_ddp2wled?include_prereleases&label=beta)


<img width="256" height="256" alt="ha_ddp2wled_icon" src="https://github.com/user-attachments/assets/3ed3db34-920a-4487-8c24-278185451c60" />


This started as a fork of https://github.com/ApolloAutomation/PixelMagicTool but I was not satisfied with the result of the image. While searching for solutions to the compression, I stumbled on https://github.com/zak-45/WLEDVideoSync and decided to leverage a DDP stream instead.

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

## Services

### `ha_ddp2wled.send_to_wled_ddp`
Sends an image to WLED device via DDP protocol with optional WLEDVideoSync-compatible image processing.

#### Required Parameters

- `Image URL` **or** `Image Path` (both templatable)
- `WLED Host`: IP address or hostname of the WLED device
- `Width`: Target width in pixels for the matrix display
- `Height`: Target height in pixels for the matrix display

#### Optional Parameters
- `Brightness`: Display brightness (0-255, default 255) — templatable
- `Segment ID`: WLED segment to target (default 0)
- `Timeout`: Network timeout in seconds (default 10)
- `Keepalive Seconds`: Duration to keep re-sending the frame (default 0 = send once)
- `Keepalive Interval`: Seconds between keepalive sends (default 1)

#### Image Processing Options
- `Auto Image Adjustment`: Enable automatic image adjustment (true/false, default true)
- `Auto Clipping Percentage`: Histogram clipping percentage for auto image adjustment (0.0-50.0, default 0.0)
- `Saturation`: Color saturation multiplier (0.0-2.0, default 1.0)
- `Contrast`: Contrast adjustment (0.5-2.0, default 1.0)
- `Sharpen`: Sharpening intensity (0.0-2.0, default 0.0)
- `Gamma Correction`: Gamma correction (0.1-3.0, default 1.0)
- `Red Balance`: Red channel color balance (1.0 = no change, 0.0 = no red, 2.0 = enhanced red)
- `Green Balance`: Green channel color balance (1.0 = no change, 0.0 = no green, 2.0 = enhanced green)
- `Blue Balance`: Blue channel color balance (1.0 = no change, 0.0 = no blue, 2.0 = enhanced blue)


#### Basic Example
```yaml
service: ha_ddp2wled.send_to_wled_ddp
data:
  image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: 200
```

#### Advanced Example with Image Processing
```yaml
service: ha_ddp2wled.send_to_wled_ddp
data:
  image_url: "https://example.com/album-cover.jpg"
  wled_host: "192.168.1.100"
  width: 32
  height: 32
  brightness: "{{ states('input_number.display_brightness') | int }}"
  saturation: 1.2
  contrast: 1.1
  sharpening: 0.5
  auto_brightness: true
  keepalive_seconds: 300
```

#### Brightness Template Examples
- Time-based dimming: `brightness: "{{ 10 if now().hour <= 8 or now().hour >= 22 else 128 }}"`
- Slider control: `brightness: "{{ states('input_number.display_brightness') | int }}"`
- Conditional brightness: `brightness: "{{ 50 if is_state('sun.sun', 'below_horizon') else 200 }}"`

### `ha_ddp2wled.stop_ddp_stream`
Stops any active keepalive stream to the specified WLED device.

#### Required Parameters
- `wled_host`: IP address or hostname of the WLED device to stop streaming to

#### Example
```yaml
service: ha_ddp2wled.stop_ddp_stream
data:
  wled_host: "192.168.1.100"
```


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
