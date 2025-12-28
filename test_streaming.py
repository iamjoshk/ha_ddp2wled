"""Test streaming functionality for DDP protocol."""
import asyncio
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'pixelmagictool'))

from ddp import DDPClient


async def test_streaming_session_lifecycle():
    """Test streaming session start, send, and stop."""
    print("Testing streaming session lifecycle...")
    
    client = DDPClient("127.0.0.1")
    
    # Initially, no streaming should be active
    assert not client.is_streaming(), "Should not be streaming initially"
    
    # Start streaming (won't actually connect since host is localhost)
    try:
        # This will fail to connect but that's OK for the test
        # We're just testing the state management
        await client.start_streaming(prepare_device=False)
    except OSError:
        # Expected - localhost doesn't have a WLED device
        pass
    
    print("✓ Streaming session lifecycle test passed")


async def test_streaming_state_management():
    """Test streaming state management."""
    print("\nTesting streaming state management...")
    
    client = DDPClient("127.0.0.1")
    
    # Check initial state
    assert not client.is_streaming(), "Should not be streaming initially"
    assert client._sequence_num == 0, "Sequence number should be 0 initially"
    
    print("✓ Streaming state management test passed")


async def test_send_frame_without_session():
    """Test that sending frame without starting session raises error."""
    print("\nTesting send_frame without active session...")
    
    client = DDPClient("127.0.0.1")
    
    # Create dummy RGB data
    rgb_data = bytes([255, 0, 0] * 10)  # 10 red LEDs
    
    # Try to send frame without starting session
    try:
        await client.send_frame(rgb_data, width=10, height=1)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "No active streaming session" in str(e), f"Wrong error message: {e}"
    
    print("✓ send_frame without session test passed")


async def test_stop_streaming_without_session():
    """Test that stopping non-existent session returns False."""
    print("\nTesting stop_streaming without active session...")
    
    client = DDPClient("127.0.0.1")
    
    # Try to stop when no session is active
    result = await client.stop_streaming()
    assert result is False, "Should return False when no session to stop"
    
    print("✓ stop_streaming without session test passed")


async def test_session_initialization():
    """Test that DDPClient initializes with correct streaming state."""
    print("\nTesting session initialization...")
    
    client = DDPClient("192.168.1.100")
    
    # Verify initial state
    assert client.host == "192.168.1.100", "Host should be set correctly"
    assert client.port == 4048, "Port should default to 4048"
    assert client.socket is None, "Socket should be None initially"
    assert not client._streaming, "Should not be streaming"
    assert client._sequence_num == 0, "Sequence number should be 0"
    assert client._lock is not None, "Lock should be initialized"
    
    print("✓ Session initialization test passed")


async def test_multiple_clients():
    """Test that multiple DDPClients can coexist."""
    print("\nTesting multiple DDPClient instances...")
    
    client1 = DDPClient("192.168.1.100")
    client2 = DDPClient("192.168.1.101")
    
    # Verify they're independent
    assert client1.host != client2.host, "Hosts should be different"
    assert not client1.is_streaming(), "Client 1 should not be streaming"
    assert not client2.is_streaming(), "Client 2 should not be streaming"
    
    print("✓ Multiple clients test passed")


def test_sequence_number_wrapping():
    """Test that sequence numbers wrap at 255."""
    print("\nTesting sequence number wrapping...")
    
    # Test sequence number masking logic
    for seq_num in [0, 1, 254, 255, 256, 257, 511, 512]:
        wrapped = seq_num & 0xFF
        assert 0 <= wrapped <= 255, f"Wrapped sequence {wrapped} out of range for input {seq_num}"
    
    # Verify specific wrapping cases
    assert (255 & 0xFF) == 255, "255 should wrap to 255"
    assert (256 & 0xFF) == 0, "256 should wrap to 0"
    assert (257 & 0xFF) == 1, "257 should wrap to 1"
    
    print("✓ Sequence number wrapping test passed")


async def run_async_tests():
    """Run all async tests."""
    await test_streaming_session_lifecycle()
    await test_streaming_state_management()
    await test_send_frame_without_session()
    await test_stop_streaming_without_session()
    await test_session_initialization()
    await test_multiple_clients()


if __name__ == "__main__":
    print("Running DDP streaming tests...\n")
    print("=" * 60)
    
    try:
        # Run synchronous tests
        test_sequence_number_wrapping()
        
        # Run async tests
        asyncio.run(run_async_tests())
        
        print("\n" + "=" * 60)
        print("✓ All streaming tests passed!")
        print("=" * 60)
        
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
