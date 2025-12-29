#!/usr/bin/env python3
"""
Test script for PixelMagicTool image processing features.

This script demonstrates how the new WLEDVideoSync-compatible image processing
features fix washed out images and provide advanced control over image quality.

Uses only PIL/Pillow - no OpenCV or numpy required.
"""

import asyncio
import sys
from pathlib import Path

# Add the custom component to the path for testing
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixelmagictool"))

from converter import PixelMagicToolAPI


async def test_image_processing():
    """Test the new image processing features."""
    
    api = PixelMagicToolAPI()
    
    # Test image (you'll need to provide a valid image URL or path)
    test_image = "https://httpbin.org/image/png"  # Example test image
    wled_host = "192.168.1.100"  # Replace with your WLED device IP
    
    print("Testing PixelMagicTool Image Processing Features")
    print("=" * 50)
    
    # Test 1: Default processing (with auto brightness/contrast enabled)
    print("\n1. Testing with AUTO brightness/contrast (should fix washed out images):")
    try:
        success = await api.send_image_via_ddp(
            image_source=test_image,
            wled_host=wled_host,
            width=16,
            height=16,
            brightness=255,
            keepalive_seconds=5,
            auto_bright=True,  # This is the key fix for washed out images
            gamma=0.5,  # LED-optimized gamma
            clip_hist_percent=25.0,  # Balanced auto adjustment
        )
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print("   → Auto processing should produce well-balanced colors")
    except Exception as e:
        print(f"   Result: FAILED - {e}")
    
    await asyncio.sleep(2)
    
    # Test 2: Enhanced saturation and contrast
    print("\n2. Testing with enhanced saturation and contrast:")
    try:
        success = await api.send_image_via_ddp(
            image_source=test_image,
            wled_host=wled_host,
            width=16,
            height=16,
            brightness=255,
            keepalive_seconds=5,
            auto_bright=True,
            saturation=1.3,  # 30% more saturated
            contrast=1.2,    # 20% more contrast
            gamma=0.5,
        )
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print("   → Should appear more vibrant and punchy")
    except Exception as e:
        print(f"   Result: FAILED - {e}")
    
    await asyncio.sleep(2)
    
    # Test 3: Sharpening for crisp details
    print("\n3. Testing with image sharpening:")
    try:
        success = await api.send_image_via_ddp(
            image_source=test_image,
            wled_host=wled_host,
            width=16,
            height=16,
            brightness=255,
            keepalive_seconds=5,
            auto_bright=True,
            sharpen=0.5,  # Medium sharpening
            gamma=0.5,
        )
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print("   → Should appear sharper with enhanced edges")
    except Exception as e:
        print(f"   Result: FAILED - {e}")
    
    await asyncio.sleep(2)
    
    # Test 4: Color balance adjustment
    print("\n4. Testing with color balance adjustment:")
    try:
        success = await api.send_image_via_ddp(
            image_source=test_image,
            wled_host=wled_host,
            width=16,
            height=16,
            brightness=255,
            keepalive_seconds=5,
            auto_bright=True,
            balance_r=0.9,  # Slightly reduce red
            balance_g=1.0,  # Keep green normal
            balance_b=1.1,  # Slightly enhance blue
            gamma=0.5,
        )
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print("   → Should appear slightly cooler (less red, more blue)")
    except Exception as e:
        print(f"   Result: FAILED - {e}")
    
    await asyncio.sleep(2)
    
    # Test 5: Comparison - OLD vs NEW processing
    print("\n5. Testing OLD processing (no auto, gamma=1.0):")
    try:
        success = await api.send_image_via_ddp(
            image_source=test_image,
            wled_host=wled_host,
            width=16,
            height=16,
            brightness=255,
            keepalive_seconds=5,
            auto_bright=False,  # Disable auto processing
            gamma=1.0,          # No gamma correction
        )
        print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
        if success:
            print("   → Should appear washed out (like before the fix)")
    except Exception as e:
        print(f"   Result: FAILED - {e}")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- Test 1 shows the 'auto' feature that fixes washed out images")
    print("- Test 2 demonstrates enhanced saturation and contrast")
    print("- Test 3 shows image sharpening for crisp details")
    print("- Test 4 demonstrates color balance fine-tuning")
    print("- Test 5 shows how images looked before the improvements")
    print("\nThe 'auto_bright=True' setting is the key improvement that")
    print("replicates WLEDVideoSync's automatic brightness/contrast feature!")
    
    await api.async_close()


def print_usage_examples():
    """Print Home Assistant service call examples."""
    
    print("\n" + "=" * 60)
    print("HOME ASSISTANT SERVICE CALL EXAMPLES")
    print("=" * 60)
    
    print("\n1. BASIC CALL (with auto image enhancement):")
    print("   service: pixelmagictool.send_to_wled_ddp")
    print("   data:")
    print("     image_url: 'https://example.com/image.jpg'")
    print("     wled_host: '192.168.1.100'")
    print("     width: 16")
    print("     height: 16")
    print("     auto_bright: true  # Fixes washed out images!")
    
    print("\n2. ENHANCED COLORS:")
    print("   service: pixelmagictool.send_to_wled_ddp")
    print("   data:")
    print("     image_path: '/config/www/album_art.jpg'")
    print("     wled_host: '192.168.1.100'")
    print("     width: 16")
    print("     height: 16")
    print("     auto_bright: true")
    print("     saturation: 1.3    # 30% more saturated")
    print("     contrast: 1.2      # 20% more contrast")
    print("     sharpen: 0.4       # Medium sharpening")
    
    print("\n3. COLOR BALANCE:")
    print("   service: pixelmagictool.send_to_wled_ddp") 
    print("   data:")
    print("     image_url: '{{ states.sensor.album_art.attributes.entity_picture }}'")
    print("     wled_host: '192.168.1.100'")
    print("     width: 16")
    print("     height: 16")
    print("     auto_bright: true")
    print("     balance_r: 0.9     # Slightly less red")
    print("     balance_g: 1.0     # Normal green")
    print("     balance_b: 1.1     # Slightly more blue")
    
    print("\n4. MANUAL BRIGHTNESS/CONTRAST (disable auto):")
    print("   service: pixelmagictool.send_to_wled_ddp")
    print("   data:")
    print("     image_url: 'https://example.com/bright_image.jpg'")
    print("     wled_host: '192.168.1.100'")
    print("     width: 16")
    print("     height: 16")
    print("     auto_bright: false      # Disable auto processing")
    print("     contrast: 0.8           # Reduce contrast manually")
    print("     gamma: 0.6              # Adjust gamma manually")
    

if __name__ == "__main__":
    print("PixelMagicTool Image Processing Test Script")
    print("=" * 50)
    print("This script tests the new WLEDVideoSync-compatible image processing")
    print("that fixes washed out images and provides advanced image controls.")
    print("\nIMPORTANT: Update the WLED host IP address and image URL in the script!")
    
    response = input("\nContinue with test? (y/n): ").lower().strip()
    if response == 'y':
        asyncio.run(test_image_processing())
    
    print_usage_examples()