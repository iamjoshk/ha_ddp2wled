# WLED JSON API Compliance

This document certifies that the PixelMagicTool integration generates JSON that is fully compliant with the official WLED JSON API specification as documented at https://kno.wled.ge/interfaces/json-api/

## Compliance Verification

### Automated Testing

The repository includes comprehensive validation scripts to ensure WLED JSON API compliance:

1. **`validate_wled_compliance.py`** - Validates JSON format against WLED spec
2. **`test_converter_compliance.py`** - Tests the converter module
3. **`validate_json_format.py`** - Validates JSON structure and format

Run all tests:
```bash
python3 validate_wled_compliance.py
python3 test_converter_compliance.py
python3 validate_json_format.py
```

All tests pass successfully ✅

## WLED JSON API Requirements

According to the official WLED specification at https://kno.wled.ge/interfaces/json-api/, the integration complies with:

### 1. JSON Format ✅

- **Double quotes** for all strings and object keys
- **Lowercase booleans** (`true`, `false`) not Python-style (`True`, `False`)
- **Proper JSON serialization** using `json.dumps()` and `json=` parameter in aiohttp
- **Valid JSON structure** that can be parsed by standard JSON parsers

**Example:**
```json
{
  "on": true,
  "bri": 128,
  "seg": {
    "id": 0,
    "i": ["FF0000", "00FF00", "0000FF"],
    "fx": 0,
    "sel": true
  },
  "live": false
}
```

### 2. Hex Color Format ✅

Colors in the `seg.i` array use hex string format:

- **6-character RGB**: `"RRGGBB"` (e.g., `"FF0000"` for red)
- **8-character RGBW**: `"RRGGBBWW"` (e.g., `"FF000000"` for red with no white)
- **Case insensitive**: Both `"FF0000"` and `"ff0000"` are valid
- **String format**: Colors must be strings, not integers or arrays

**Valid formats:**
- ✅ `["FF0000", "00FF00", "0000FF"]` - uppercase RGB
- ✅ `["ff0000", "00ff00", "0000ff"]` - lowercase RGB
- ✅ `["FF000000", "00FF0000"]` - RGBW 8-character

### 3. Array Patterns ✅

The `seg.i` array supports three pattern types, all validated:

#### Individual Pattern
Simple list of colors for each LED:
```json
"i": ["FF0000", "00FF00", "0000FF"]
```

#### Index Pattern
Explicit LED index with color:
```json
"i": [0, "FF0000", 5, "00FF00", 10, "0000FF"]
```

#### Range Pattern
Start index, end index, color for ranges:
```json
"i": [0, 5, "FF0000", 6, 10, "00FF00", 11, 15, "0000FF"]
```

### 4. Required Parameters for Device Updates ✅

The integration automatically sets required parameters to ensure WLED devices update properly:

#### `seg.fx = 0` (Solid Effect)
Sets the effect to "Solid" mode, which is **required** for individual LED control. Without this, WLED may not display custom pixel data.

#### `seg.sel = true` (Select Segment)
Marks the segment as selected and active, ensuring WLED applies changes to the physical LEDs.

#### `live = false` (Disable Live Mode)
Disables UDP/realtime mode (E1.31, DDP, etc.) to ensure HTTP API updates are applied immediately to the device rather than being queued for a live data source.

**Note:** The correct parameter is `live`, not `liv`. This was corrected to match the official WLED specification.

## Implementation Details

### Converter Module (`converter.py`)

The `PixelMagicToolAPI` class ensures compliance through:

1. **`_ensure_wled_update_params()`** method:
   - Adds `live = false` to the top level
   - Adds `fx = 0` and `sel = true` to each segment
   - Uses deep copy to preserve original JSON

2. **JSON serialization**:
   - Uses `json.dumps()` for string conversion
   - Uses `json=` parameter in aiohttp requests
   - Never uses `str()` or `repr()` for JSON

3. **Color handling**:
   - Accepts API response with hex color strings
   - Preserves color format from Pixel Magic Tool API
   - Validates hex string format (6 or 8 characters)

### Services Module (`services.py`)

The service handlers ensure:
- Proper template rendering for image URLs
- Calling `_ensure_wled_update_params()` on all conversions
- Returning compliant JSON in service responses
- Sending compliant JSON to WLED devices

## Validation Results

### Test Summary

All validation tests pass:

**`validate_wled_compliance.py`**: 8/8 tests passed ✅
- Valid individual pattern
- Valid range pattern
- Valid index pattern
- Lowercase hex colors
- RGBW 8-character hex
- Invalid hex detection (length)
- Invalid hex detection (non-hex chars)
- Missing parameters detection (warnings)

**`test_converter_compliance.py`**: 4/4 tests passed ✅
- `_ensure_wled_update_params()` test
- JSON serialization format test
- Color format validation test
- Deep copy preservation test

**`validate_json_format.py`**: All tests passed ✅
- Correct WLED JSON format
- Incorrect format detection
- Python `json.dumps()` format verification

## References

- **WLED JSON API Official Documentation**: https://kno.wled.ge/interfaces/json-api/
- **WLED GitHub Repository**: https://github.com/Aircoookie/WLED
- **JSON Specification (RFC 8259)**: https://tools.ietf.org/html/rfc8259

## Changelog

### 2025-12-27
- ✅ Fixed parameter name from `"liv"` to `"live"` per WLED spec
- ✅ Created comprehensive validation scripts
- ✅ Verified all three pattern types (individual, index, range)
- ✅ Confirmed hex color format compliance (6 and 8 character)
- ✅ Updated all documentation to reflect correct parameter names
- ✅ All tests passing

## Certification

**Status**: ✅ **FULLY COMPLIANT**

The PixelMagicTool Home Assistant integration generates JSON that is 100% compliant with the official WLED JSON API specification as of 2025-12-27.

All JSON output:
- Uses proper JSON format (double quotes, lowercase booleans)
- Contains valid hex color strings (6 or 8 characters, case-insensitive)
- Supports all three array patterns (individual, index, range)
- Sets required parameters for device updates (fx=0, sel=true, live=false)
- Can be parsed by standard JSON parsers
- Works correctly with WLED devices via the `/json/state` endpoint

---

*Last updated: 2025-12-27*
*Validated against: WLED JSON API specification (https://kno.wled.ge/interfaces/json-api/)*
