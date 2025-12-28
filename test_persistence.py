#!/usr/bin/env python3
"""
Test script to verify DDP image persistence on WLED devices.

This script creates a simple test image and sends it to a WLED device
to verify that the image persists after transmission.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the custom_components path to allow importing the modules
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "pixelmagictool"))

from converter import PixelMagicToolAPI

async def test_ddp_persistence():
    """Test DDP image persistence."""
    
    # Configuration
    WLED_HOST = "192.168.1.100"  # Change to your WLED device IP
    WIDTH = 16
    HEIGHT = 16
    
    print(f"Testing DDP persistence on WLED device at {WLED_HOST}")
    print(f"Matrix size: {WIDTH}x{HEIGHT}")
    
    # Create a simple test image (red square)
    import io
    from PIL import Image
    
    # Create a red test image
    img = Image.new('RGB', (WIDTH, HEIGHT), (255, 0, 0))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # Save test image temporarily
    test_image_path = "/tmp/test_image.png"
    with open(test_image_path, 'wb') as f:
        f.write(img_bytes)
    
    try:
        # Initialize the API
        api = PixelMagicToolAPI()
        
        print("Sending test image via DDP...")
        success = await api.send_image_via_ddp(
            image_source=test_image_path,
            wled_host=WLED_HOST,
            width=WIDTH,
            height=HEIGHT,
            brightness=128,
            segment_id=0,
            timeout=10,
            keepalive_seconds=10,  # Short keepalive for testing
            keepalive_interval=1.0,
        )
        
        if success:
            print("✓ Successfully sent image via DDP!")
            print("The image should now persist on your WLED device.")
            print("Check that the red square is displayed and remains after 10 seconds.")
        else:
            print("✗ Failed to send image via DDP")
        
        # Clean up
        await api.async_close()
        
        return success
        
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

if __name__ == "__main__":
    print("DDP Persistence Test")
    print("===================")
    print()
    print("Before running this test, please:")
    print("1. Update WLED_HOST in this script to your device's IP address")
    print("2. Update WIDTH and HEIGHT to match your WLED matrix size")
    print("3. Ensure your WLED device is accessible on the network")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        # Run the actual test
        success = asyncio.run(test_ddp_persistence())
        sys.exit(0 if success else 1)
    else:
        print("To run the test, use: python test_persistence.py --run")