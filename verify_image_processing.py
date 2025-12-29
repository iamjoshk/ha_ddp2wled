#!/usr/bin/env python3
"""
Quick verification script for PIL-based image processing.

This script verifies that the image processing works without OpenCV/numpy.
"""

import sys
from pathlib import Path
from PIL import Image

# Add the custom component to the path for testing
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixelmagictool"))

try:
    from image_processing import ImageProcessor
    print("✅ Successfully imported ImageProcessor")
except Exception as e:
    print(f"❌ Failed to import ImageProcessor: {e}")
    sys.exit(1)

def test_image_processing():
    """Test basic image processing functionality."""
    
    # Create a simple test image (16x16 RGB)
    test_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
    print("✅ Created test image")
    
    try:
        # Test gamma correction
        gamma_result = ImageProcessor.apply_gamma_correction(test_img, 0.5)
        print("✅ Gamma correction works")
    except Exception as e:
        print(f"❌ Gamma correction failed: {e}")
        return False
    
    try:
        # Test automatic brightness/contrast
        auto_result = ImageProcessor.automatic_brightness_and_contrast(test_img, 25.0)
        print("✅ Auto brightness/contrast works")
    except Exception as e:
        print(f"❌ Auto brightness/contrast failed: {e}")
        return False
    
    try:
        # Test full processing pipeline
        result = ImageProcessor.process_image_for_led(
            test_img,
            saturation=1.2,
            brightness=1.1,
            contrast=1.1,
            sharpen=0.3,
            balance_r=1.0,
            balance_g=1.0,
            balance_b=1.0,
            gamma=0.5,
            auto_bright=True,
            clip_hist_percent=25.0,
        )
        print("✅ Full processing pipeline works")
        print(f"   Original size: {test_img.size}")
        print(f"   Result size: {result.size}")
        print(f"   Original mode: {test_img.mode}")
        print(f"   Result mode: {result.mode}")
    except Exception as e:
        print(f"❌ Full processing pipeline failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("PIL-based Image Processing Verification")
    print("=" * 40)
    
    if test_image_processing():
        print("\n🎉 All tests passed! Image processing is working correctly.")
        print("The integration should now work without OpenCV dependency issues.")
    else:
        print("\n💥 Some tests failed. There may be issues with the PIL implementation.")
        sys.exit(1)