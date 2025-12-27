# JSON Format Specification

## Overview

This document specifies the JSON format requirements for the PixelMagicTool integration. All JSON output must conform to the JSON standard (RFC 8259) with specific formatting requirements.

## Format Requirements

### 1. String Delimiters

**✓ CORRECT**: Use double quotes (`"`) for all strings and object keys

```json
{
  "on": true,
  "bri": 128,
  "seg": {
    "id": 0,
    "i": ["060505", "050706"]
  }
}
```

**✗ INCORRECT**: Never use single quotes (`'`) for JSON

```javascript
// This is NOT valid JSON
{'on': true, 'bri': 128}
```

### 2. Boolean Values

**✓ CORRECT**: Use lowercase `true` and `false`

```json
{
  "on": true,
  "live": false,
  "sel": true
}
```

**✗ INCORRECT**: Never use uppercase or string booleans

```javascript
// These are NOT valid JSON boolean values
{"on": True}   // Python-style (wrong)
{"on": FALSE}  // Uppercase (wrong)
{"on": "true"} // String (wrong, unless intentionally a string)
```

### 3. Number Values

Numbers should be unquoted (unless they are intentionally string representations):

```json
{
  "bri": 128,
  "id": 0,
  "fx": 0
}
```

### 4. String Values in Arrays

Color values in the `"i"` array are strings (hex color codes) and must use double quotes:

```json
{
  "seg": {
    "i": [
      "060505",
      "050706",
      "0c100f"
    ]
  }
}
```

## Complete Example

Here's a complete, correctly formatted WLED JSON payload:

```json
{
  "on": true,
  "bri": 128,
  "seg": {
    "id": 0,
    "i": [
      "060505",
      "050706",
      "0c100f",
      "2a2c2c",
      "343434"
    ],
    "fx": 0,
    "sel": true
  },
  "live": false
}
```

## Implementation Guidelines

### Python Code

**✓ ALWAYS use `json.dumps()` for serialization:**

```python
import json

wled_data = {
    "on": True,  # Python True → JSON true
    "bri": 128,
    "seg": {
        "id": 0,
        "i": ["060505", "050706"],
        "fx": 0,
        "sel": True  # Python True → JSON true
    },
    "live": False  # Python False → JSON false
}

# Correct: Use json.dumps()
json_string = json.dumps(wled_data)
# Result: {"on": true, "bri": 128, ...}
```

**✓ ALWAYS use `json=` parameter with aiohttp:**

```python
async with session.post(url, json=wled_data) as response:
    # aiohttp automatically serializes with json.dumps()
    pass
```

**✗ NEVER use `str()` or `repr()` for JSON:**

```python
# WRONG: This produces Python dict format with single quotes
json_string = str(wled_data)  # {'on': True, 'bri': 128}

# WRONG: This also produces Python format
json_string = repr(wled_data)  # {'on': True, 'bri': 128}
```

### JavaScript Code

**✓ ALWAYS use `JSON.stringify()` for serialization:**

```javascript
const wledData = {
    on: true,  // JavaScript true → JSON true
    bri: 128,
    seg: {
        id: 0,
        i: ["060505", "050706"],
        fx: 0,
        sel: true  // JavaScript true → JSON true
    },
    live: false  // JavaScript false → JSON false
};

// Correct: Use JSON.stringify()
const jsonString = JSON.stringify(wledData);
// Result: {"on":true,"bri":128,...}
```

**✗ NEVER manually construct JSON strings:**

```javascript
// WRONG: Manual string construction is error-prone
const jsonString = `{"on": ${data.on}, "bri": ${data.bri}}`;
```

## Validation

To validate JSON formatting, use the provided validation script:

```bash
python3 validate_json_format.py
```

This script verifies:
- Strings use double quotes
- Booleans are lowercase
- Format conforms to JSON standard

## Common Issues

### Issue 1: Python dict repr in logs

**Problem**: Using `%s` formatting with dicts in logging produces Python format:

```python
# This logs Python format with single quotes
_LOGGER.debug("Data: %s", wled_data)
# Output: Data: {'on': True, 'bri': 128}
```

**Solution**: Convert to JSON for logging if needed:

```python
import json
_LOGGER.debug("Data: %s", json.dumps(wled_data))
# Output: Data: {"on": true, "bri": 128}
```

### Issue 2: Shell command quoting

**Problem**: Confusion between JSON quotes and shell quotes

In shell commands (bash, curl), the JSON itself uses double quotes, but the shell argument uses single quotes:

```bash
curl -X POST "http://192.168.1.100/json/state" -d '{"on": true}' -H "Content-Type: application/json"
```

This is CORRECT! The single quotes are shell delimiters, not part of the JSON.

## Testing

Always test JSON output with the official JSON parser:

```python
import json

# Test serialization
json_string = json.dumps(data)

# Verify it can be parsed back
parsed = json.loads(json_string)
```

## References

- [JSON Specification (RFC 8259)](https://tools.ietf.org/html/rfc8259)
- [WLED JSON API Documentation](https://kno.wled.ge/interfaces/json-api/)
- Python `json` module: https://docs.python.org/3/library/json.html
- JavaScript `JSON` object: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON
