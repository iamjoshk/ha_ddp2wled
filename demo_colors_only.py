#!/usr/bin/env python3
"""
Demonstration of the colors_only feature.
Shows size comparison between full and minimal payloads.
"""

import json
import sys

sys.path.insert(0, 'custom_components/pixelmagictool')
from converter import PixelMagicToolAPI


def main():
    """Demonstrate colors_only payload reduction."""
    print("\n" + "=" * 70)
    print("Colors-Only Mode Demonstration")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Example: 32x32 LED matrix (1024 pixels)
    # Simulating a typical album art display with 4 color zones
    colors = ["FF0000"] * 256 + ["00FF00"] * 256 + ["0000FF"] * 256 + ["FFFF00"] * 256  # 1024 total pixels
    
    # Create full WLED payload (what gets sent normally)
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
    
    # Create minimal colors-only payload
    minimal_payload = api.create_colors_only_payload(full_payload)
    
    # Calculate sizes
    full_size = len(json.dumps(full_payload))
    minimal_size = len(json.dumps(minimal_payload))
    reduction = full_size - minimal_size
    reduction_percent = (1 - minimal_size / full_size) * 100
    
    print("\n" + "-" * 70)
    print("Example: 32x32 LED Matrix (1024 pixels)")
    print("-" * 70)
    
    print("\nFull Payload Structure:")
    print(json.dumps(full_payload, indent=2)[:300] + "\n  ... (truncated)")
    print(f"\nFull Payload Size: {full_size:,} bytes")
    
    print("\n" + "-" * 70)
    
    print("\nMinimal Payload Structure (colors_only=True):")
    print(json.dumps(minimal_payload, indent=2)[:300] + "\n  ... (truncated)")
    print(f"\nMinimal Payload Size: {minimal_size:,} bytes")
    
    print("\n" + "-" * 70)
    print(f"Size Reduction: {reduction} bytes ({reduction_percent:.1f}%)")
    print("-" * 70)
    
    print("\nWhat's removed in colors_only mode:")
    print("  ✓ 'on' field (true/false)")
    print("  ✓ 'bri' field (brightness 0-255)")
    print("  ✓ 'live' field (false)")
    print("  ✓ 'seg.fx' field (effect ID)")
    print("  ✓ 'seg.sel' field (segment selection)")
    
    print("\nWhat's kept in colors_only mode:")
    print("  ✓ 'seg.id' (segment ID - needed for targeting)")
    print("  ✓ 'seg.i' (color array - the actual pixel data)")
    
    print("\n" + "=" * 70)
    print("When to use colors_only mode:")
    print("=" * 70)
    print("✓ When payload size is critical")
    print("✓ When WLED device already has correct settings (brightness, effect, etc.)")
    print("✓ When frequently updating the same segment")
    print("✓ For high-frequency updates (reduces bandwidth)")
    print("\n" + "=" * 70)
    print()


if __name__ == "__main__":
    main()
