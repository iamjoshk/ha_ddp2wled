"""Test DDP default behavior - verify prepare_device defaults to False."""
import sys
import os
import inspect

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'pixelmagictool'))

from ddp import DDPClient


def test_send_image_default():
    """Test that send_image has prepare_device=False by default."""
    print("Testing send_image default parameter...")
    
    client = DDPClient("127.0.0.1")
    sig = inspect.signature(client.send_image)
    
    # Check that prepare_device parameter exists and has default value False
    assert 'prepare_device' in sig.parameters, "prepare_device parameter should exist"
    
    param = sig.parameters['prepare_device']
    assert param.default is False, f"prepare_device should default to False, got {param.default}"
    
    print("✓ send_image defaults to prepare_device=False")


def test_send_rgb_data_default():
    """Test that send_rgb_data has prepare_device=False by default."""
    print("\nTesting send_rgb_data default parameter...")
    
    client = DDPClient("127.0.0.1")
    sig = inspect.signature(client.send_rgb_data)
    
    # Check that prepare_device parameter exists and has default value False
    assert 'prepare_device' in sig.parameters, "prepare_device parameter should exist"
    
    param = sig.parameters['prepare_device']
    assert param.default is False, f"prepare_device should default to False, got {param.default}"
    
    print("✓ send_rgb_data defaults to prepare_device=False")


def test_start_streaming_default():
    """Test that start_streaming has prepare_device=False by default."""
    print("\nTesting start_streaming default parameter...")
    
    client = DDPClient("127.0.0.1")
    sig = inspect.signature(client.start_streaming)
    
    # Check that prepare_device parameter exists and has default value False
    assert 'prepare_device' in sig.parameters, "prepare_device parameter should exist"
    
    param = sig.parameters['prepare_device']
    assert param.default is False, f"prepare_device should default to False, got {param.default}"
    
    print("✓ start_streaming defaults to prepare_device=False")


if __name__ == "__main__":
    print("Testing DDP Default Parameters")
    print("=" * 60)
    
    try:
        test_send_image_default()
        test_send_rgb_data_default()
        test_start_streaming_default()
        
        print("\n" + "=" * 60)
        print("✓ All default parameter tests passed!")
        print("=" * 60)
        print("\nConclusion:")
        print("- DDP methods now default to prepare_device=False")
        print("- This matches WLEDVideoSync web UI behavior")
        print("- HTTP API preparation is skipped by default")
        print("- Users can still enable it by passing prepare_device=True")
        
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
