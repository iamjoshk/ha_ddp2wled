#!/usr/bin/env python3
"""
Validation script to ensure JSON output uses correct format.

This script verifies that:
1. String values and keys use double quotes (")
2. Boolean values are lowercase (true, false)
3. All JSON is properly formatted according to JSON specification

Run this script to validate JSON formatting in the codebase.
"""

import json
import re


def validate_json_format(json_string: str) -> tuple[bool, list[str]]:
    """
    Validate that a JSON string uses correct formatting.
    
    Args:
        json_string: The JSON string to validate
        
    Returns:
        Tuple of (is_valid, list of issues found)
    """
    issues = []
    
    # Check 1: Verify it's valid JSON first
    try:
        parsed = json.loads(json_string)
    except json.JSONDecodeError as e:
        issues.append(f"Invalid JSON: {e}")
        return False, issues
    
    # Check 2: Verify no single quotes are used for strings
    # Since json.loads() already validated the JSON, we can trust it's valid
    # Just check for suspicious patterns (single quotes outside strings)
    # Note: This is a simple heuristic check
    if "'" in json_string:
        # Count single quotes - in valid JSON they should only appear within double-quoted strings
        # This is a simplified check; the main validation is json.loads() above
        single_quote_count = json_string.count("'")
        if single_quote_count > 0:
            # This is informational - single quotes might be in string values
            pass  # Not necessarily an error
    
    # Check 3: Verify boolean values are lowercase
    # Check for uppercase True/False (these wouldn't be in valid JSON but check anyway)
    if 'True' in json_string or 'False' in json_string:
        issues.append("Found uppercase True/False (should be lowercase true/false)")
    
    # Check 4: Verify keys use double quotes
    # This is inherently checked by json.loads() which already validated the JSON
    # Any single-quoted keys would have caused json.loads() to fail above
    
    is_valid = len(issues) == 0
    return is_valid, issues


def test_wled_json_format():
    """Test WLED JSON format examples."""
    print("=" * 70)
    print("WLED JSON Format Validation")
    print("=" * 70)
    print()
    
    # Test Case 1: Correct format (from requirement)
    correct_json = json.dumps({
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["060505", "050706", "0c100f"],
            "fx": 0,
            "sel": True
        },
        "live": False
    })
    
    print("Test 1: Correct WLED JSON format")
    print("-" * 70)
    is_valid, issues = validate_json_format(correct_json)
    print(f"Valid: {is_valid}")
    if issues:
        print(f"Issues: {issues}")
    else:
        print("✓ All checks passed")
    print()
    print("Sample output:")
    print(json.dumps(json.loads(correct_json), indent=2))
    print()
    
    # Test Case 2: Incorrect format with single quotes (simulated)
    incorrect_json_example = "{'on': True, 'bri': 128}"
    print("Test 2: Incorrect format (Python dict repr)")
    print("-" * 70)
    is_valid, issues = validate_json_format(incorrect_json_example)
    print(f"Valid: {is_valid}")
    print(f"Issues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
    print()
    
    # Test Case 3: Verify Python's json.dumps always produces correct format
    print("Test 3: Python json.dumps() output format")
    print("-" * 70)
    test_data = {
        "string": "value",
        "boolean_true": True,
        "boolean_false": False,
        "number": 123,
        "list": ["item1", "item2"],
        "nested": {"key": "value"}
    }
    output = json.dumps(test_data, indent=2)
    is_valid, issues = validate_json_format(output)
    print(f"Valid: {is_valid}")
    if issues:
        print(f"Issues: {issues}")
    else:
        print("✓ json.dumps() produces correct format")
    print()
    print("Format verification:")
    print(f"  - Uses double quotes: {'\"string\"' in output}")
    print(f"  - Boolean true is lowercase: {'true' in output and 'True' not in output}")
    print(f"  - Boolean false is lowercase: {'false' in output and 'False' not in output}")
    print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("✓ Python's json.dumps() correctly uses:")
    print("  - Double quotes (\") for strings and keys")
    print("  - Lowercase true/false for booleans")
    print("  - Standard JSON formatting")
    print()
    print("⚠ IMPORTANT: Always use json.dumps() or json parameter in aiohttp")
    print("  - Never use str() or repr() for JSON output")
    print("  - Never manually construct JSON strings")
    print()


if __name__ == "__main__":
    test_wled_json_format()
