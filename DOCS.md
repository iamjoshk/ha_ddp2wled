# Pixel Magic Tool

## About

Pixel Magic Tool is a powerful add-on that converts any image into code in JSON WLED format for 2D Matrix LED panels. This tool is essential for anyone working with WLED-controlled LED matrices who wants to display custom images and animations.

## Features

- Converts any type of image to WLED JSON format
- Multiple output format options (JSON, Home Assistant YAML, CURL)
- Pattern selection (Individual, Index, Range)
- Adjustable brightness control
- Support for animated GIFs
- Image resizing capabilities
- Transparent pixel color replacement
- Compression options for large images
- Preview and simulation capabilities
- Save, copy, or download generated code

## Installation

1. Add this repository to your Home Assistant HACS: `https://github.com/iamjoshk/PixelMagicTool`
2. Search for "Pixel Magic Tool" in the HACS Add-on Store
3. Click Install
4. Start the add-on
5. Access the web interface through the Add-on UI

## Configuration

The add-on has minimal configuration options:

```yaml
log_level: info
```

### Option: `log_level`

The log level to use for the add-on. Options include:
- `trace`
- `debug`
- `info` (default)
- `notice`
- `warning`
- `error`
- `fatal`

## How to use

1. Open the Pixel Magic Tool web interface through the Home Assistant UI
2. Enter your WLED device hostname/IP address
3. Select your segment configuration
4. Choose your output format:
   - **WLED JSON**: Direct JSON format for WLED
   - **Home Assistant**: YAML configuration for HA switch integration
   - **CURL**: Command-line format for scripting
5. Upload or select an image:
   - Drag and drop a local file
   - Select from images already uploaded to your WLED device
6. Adjust settings:
   - Pattern type (Individual, Index, or Range)
   - Brightness level
   - Enable/disable image resizing
   - Set custom dimensions if needed
   - Enable compression for large images
   - Handle transparent pixels
7. Click "Generate" to create the code
8. Use the generated output:
   - **Copy**: Copy to clipboard
   - **Save**: Save preset directly to WLED device
   - **Download**: Download as file
   - **Simulate**: Preview on your WLED device

## Tips

- For large images (over 100x100 pixels), enable compression to reduce data size
- Use the Range pattern for most efficient data compression
- Test with the Simulate button before saving presets
- Access WLED's file upload at `http://[WLED-IP]/edit` to manage images

## Animated GIFs

To convert animated GIFs:

1. Enable the "Animation" toggle
2. Select or upload a GIF file
3. Set the number of frames (or 0 for all frames)
4. Adjust duration and transition times
5. Generate and save as a playlist

## Support

For issues, feature requests, or contributions, visit:
https://github.com/iamjoshk/PixelMagicTool/issues

## Credits

Original tool by @ajotanc
Home Assistant add-on packaging and HACS integration
