#!/usr/bin/env python3
"""
Validation script for WLED JSON API compliance.

This script verifies that the generated JSON complies with the official
WLED JSON API specification from https://kno.wled.ge/interfaces/json-api/

Requirements being validated:
1. JSON format correctness (proper quotes, booleans, etc.)
2. Color format in seg.i array (hex strings, 6 or 8 characters)
3. Required WLED parameters for device updates
4. Array pattern format validation (individual, index, range)
"""

import json
import re
from typing import Any, Dict, List, Tuple


def validate_json_structure(wled_json: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate basic JSON structure compliance with WLED API.
    
    Args:
        wled_json: The WLED JSON payload to validate
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    # Check for required top-level parameters
    if "on" in wled_json and not isinstance(wled_json["on"], bool):
        issues.append(f"'on' must be boolean, got {type(wled_json['on'])}")
    
    if "bri" in wled_json:
        bri = wled_json["bri"]
        if not isinstance(bri, int) or not (0 <= bri <= 255):
            issues.append(f"'bri' must be integer 0-255, got {bri}")
    
    if "live" in wled_json and not isinstance(wled_json["live"], bool):
        issues.append(f"'live' must be boolean, got {type(wled_json['live'])}")
    
    return len(issues) == 0, issues


def validate_hex_color(color: Any, allow_rgbw: bool = True) -> Tuple[bool, str]:
    """
    Validate that a color is a proper hex string.
    
    WLED spec allows:
    - 6 character RGB: "RRGGBB" or "rrggbb"
    - 8 character RGBW: "RRGGBBWW" or "rrggbbww" (if allow_rgbw=True)
    
    Args:
        color: The color value to validate
        allow_rgbw: Whether to allow 8-character RGBW format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(color, str):
        return False, f"Color must be string, got {type(color)}"
    
    # Check length
    valid_lengths = [6]
    if allow_rgbw:
        valid_lengths.append(8)
    
    if len(color) not in valid_lengths:
        return False, f"Color must be {' or '.join(map(str, valid_lengths))} characters, got {len(color)}"
    
    # Check that all characters are valid hex
    if not re.match(r'^[0-9A-Fa-f]+$', color):
        return False, f"Color must be valid hex string, got '{color}'"
    
    return True, ""


def validate_segment_colors(seg_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the seg.i array color format.
    
    The WLED API supports three patterns:
    1. Individual: ["FF0000", "00FF00", "0000FF"]
    2. Index: [0, "FF0000", 1, "00FF00", 2, "0000FF"]
    3. Range: [0, 5, "FF0000", 6, 10, "00FF00"]
    
    Args:
        seg_data: The segment data dictionary
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    if "i" not in seg_data:
        # Having no 'i' is valid - segment might use other color settings
        return True, []
    
    led_data = seg_data["i"]
    
    if not isinstance(led_data, list):
        issues.append(f"seg.i must be array, got {type(led_data)}")
        return False, issues
    
    if len(led_data) == 0:
        # Empty array is valid
        return True, []
    
    # Detect pattern type and validate accordingly
    pattern_type = _detect_pattern_type(led_data)
    
    if pattern_type == "individual":
        # All elements should be hex color strings
        for idx, color in enumerate(led_data):
            is_valid, error = validate_hex_color(color)
            if not is_valid:
                issues.append(f"seg.i[{idx}] (individual pattern): {error}")
    
    elif pattern_type == "index":
        # Format: [index, color, index, color, ...]
        if len(led_data) % 2 != 0:
            issues.append(f"seg.i (index pattern) must have even number of elements, got {len(led_data)}")
        else:
            for i in range(0, len(led_data), 2):
                # Check index
                if not isinstance(led_data[i], int) or led_data[i] < 0:
                    issues.append(f"seg.i[{i}] (index pattern): LED index must be non-negative integer, got {led_data[i]}")
                # Check color
                if i + 1 < len(led_data):
                    is_valid, error = validate_hex_color(led_data[i + 1])
                    if not is_valid:
                        issues.append(f"seg.i[{i + 1}] (index pattern): {error}")
    
    elif pattern_type == "range":
        # Format: [start, end, color, start, end, color, ...]
        if len(led_data) % 3 != 0:
            issues.append(f"seg.i (range pattern) must have length divisible by 3, got {len(led_data)}")
        else:
            for i in range(0, len(led_data), 3):
                # Check start index
                if not isinstance(led_data[i], int) or led_data[i] < 0:
                    issues.append(f"seg.i[{i}] (range pattern): start index must be non-negative integer, got {led_data[i]}")
                # Check end index
                if i + 1 < len(led_data):
                    if not isinstance(led_data[i + 1], int) or led_data[i + 1] < 0:
                        issues.append(f"seg.i[{i + 1}] (range pattern): end index must be non-negative integer, got {led_data[i + 1]}")
                    elif isinstance(led_data[i], int) and led_data[i + 1] < led_data[i]:
                        issues.append(f"seg.i[{i}:{i + 2}] (range pattern): end index must be >= start index")
                # Check color
                if i + 2 < len(led_data):
                    is_valid, error = validate_hex_color(led_data[i + 2])
                    if not is_valid:
                        issues.append(f"seg.i[{i + 2}] (range pattern): {error}")
    
    else:
        issues.append(f"Could not determine pattern type for seg.i array")
    
    return len(issues) == 0, issues


def _detect_pattern_type(led_data: List[Any]) -> str:
    """
    Detect which pattern type is used in the seg.i array.
    
    Returns:
        "individual", "index", "range", or "unknown"
    """
    if len(led_data) == 0:
        return "individual"
    
    # Check first few elements to determine pattern
    if isinstance(led_data[0], str):
        # Individual pattern - all strings
        return "individual"
    elif isinstance(led_data[0], int):
        # Could be index or range pattern
        if len(led_data) >= 3:
            # Check if pattern looks like range (int, int, str, ...)
            if (isinstance(led_data[0], int) and 
                isinstance(led_data[1], int) and 
                len(led_data) > 2 and isinstance(led_data[2], str)):
                return "range"
        # Otherwise assume index pattern (int, str, int, str, ...)
        return "index"
    
    return "unknown"


def validate_segment_params(seg_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate segment parameters required for proper device updates.
    
    Args:
        seg_data: The segment data dictionary
        
    Returns:
        Tuple of (is_valid, list of errors, list of warnings)
    """
    errors = []
    warnings = []
    
    # Check segment ID
    if "id" in seg_data:
        if not isinstance(seg_data["id"], int) or seg_data["id"] < 0:
            errors.append(f"seg.id must be non-negative integer, got {seg_data['id']}")
    
    # Check effect setting (fx) - should be 0 for individual LED control
    if "i" in seg_data:  # Only check if using individual LED control
        if "fx" not in seg_data:
            warnings.append("seg.fx not set - should be 0 (Solid) for individual LED control")
        elif seg_data["fx"] != 0:
            warnings.append(f"seg.fx is {seg_data['fx']} - should be 0 (Solid) for individual LED control")
    
    # Check selection flag
    if "sel" not in seg_data:
        warnings.append("seg.sel not set - should be true to mark segment as active")
    elif seg_data["sel"] is not True:
        warnings.append(f"seg.sel is {seg_data['sel']} - should be true to mark segment as active")
    
    return len(errors) == 0, errors, warnings


def validate_wled_json(wled_json: Dict[str, Any], verbose: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Comprehensive validation of WLED JSON API compliance.
    
    Args:
        wled_json: The WLED JSON payload to validate
        verbose: Whether to include warnings in output
        
    Returns:
        Tuple of (is_valid, list of errors, list of warnings)
    """
    all_errors = []
    all_warnings = []
    
    # 1. Validate JSON structure
    is_valid, issues = validate_json_structure(wled_json)
    if not is_valid:
        all_errors.extend([f"Structure: {issue}" for issue in issues])
    
    # 2. Validate segment data
    if "seg" in wled_json:
        seg_data = wled_json["seg"]
        
        # Handle both single segment (dict) and multiple segments (list)
        segments_to_check = []
        if isinstance(seg_data, dict):
            segments_to_check = [seg_data]
        elif isinstance(seg_data, list):
            segments_to_check = seg_data
        else:
            all_errors.append(f"Structure: 'seg' must be dict or list, got {type(seg_data)}")
            segments_to_check = []
        
        # Validate each segment
        for idx, seg in enumerate(segments_to_check):
            if not isinstance(seg, dict):
                all_errors.append(f"Segment {idx}: must be dict, got {type(seg)}")
                continue
            
            # Validate colors
            is_valid, issues = validate_segment_colors(seg)
            if not is_valid:
                all_errors.extend([f"Segment {idx}: {issue}" for issue in issues])
            
            # Validate parameters
            is_valid, errors, warnings = validate_segment_params(seg)
            if not is_valid:
                all_errors.extend([f"Segment {idx}: {issue}" for issue in errors])
            if warnings:
                all_warnings.extend([f"Segment {idx}: {issue}" for issue in warnings])
    
    # 3. Check for device update parameters
    if "live" in wled_json:
        if wled_json["live"] is not False:
            all_warnings.append(f"'live' is {wled_json['live']} - should be false for immediate updates")
    else:
        if "seg" in wled_json:
            all_warnings.append("'live' not set - should be false for immediate device updates")
    
    return len(all_errors) == 0, all_errors, all_warnings


def test_wled_compliance():
    """Run comprehensive tests for WLED JSON API compliance."""
    print("=" * 70)
    print("WLED JSON API Compliance Validation")
    print("=" * 70)
    print()
    
    test_cases = []
    
    # Test 1: Valid WLED JSON with individual pattern
    test_cases.append({
        "name": "Valid individual pattern",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["FF0000", "00FF00", "0000FF"],
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": True
    })
    
    # Test 2: Valid WLED JSON with range pattern
    test_cases.append({
        "name": "Valid range pattern",
        "json": {
            "on": True,
            "bri": 255,
            "seg": {
                "id": 0,
                "i": [0, 5, "FF0000", 6, 10, "00FF00", 11, 15, "0000FF"],
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": True
    })
    
    # Test 3: Valid WLED JSON with index pattern
    test_cases.append({
        "name": "Valid index pattern",
        "json": {
            "on": True,
            "bri": 200,
            "seg": {
                "id": 0,
                "i": [0, "FF0000", 5, "00FF00", 10, "0000FF"],
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": True
    })
    
    # Test 4: Lowercase hex colors (should pass)
    test_cases.append({
        "name": "Lowercase hex colors",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["ff0000", "00ff00", "0000ff"],
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": True
    })
    
    # Test 5: RGBW format (8 characters)
    test_cases.append({
        "name": "RGBW 8-character hex",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["FF000000", "00FF0000", "0000FF00"],
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": True
    })
    
    # Test 6: Invalid hex color (wrong length)
    test_cases.append({
        "name": "Invalid hex color length",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["FF00", "00FF00"],  # Wrong length
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": False
    })
    
    # Test 7: Invalid hex color (non-hex characters)
    test_cases.append({
        "name": "Non-hex characters",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["GGHHII", "00FF00"],  # Invalid hex
                "fx": 0,
                "sel": True
            },
            "live": False
        },
        "should_pass": False
    })
    
    # Test 8: Missing required parameters (warnings)
    test_cases.append({
        "name": "Missing fx and sel (warnings)",
        "json": {
            "on": True,
            "bri": 128,
            "seg": {
                "id": 0,
                "i": ["FF0000", "00FF00", "0000FF"]
            },
            "live": False
        },
        "should_pass": True  # Valid but with warnings
    })
    
    # Run tests
    passed = 0
    failed = 0
    
    for idx, test in enumerate(test_cases, 1):
        print(f"Test {idx}: {test['name']}")
        print("-" * 70)
        
        is_valid, errors, warnings = validate_wled_json(test["json"], verbose=True)
        
        if is_valid and test["should_pass"]:
            print("✓ PASS - JSON is compliant")
            passed += 1
        elif not is_valid and not test["should_pass"]:
            print("✓ PASS - Correctly detected issues")
            passed += 1
        else:
            print(f"✗ FAIL - Expected {'pass' if test['should_pass'] else 'fail'}")
            failed += 1
        
        if errors:
            print(f"\nErrors found ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        else:
            print("No errors found")
        
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  ⚠ {warning}")
        
        # Show JSON sample
        print("\nJSON:")
        print(json.dumps(test["json"], indent=2))
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = test_wled_compliance()
    exit(0 if success else 1)
