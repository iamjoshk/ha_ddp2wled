#!/usr/bin/env python3
"""
Test image validation in DDP and convert_image functions.

This test validates that the image download and validation works correctly
for both the convert_image and send_image_via_ddp methods.
"""

import asyncio
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

# Import the converter - need to handle relative imports
sys.path.insert(0, 'custom_components')
from pixelmagictool.converter import PixelMagicToolAPI


async def test_ddp_empty_image_data():
    """Test that send_image_via_ddp rejects empty image data."""
    print("=" * 70)
    print("Test: DDP Empty Image Data Validation")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Mock the session to return empty data
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.read = AsyncMock(return_value=b"")  # Empty data
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.post = MagicMock(return_value=mock_response)
    
    try:
        await api.send_image_via_ddp(
            image_url="http://example.com/test.jpg",
            wled_host="192.168.1.100",
            width=16,
            height=16,
            session=mock_session,
        )
        print("✗ Test failed - Should have raised ValueError for empty data")
        return False
    except ValueError as e:
        if "empty" in str(e).lower():
            print(f"✓ Test passed - Correctly rejected empty data: {e}")
            return True
        else:
            print(f"✗ Test failed - Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"✗ Test failed - Unexpected exception: {e}")
        return False


async def test_ddp_invalid_image_data():
    """Test that send_image_via_ddp rejects invalid image data."""
    print("\n" + "=" * 70)
    print("Test: DDP Invalid Image Data Validation")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Mock the session to return invalid data (not an image)
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.read = AsyncMock(return_value=b"This is not an image")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.post = MagicMock(return_value=mock_response)
    
    try:
        await api.send_image_via_ddp(
            image_url="http://example.com/test.jpg",
            wled_host="192.168.1.100",
            width=16,
            height=16,
            session=mock_session,
        )
        print("✗ Test failed - Should have raised ValueError for invalid image")
        return False
    except ValueError as e:
        if "open image" in str(e).lower():
            print(f"✓ Test passed - Correctly rejected invalid image data: {e}")
            return True
        else:
            print(f"✗ Test failed - Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"✗ Test failed - Unexpected exception: {e}")
        return False


async def test_ddp_valid_image_data():
    """Test that send_image_via_ddp accepts valid image data."""
    print("\n" + "=" * 70)
    print("Test: DDP Valid Image Data")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Create a valid test image
    test_img = Image.new('RGB', (32, 32), color='red')
    img_bytes = io.BytesIO()
    test_img.save(img_bytes, format='PNG')
    valid_image_data = img_bytes.getvalue()
    
    # Mock the session
    mock_session = MagicMock()
    
    # Mock GET response (image download)
    mock_get_response = AsyncMock()
    mock_get_response.raise_for_status = MagicMock()
    mock_get_response.read = AsyncMock(return_value=valid_image_data)
    mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
    mock_get_response.__aexit__ = AsyncMock(return_value=None)
    
    # Mock POST response (WLED preparation)
    mock_post_response = AsyncMock()
    mock_post_response.status = 200
    mock_post_response.__aenter__ = AsyncMock(return_value=mock_post_response)
    mock_post_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = MagicMock(return_value=mock_get_response)
    mock_session.post = MagicMock(return_value=mock_post_response)
    
    # Mock the DDPClient
    with patch('pixelmagictool.converter.DDPClient') as mock_ddp:
        mock_ddp_instance = MagicMock()
        mock_ddp_instance.send_image = AsyncMock(return_value=True)
        mock_ddp.return_value = mock_ddp_instance
        
        try:
            result = await api.send_image_via_ddp(
                image_url="http://example.com/test.jpg",
                wled_host="192.168.1.100",
                width=16,
                height=16,
                session=mock_session,
            )
            if result:
                print("✓ Test passed - Valid image processed successfully")
                return True
            else:
                print("✗ Test failed - Processing returned False")
                return False
        except Exception as e:
            print(f"✗ Test failed - Unexpected exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_convert_image_empty_data():
    """Test that convert_image rejects empty image data."""
    print("\n" + "=" * 70)
    print("Test: Convert Image Empty Data Validation")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Mock the session to return empty data
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.read = AsyncMock(return_value=b"")  # Empty data
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = MagicMock(return_value=mock_response)
    
    try:
        await api.convert_image(
            image_url="http://example.com/test.jpg",
            session=mock_session,
        )
        print("✗ Test failed - Should have raised ValueError for empty data")
        return False
    except ValueError as e:
        if "empty" in str(e).lower():
            print(f"✓ Test passed - Correctly rejected empty data: {e}")
            return True
        else:
            print(f"✗ Test failed - Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"✗ Test failed - Unexpected exception: {e}")
        return False


async def test_convert_image_invalid_data():
    """Test that convert_image rejects invalid image data."""
    print("\n" + "=" * 70)
    print("Test: Convert Image Invalid Data Validation")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Mock the session to return invalid data
    mock_session = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.read = AsyncMock(return_value=b"Not an image")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session.get = MagicMock(return_value=mock_response)
    
    try:
        await api.convert_image(
            image_url="http://example.com/test.jpg",
            session=mock_session,
        )
        print("✗ Test failed - Should have raised ValueError for invalid image")
        return False
    except ValueError as e:
        if "valid image" in str(e).lower():
            print(f"✓ Test passed - Correctly rejected invalid image: {e}")
            return True
        else:
            print(f"✗ Test failed - Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"✗ Test failed - Unexpected exception: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("\n")
    print("*" * 70)
    print("Image Validation Test Suite")
    print("Testing: custom_components/pixelmagictool/converter.py")
    print("*" * 70)
    print("\n")
    
    results = []
    
    # Run DDP tests
    results.append(await test_ddp_empty_image_data())
    results.append(await test_ddp_invalid_image_data())
    results.append(await test_ddp_valid_image_data())
    
    # Run convert_image tests
    results.append(await test_convert_image_empty_data())
    results.append(await test_convert_image_invalid_data())
    
    print("\n\n")
    print("*" * 70)
    
    if all(results):
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("*" * 70)
        print("\nImage validation works correctly:")
        print("  ✓ Empty image data is rejected")
        print("  ✓ Invalid image data is rejected")
        print("  ✓ Valid images are processed successfully")
        print("  ✓ Clear error messages for failures")
        print("\n")
        return 0
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("*" * 70)
        failed_count = len([r for r in results if not r])
        print(f"\n{failed_count} out of {len(results)} tests failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
