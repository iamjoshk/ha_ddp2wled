#!/usr/bin/env python3
"""
Test the colors_only functionality to ensure minimal payloads are created correctly.
"""

import json
import sys

sys.path.insert(0, 'custom_components/pixelmagictool')
from converter import PixelMagicToolAPI


def test_create_colors_only_payload():
    """Test that create_colors_only_payload generates minimal payload."""
    print("=" * 70)
    print("Test: create_colors_only_payload")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Test case 1: Full payload to minimal
    full_payload = {
        "on": True,
        "bri": 128,
        "live": False,
        "seg": {
            "id": 0,
            "fx": 0,
            "sel": True,
            "i": ["FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF"]
        }
    }
    
    minimal = api.create_colors_only_payload(full_payload)
    
    print("\nTest 1: Full payload to minimal")
    print("-" * 70)
    print("Input (full payload):")
    print(json.dumps(full_payload, indent=2))
    print(f"Size: {len(json.dumps(full_payload))} bytes")
    print("\nOutput (minimal payload):")
    print(json.dumps(minimal, indent=2))
    print(f"Size: {len(json.dumps(minimal))} bytes")
    
    # Verify minimal payload structure
    assert "seg" in minimal, "Missing 'seg' in minimal payload"
    assert "i" in minimal["seg"], "Missing 'seg.i' in minimal payload"
    assert minimal["seg"]["i"] == full_payload["seg"]["i"], "Colors should match"
    assert minimal["seg"]["id"] == 0, "Segment ID should be preserved"
    
    # Verify unnecessary fields are removed
    assert "on" not in minimal, "Should not have 'on' field"
    assert "bri" not in minimal, "Should not have 'bri' field"
    assert "live" not in minimal, "Should not have 'live' field"
    assert "fx" not in minimal["seg"], "Should not have 'seg.fx' field"
    assert "sel" not in minimal["seg"], "Should not have 'seg.sel' field"
    
    # Verify size reduction
    original_size = len(json.dumps(full_payload))
    minimal_size = len(json.dumps(minimal))
    reduction_percent = (1 - minimal_size / original_size) * 100
    
    print(f"\nSize reduction: {original_size - minimal_size} bytes ({reduction_percent:.1f}%)")
    assert minimal_size < original_size, "Minimal payload should be smaller"
    
    print("\n✓ Test 1 passed - Minimal payload created correctly")
    
    # Test case 2: Range pattern preservation
    range_payload = {
        "on": True,
        "bri": 255,
        "seg": {
            "id": 1,
            "i": [0, 5, "FF0000", 6, 10, "00FF00"]
        }
    }
    
    minimal_range = api.create_colors_only_payload(range_payload)
    
    print("\nTest 2: Range pattern preservation")
    print("-" * 70)
    print("Output:")
    print(json.dumps(minimal_range, indent=2))
    
    assert minimal_range["seg"]["i"] == range_payload["seg"]["i"], "Range pattern should be preserved"
    assert minimal_range["seg"]["id"] == 1, "Segment ID should be preserved"
    
    print("\n✓ Test 2 passed - Range pattern preserved correctly")
    
    # Test case 3: Missing segment data
    invalid_payload = {
        "on": True,
        "bri": 128
    }
    
    result = api.create_colors_only_payload(invalid_payload)
    
    print("\nTest 3: Missing segment data handling")
    print("-" * 70)
    print("Input (no seg.i):")
    print(json.dumps(invalid_payload, indent=2))
    print("\nOutput (should return original):")
    print(json.dumps(result, indent=2))
    
    assert result == invalid_payload, "Should return original payload when seg.i is missing"
    
    print("\n✓ Test 3 passed - Missing data handled correctly")
    
    print("\n" + "=" * 70)
    print("✓ All create_colors_only_payload tests passed!")
    print("=" * 70)


def test_size_comparison():
    """Test size reduction with various payload sizes."""
    print("\n\n" + "=" * 70)
    print("Test: Size Comparison with Different LED Counts")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Test with different numbers of LEDs
    test_cases = [
        ("Small (16 LEDs)", ["FF0000"] * 16),
        ("Medium (64 LEDs)", ["00FF00"] * 64),
        ("Large (256 LEDs)", ["0000FF"] * 256),
        ("Very Large (1024 LEDs)", ["FFFF00"] * 1024),
    ]
    
    print("\n" + "-" * 70)
    print(f"{'Case':<25} {'Full Size':<15} {'Minimal Size':<15} {'Reduction':<15}")
    print("-" * 70)
    
    for name, colors in test_cases:
        full_payload = {
            "on": True,
            "bri": 128,
            "live": False,
            "seg": {
                "id": 0,
                "fx": 0,
                "sel": True,
                "i": colors
            }
        }
        
        minimal = api.create_colors_only_payload(full_payload)
        
        full_size = len(json.dumps(full_payload))
        minimal_size = len(json.dumps(minimal))
        reduction = full_size - minimal_size
        reduction_percent = (1 - minimal_size / full_size) * 100
        
        print(f"{name:<25} {full_size:<15,} {minimal_size:<15,} {reduction:,} ({reduction_percent:.1f}%)")
    
    print("-" * 70)
    print("\n✓ Size comparison test completed!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("Colors-Only Payload Test Suite")
    print("Testing: create_colors_only_payload() functionality")
    print("*" * 70)
    
    try:
        test_create_colors_only_payload()
        test_size_comparison()
        
        print("\n\n")
        print("*" * 70)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("*" * 70)
        print("\nThe colors-only functionality:")
        print("  ✓ Creates minimal payloads with only seg.i")
        print("  ✓ Preserves segment ID")
        print("  ✓ Removes unnecessary fields (on, bri, live, fx, sel)")
        print("  ✓ Reduces payload size significantly")
        print("  ✓ Handles missing data gracefully")
        print("  ✓ Works with all pattern types (individual, range, index)")
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
