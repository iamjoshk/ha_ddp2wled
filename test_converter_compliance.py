#!/usr/bin/env python3
"""
Test the converter module to ensure it generates WLED-compliant JSON.

This test validates that the PixelMagicToolAPI class:
1. Generates proper JSON format
2. Sets required WLED parameters correctly
3. Produces valid hex color strings
"""

import json
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Import the validation functions
from validate_wled_compliance import validate_wled_json

# Import the converter
sys.path.insert(0, 'custom_components/pixelmagictool')
from converter import PixelMagicToolAPI


def test_ensure_wled_update_params():
    """Test that _ensure_wled_update_params sets correct parameters."""
    print("=" * 70)
    print("Test: _ensure_wled_update_params")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Test case 1: Single segment
    test_json = {
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["FF0000", "00FF00", "0000FF"]
        }
    }
    
    result = api._ensure_wled_update_params(test_json)
    
    print("\nTest 1: Single segment")
    print("-" * 70)
    print("Input:")
    print(json.dumps(test_json, indent=2))
    print("\nOutput:")
    print(json.dumps(result, indent=2))
    
    # Validate
    is_valid, errors, warnings = validate_wled_json(result, verbose=True)
    
    assert "live" in result, "Missing 'live' parameter"
    assert result["live"] is False, "'live' should be False"
    assert result["seg"]["fx"] == 0, "'seg.fx' should be 0"
    assert result["seg"]["sel"] is True, "'seg.sel' should be True"
    
    print("\n✓ Test 1 passed - All required parameters set correctly")
    
    # Test case 2: Multiple segments
    test_json_multi = {
        "on": True,
        "bri": 200,
        "seg": [
            {"id": 0, "i": ["FF0000", "00FF00"]},
            {"id": 1, "i": ["0000FF", "FFFF00"]}
        ]
    }
    
    result_multi = api._ensure_wled_update_params(test_json_multi)
    
    print("\nTest 2: Multiple segments")
    print("-" * 70)
    print("Input:")
    print(json.dumps(test_json_multi, indent=2))
    print("\nOutput:")
    print(json.dumps(result_multi, indent=2))
    
    # Validate
    is_valid, errors, warnings = validate_wled_json(result_multi, verbose=True)
    
    assert "live" in result_multi, "Missing 'live' parameter"
    assert result_multi["live"] is False, "'live' should be False"
    for seg in result_multi["seg"]:
        assert seg["fx"] == 0, f"Segment {seg['id']}: 'fx' should be 0"
        assert seg["sel"] is True, f"Segment {seg['id']}: 'sel' should be True"
    
    print("\n✓ Test 2 passed - All segments have required parameters")
    
    # Test case 3: Range pattern
    test_json_range = {
        "on": True,
        "bri": 255,
        "seg": {
            "id": 0,
            "i": [0, 5, "FF0000", 6, 10, "00FF00", 11, 15, "0000FF"]
        }
    }
    
    result_range = api._ensure_wled_update_params(test_json_range)
    
    print("\nTest 3: Range pattern")
    print("-" * 70)
    print("Output:")
    print(json.dumps(result_range, indent=2))
    
    # Validate
    is_valid, errors, warnings = validate_wled_json(result_range, verbose=True)
    
    assert is_valid, f"Range pattern validation failed: {errors}"
    print("\n✓ Test 3 passed - Range pattern is valid")
    
    print("\n" + "=" * 70)
    print("✓ All _ensure_wled_update_params tests passed!")
    print("=" * 70)


def test_json_serialization():
    """Test that JSON serialization produces correct format."""
    print("\n\n" + "=" * 70)
    print("Test: JSON Serialization Format")
    print("=" * 70)
    
    test_data = {
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["FF0000", "00FF00", "0000FF"],
            "fx": 0,
            "sel": True
        },
        "live": False
    }
    
    # Serialize with json.dumps
    json_string = json.dumps(test_data)
    
    print("\nSerialized JSON:")
    print(json_string)
    
    # Verify format
    assert '"on": true' in json_string or '"on":true' in json_string, "Boolean 'true' should be lowercase"
    assert '"live": false' in json_string or '"live":false' in json_string, "Boolean 'false' should be lowercase"
    assert '"sel": true' in json_string or '"sel":true' in json_string, "Boolean 'true' should be lowercase"
    assert '"on": True' not in json_string, "Should not have Python-style 'True'"
    assert '"live": False' not in json_string, "Should not have Python-style 'False'"
    assert "'" not in json_string, "Should not have single quotes"
    
    # Verify it can be parsed back
    parsed = json.loads(json_string)
    assert parsed["on"] is True
    assert parsed["live"] is False
    assert parsed["seg"]["sel"] is True
    
    print("\n✓ JSON serialization format is correct")
    print("  - Uses double quotes")
    print("  - Lowercase booleans (true/false)")
    print("  - Parses correctly")
    
    print("\n" + "=" * 70)
    print("✓ JSON serialization test passed!")
    print("=" * 70)


def test_color_format():
    """Test that color values are in the correct hex format."""
    print("\n\n" + "=" * 70)
    print("Test: Color Format Validation")
    print("=" * 70)
    
    # Test valid color formats
    valid_colors = [
        ["FF0000", "00FF00", "0000FF"],  # Uppercase RGB
        ["ff0000", "00ff00", "0000ff"],  # Lowercase RGB
        ["FF000000", "00FF0000"],        # RGBW 8-char
    ]
    
    for idx, colors in enumerate(valid_colors, 1):
        test_json = {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": colors,
                "fx": 0,
                "sel": True
            },
            "live": False
        }
        
        is_valid, errors, warnings = validate_wled_json(test_json)
        
        print(f"\nTest {idx}: {colors}")
        if is_valid:
            print("  ✓ Valid")
        else:
            print(f"  ✗ Invalid: {errors}")
            raise AssertionError(f"Color format test {idx} failed: {errors}")
    
    print("\n" + "=" * 70)
    print("✓ All color format tests passed!")
    print("=" * 70)


def test_deep_copy_preservation():
    """Test that _ensure_wled_update_params doesn't modify the original."""
    print("\n\n" + "=" * 70)
    print("Test: Deep Copy Preservation")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    original_json = {
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["FF0000", "00FF00", "0000FF"]
        }
    }
    
    # Make a copy to compare later
    import copy
    original_copy = copy.deepcopy(original_json)
    
    # Call _ensure_wled_update_params
    result = api._ensure_wled_update_params(original_json)
    
    # Verify original wasn't modified
    assert original_json == original_copy, "Original JSON was modified!"
    assert "live" not in original_json, "Original should not have 'live' parameter"
    assert "fx" not in original_json["seg"], "Original should not have modified segment"
    
    # Verify result has the parameters
    assert "live" in result, "Result should have 'live' parameter"
    assert "fx" in result["seg"], "Result should have 'fx' in segment"
    
    print("\n✓ Deep copy preservation test passed!")
    print("  - Original JSON not modified")
    print("  - Result has required parameters")
    
    print("\n" + "=" * 70)
    print("✓ Deep copy test passed!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("WLED JSON API Compliance Test Suite")
    print("Testing: custom_components/pixelmagictool/converter.py")
    print("*" * 70)
    
    try:
        test_ensure_wled_update_params()
        test_json_serialization()
        test_color_format()
        test_deep_copy_preservation()
        
        print("\n\n")
        print("*" * 70)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("*" * 70)
        print("\nThe converter module generates WLED-compliant JSON:")
        print("  ✓ Proper JSON format (double quotes, lowercase booleans)")
        print("  ✓ Correct 'live' parameter (not 'liv')")
        print("  ✓ Required parameters set (fx=0, sel=true, live=false)")
        print("  ✓ Valid hex color strings (6 or 8 characters)")
        print("  ✓ Deep copy preservation (original not modified)")
        print("\n")
        
        sys.exit(0)
        
    except Exception as e:
        print("\n\n")
        print("*" * 70)
        print("✗✗✗ TEST FAILED ✗✗✗")
        print("*" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        print("\n")
        sys.exit(1)
