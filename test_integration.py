"""Test the simplified WLEDVideoSync integration."""
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'pixelmagictool'))

from converter import PixelMagicToolAPI
from ddp import DDPClient

def test_api_initialization():
    """Test that API can be initialized."""
    print("Testing API initialization...")
    
    api = PixelMagicToolAPI()
    assert api is not None, "API should initialize"
    
    # Test with api_url parameter (should be ignored but not cause error)
    api_with_url = PixelMagicToolAPI(api_url="http://example.com")
    assert api_with_url is not None, "API should initialize with api_url parameter"
    
    print("✓ API initialization test passed")


def test_ddp_client():
    """Test DDP client initialization."""
    print("\nTesting DDP client initialization...")
    
    client = DDPClient("192.168.1.100")
    assert client.host == "192.168.1.100", "Host should be set correctly"
    assert client.port == 4048, "Default port should be 4048"
    
    client_custom_port = DDPClient("192.168.1.100", port=5000)
    assert client_custom_port.port == 5000, "Custom port should be set"
    
    print("✓ DDP client initialization test passed")


def test_const_values():
    """Test that constants are properly defined."""
    print("\nTesting constants...")
    
    from const import (
        DOMAIN,
        SERVICE_SEND_TO_WLED_DDP,
        CONF_WLED_HOST,
        CONF_BRIGHTNESS,
        CONF_WIDTH,
        CONF_HEIGHT,
        DEFAULT_BRIGHTNESS,
    )
    
    assert DOMAIN == "pixelmagictool", "Domain should be pixelmagictool"
    assert SERVICE_SEND_TO_WLED_DDP == "send_to_wled_ddp", "Service name should be correct"
    assert DEFAULT_BRIGHTNESS == 255, "Default brightness should be 255"
    
    print("✓ Constants test passed")


if __name__ == "__main__":
    print("Running WLEDVideoSync integration tests...\n")
    print("=" * 60)
    
    try:
        test_api_initialization()
        test_ddp_client()
        test_const_values()
        
        print("\n" + "=" * 60)
        print("✓ All integration tests passed!")
        print("=" * 60)
        print("\nThe integration is ready to use.")
        print("Use the 'pixelmagictool.send_to_wled_ddp' service to send images.")
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
