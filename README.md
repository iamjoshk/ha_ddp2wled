![PixelMagicTool](https://github.com/ajotanc/PixelMagicTool/assets/47322034/300b240b-40a3-4a9a-a6f0-925631919d9b)

# Pixel Magic Tool - Home Assistant Integration

[![Home Assistant Integration](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)](https://www.home-assistant.io/)
[![HACS Compatible](https://img.shields.io/badge/HACS-Compatible-brightgreen.svg)](https://hacs.xyz/)

A Home Assistant custom integration that converts images to WLED JSON format for HUB75 and 2D Matrix LED panels. Perfect for displaying album art, weather icons, or any dynamic images on your LED displays!

## What This Does

This integration provides **Home Assistant services** that can:
- 🔄 Convert images from URLs (including sensor attributes) to WLED format
- 📤 Send converted images directly to WLED devices
- 🎨 Work with album art from media players, weather icons, camera snapshots, and more
- 🤖 Be called from automations, scripts, and Node-RED flows

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
6. Select category: "Add-on"
7. Click "Add"
8. Find "Pixel Magic Tool" in the add-on store
9. Click "Install"
10. Start the add-on
11. Access through the Home Assistant UI

### Manual Installation

1. Navigate to your Home Assistant's `/addons` directory
2. Clone this repository:
   ```bash
   git clone https://github.com/iamjoshk/PixelMagicTool.git
   ```
3. Restart Home Assistant
4. Go to Supervisor → Add-on Store
5. Refresh the page
6. Find "Pixel Magic Tool" in the local add-ons section
7. Click "Install"

## Features

- 🎨 Converts any type of image to WLED JSON format
- 📋 Multiple output formats: WLED JSON, Home Assistant YAML, CURL commands
- 🎭 Pattern selection (Individual, Index, Range)
- 💡 Adjustable brightness control
- 🎬 Convert animated GIFs with playlist support
- 📐 Image resizing capabilities
- 🌈 Convert transparent pixels to chosen color
- 🗜️ Compression options for large images
- 👁️ Live preview and simulation
- 💾 Save directly to WLED, copy to clipboard, or download generated code
- 🔗 Select images directly from **[WLED-IP]/edit** or upload local files

## Usage

### As a Home Assistant Add-on

1. Open the Pixel Magic Tool add-on from your Home Assistant sidebar
2. Enter your WLED device IP address or hostname
3. Upload an image or select from WLED's storage
4. Configure your preferences:
   - Select segment and dimensions
   - Choose output format
   - Adjust brightness
   - Enable compression if needed
5. Click "Generate" to create the WLED code
6. Use the generated output:
   - Save directly to WLED
   - Copy to clipboard
   - Download as file
   - Simulate on your device

### Tips for Best Results

- **Large Images**: Enable compression for images over 100x100 pixels
- **Pattern Selection**: Use "Range" pattern for best data compression
- **Testing**: Use the Simulate button before saving presets
- **Image Management**: Access WLED's file manager at `http://[WLED-IP]/edit`

### Animated GIFs

The tool supports animated GIF conversion:

1. Enable "Animation" toggle
2. Upload or select a GIF
3. Set frame count (0 = all frames)
4. Configure duration and transition
5. Generate and save as WLED playlist

## Configuration

The add-on has minimal configuration. See [DOCS.md](DOCS.md) for detailed documentation.

```yaml
log_level: info
```

### Improvements and fixes
### (12/7/2025)
- Added chunking to send larger amounts of data to WLED
- Added compression system to reduce amount of data

### (25/10/2023)
 - Correction in animation generation that was actually breaking
 - Button to return to WLED if pxmagic.htm is accessed via url (http://), if accessed via external (file://) the button will not show
 - Adjustments to CSS and some features
 - Rremoving unnecessary html
 - Correction of CORS error when using the file locally, it was unable to generate the images that are saved in WLED

#### (15/06/2023)
- Changing the use of **document**
- Creation of function **element** to be reduced in relation to **document.getElementById**
- Fixes
- Image being generated according to its size
- Re-creation of the redone image
- Reworked Resize, if your segment is 20x20 and you want to use 16x16 it will be fine, credits @blazoncek 
- Default Segment Default as 0 and **data-width** and **data-height** as 16 if user opens via Desktop and not via WLED, credits @ALDIY#2452 
- Final file size reduction
- Improved functionality and interaction between parameters
-
#### (12/06/2023)
- The API domain was **ajota.vercel.app** now it's **pixelmagictool.vercel.app**
- Performance in **pxmagic** and **inpxmagic** version
- Significantly decreased **pxmagic.htm** file size
- **range** pattern now in hybrid style to improve JSON size
- Version name change from **interface.htm** to **pxmagic.htm**
- Version name change from **inline.htm** to **inpxmagic.htm**

#### (09/06/2023)
- Fixed animation generation
- Fixed drag and drop function
- Fix when saving presets and playlist
- Function performance fixes
- Parameter text interpretation
- Interaction of functionality
- Save presets via API
- Auto default segment width and height

## INTERFACE VERSION
### Download
**Right-Click** [[Interface]](https://raw.githubusercontent.com/ajotanc/wled-matrix-converter/main/pxmagic.htm) and select save to your local computer.

### Tutorial
Showing usability in the interface version in an easy, simple and intuitive way.

https://github.com/ajotanc/wled-matrix-converter/assets/47322034/20ad60d1-3b01-42b6-9937-4dda3862a3a4

## INLINE VERSION
### Download
**Right-Click** [[Inline]](https://raw.githubusercontent.com/ajotanc/wled-matrix-converter/main/inpxmagic.htm) and select save to your local computer.

### Example of what the URL looks like
```
  GET http://[WLED-IP]/inpxmagic.htm?id=0&output=ha&brightness=255&pre_segment=individual&device=pixel_art_controller_001&unique_id=pixel_art_controller_001a&friendly_name=PixelArt&hostname=[WLED-IP]&color=3CCFFE5&image=33.png&download=true&simulate=false
```
## CURL GENERATE WLED JSON
```bash
# Local image upload
# Remember to change the \path\image.png path to the desired image path.
curl -X POST -F "file=@\path\image.png" "https://pixelmagictool.vercel.app/api/wled/image?id=0&output=json&brightness=255&pre_segment=individual&hostname=10.0.0.41&color=CCFFE5"

# External image upload
curl -X POST -F "file=@-;filename=image.png" "https://pixelmagictool.vercel.app/api/wled/image?id=0&output=curl&brightness=255&pre_segment=individual&hostname=10.0.0.41&color=CCFFE5" < <(curl -s "https://img.freepik.com/premium-vector/lightning-pixel-art-gaming-item-game-pixel-lightning_158677-585.jpg")
# OR
curl -o /tmp/image.png -s "https://img.freepik.com/premium-vector/lightning-pixel-art-gaming-item-game-pixel-lightning_158677-585.jpg" && curl -X POST -F "file=@/tmp/image.png" "https://pixelmagictool.vercel.app/api/wled/image?id=0&output=curl&brightness=255&pre_segment=individual&hostname=10.0.0.41&color=3CCFFE5"
```

#### Description of parameters
| Parameters | Type | Description | Default | Required |
| ---------- | ---- | ------- | ----------- | -------- | 
| `id` | `integer` | Segment id | **0** | ✅
| `output` or `o` | `string` | Output type, options [json, curl, ha] | **json** | ✅
| `brightness` or `bri` | `integer` | Brightness of the LEDs | **128** | ✅
| `pattern` or `pat` | `string` | Pattern type, options [individual ["FFFFFF"], index [0, "FFFFFF"], range [0, 5, "FFFFFF"] | **individual** | ✅
| `hostname` or `hn` | `string` | WLED IP | - | ✅
| `width` or `w` | `number` | Resize image width | **16** | ⬜️
| `height` or `h` | `number` | Resize image height | **16** | ⬜️
| `device` or `d` | `string` | Device name, mandatory if the output is "ha" | - | ⬜️
| `unique_id` or `uid` | `string` | Unique device id, required if output is "ha" | - | ⬜️
| `friendly_name` or `fn` | `string` | Friendly name of the device, mandatory if the output is "ha" | - | ⬜️
| `color` or `c` | `string` | If the image contains a transparent background, you can change it to a desired color by passing the color in the HEX pattern | - | ⬜️
| `animation` or `anim` | `boolean` | If true, it will return the WLED JSON according to the number of frames in the GIF image. | **false** | ⬜️
| `amount` or `amt` | `number` | Number of frames contained in the GIF image, if the **animation** parameter is **true** | **0** | ⬜️
| `delay` or `dl` | `number` | Delay seconds between executions **curl**, optional and only for **output** curl | **2** | ⬜️
| `name` or `n` | `string` | Name of the preset to be saved | - | ⬜️
| `psave` or `ps` | `number` | Preset id to be saved | - | ⬜️
| `image` | `string` | Image that will be converted to JSON WLED, required only if using the **inpxmagic** version | - | ⬜️
| `file` | `boolean` | If true, it will download the file according to the output, required only if using the **inpxmagic** version | **false** | ⬜️
| `simulate` | `boolean` | If true and output is "json" then simulate JSON WLED, required only if using the **inpxmagic** version | **false** | ⬜️
