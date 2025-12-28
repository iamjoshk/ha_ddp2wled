"""Test DDP fix for WLED realtime mode reversion."""
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, call
import io

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from pixelmagictool.converter import PixelMagicToolAPI


async def test_ddp_prepares_wled_device():
    """Test that send_image_via_ddp prepares WLED device before sending DDP packets."""
    print("Testing DDP preparation sequence...")
    
    # Create a simple 2x2 test image (red, green, blue, white)
    from PIL import Image
    img = Image.new('RGB', (2, 2))
    pixels = img.load()
    pixels[0, 0] = (255, 0, 0)    # Red
    pixels[1, 0] = (0, 255, 0)    # Green
    pixels[0, 1] = (0, 0, 255)    # Blue
    pixels[1, 1] = (255, 255, 255)  # White
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Mock aiohttp session
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=img_bytes.getvalue())
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    mock_prepare_response = AsyncMock()
    mock_prepare_response.status = 200
    mock_prepare_response.__aenter__ = AsyncMock(return_value=mock_prepare_response)
    mock_prepare_response.__aexit__ = AsyncMock()
    
    mock_session = AsyncMock()
    
    # Track call order
    call_order = []
    
    def track_get(*args, **kwargs):
        call_order.append(('get', args[0]))
        mock_response.raise_for_status = MagicMock()
        return mock_response
    
    def track_post(*args, **kwargs):
        call_order.append(('post', args[0], kwargs.get('json')))
        return mock_prepare_response
    
    mock_session.get = track_get
    mock_session.post = track_post
    
    # Mock DDPClient
    with patch('pixelmagictool.converter.DDPClient') as mock_ddp_class:
        mock_ddp_instance = AsyncMock()
        mock_ddp_instance.send_image = AsyncMock(return_value=True)
        mock_ddp_class.return_value = mock_ddp_instance
        
        # Create API and send image
        api = PixelMagicToolAPI()
        success = await api.send_image_via_ddp(
            image_url="http://example.com/test.png",
            wled_host="192.168.1.100",
            width=2,
            height=2,
            brightness=255,
            timeout=10,
            session=mock_session,
        )
        
        # Verify success
        assert success, "DDP send should succeed"
        
        # Verify call order
        assert len(call_order) >= 2, f"Expected at least 2 calls, got {len(call_order)}"
        
        # First call should be POST to prepare WLED
        first_call = call_order[0]
        assert first_call[0] == 'post', f"First call should be POST, got {first_call[0]}"
        assert 'json/state' in first_call[1], f"First POST should be to /json/state, got {first_call[1]}"
        
        # Check the preparation payload
        prep_payload = first_call[2]
        assert prep_payload is not None, "Preparation payload should not be None"
        assert prep_payload.get('live') is False, "live should be False in preparation"
        assert 'seg' in prep_payload, "seg should be in preparation payload"
        assert prep_payload['seg'].get('fx') == 0, "fx should be 0 (Solid effect)"
        assert prep_payload['seg'].get('sel') is True, "sel should be True"
        
        print(f"  ✓ Preparation payload correct: {prep_payload}")
        
        # Second call should be GET to download image
        second_call = call_order[1]
        assert second_call[0] == 'get', f"Second call should be GET, got {second_call[0]}"
        assert 'example.com' in second_call[1], f"Second GET should be to image URL"
        
        print(f"  ✓ Call order correct: POST /json/state, then GET image")
        
        # Verify DDP client was called
        mock_ddp_instance.send_image.assert_called_once()
        call_args = mock_ddp_instance.send_image.call_args
        
        # Check RGB data size (2x2 image = 4 pixels * 3 bytes = 12 bytes)
        rgb_data = call_args[0][0]
        assert len(rgb_data) == 12, f"RGB data should be 12 bytes, got {len(rgb_data)}"
        
        # Check dimensions
        assert call_args[0][1] == 2, "Width should be 2"
        assert call_args[0][2] == 2, "Height should be 2"
        
        print(f"  ✓ DDP client called with correct parameters")
    
    print("✓ DDP preparation test passed\n")


async def test_ddp_handles_preparation_failure():
    """Test that DDP continues even if WLED preparation fails."""
    print("Testing DDP graceful handling of preparation failure...")
    
    # Create a simple 2x2 test image
    from PIL import Image
    img = Image.new('RGB', (2, 2), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Mock aiohttp session
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.read = AsyncMock(return_value=img_bytes.getvalue())
    mock_response.raise_for_status = MagicMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # Mock preparation response that fails
    mock_prepare_response = AsyncMock()
    mock_prepare_response.status = 500  # Server error
    mock_prepare_response.__aenter__ = AsyncMock(return_value=mock_prepare_response)
    mock_prepare_response.__aexit__ = AsyncMock()
    
    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.post = MagicMock(return_value=mock_prepare_response)
    
    # Mock DDPClient
    with patch('pixelmagictool.converter.DDPClient') as mock_ddp_class:
        mock_ddp_instance = AsyncMock()
        mock_ddp_instance.send_image = AsyncMock(return_value=True)
        mock_ddp_class.return_value = mock_ddp_instance
        
        # Create API and send image - should succeed despite prep failure
        api = PixelMagicToolAPI()
        success = await api.send_image_via_ddp(
            image_url="http://example.com/test.png",
            wled_host="192.168.1.100",
            width=2,
            height=2,
            brightness=255,
            timeout=10,
            session=mock_session,
        )
        
        # Should still succeed
        assert success, "DDP send should succeed even if preparation fails"
        
        # DDP should still have been called
        mock_ddp_instance.send_image.assert_called_once()
        
        print("  ✓ DDP continues despite preparation failure")
    
    print("✓ Graceful failure handling test passed\n")


if __name__ == "__main__":
    print("Running DDP fix tests...\n")
    print("=" * 60)
    
    try:
        asyncio.run(test_ddp_prepares_wled_device())
        asyncio.run(test_ddp_handles_preparation_failure())
        
        print("=" * 60)
        print("✓ All DDP fix tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
