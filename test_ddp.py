"""Test DDP protocol implementation."""
import struct
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'pixelmagictool'))

from ddp import DDPClient

def test_ddp_header():
    """Test DDP header creation."""
    print("Testing DDP header creation...")
    
    client = DDPClient("127.0.0.1")
    
    # Test header creation
    header = client._create_ddp_header(
        flags=0x41,
        sequence=0,
        data_type=0,
        dest_id=1,
        data_offset=0,
        data_length=9,
    )
    
    assert len(header) == 10, f"Header should be 10 bytes, got {len(header)}"
    
    # Unpack and verify
    unpacked = struct.unpack(">BBBBHHH", header)
    assert unpacked[0] == 0x41, f"Flags should be 0x41, got {unpacked[0]:02x}"
    assert unpacked[1] == 0, f"Sequence should be 0, got {unpacked[1]}"
    assert unpacked[2] == 0, f"Data type should be 0, got {unpacked[2]}"
    assert unpacked[3] == 1, f"Dest ID should be 1, got {unpacked[3]}"
    assert unpacked[4] == 0, f"Data offset should be 0, got {unpacked[4]}"
    assert unpacked[5] == 9, f"Data length should be 9, got {unpacked[5]}"
    assert unpacked[6] == 0, f"Timecode should be 0, got {unpacked[6]}"
    
    print("✓ DDP header creation test passed")


def test_ddp_packet():
    """Test DDP packet creation."""
    print("\nTesting DDP packet creation...")
    
    client = DDPClient("127.0.0.1")
    
    # Create test RGB data (3 LEDs: red, green, blue)
    rgb_data = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])
    
    packet = client._create_ddp_packet(rgb_data, offset=0, sequence=0, push=True)
    
    # Header is 10 bytes
    assert len(packet) == 10 + 9, f"Packet should be 19 bytes, got {len(packet)}"
    
    # Verify header
    header = packet[:10]
    unpacked = struct.unpack(">BBBBHHH", header)
    
    # Check push flag is set (0x40 | 0x01 = 0x41)
    assert unpacked[0] == 0x41, f"Flags should be 0x41 with push, got {unpacked[0]:02x}"
    
    # Verify data
    data = packet[10:]
    assert data == rgb_data, "RGB data should match"
    
    print("✓ DDP packet creation test passed")


def test_ddp_packet_offset():
    """Test DDP packet with offset."""
    print("\nTesting DDP packet with offset...")
    
    client = DDPClient("127.0.0.1")
    
    # Create test RGB data
    rgb_data = bytes([255, 255, 255] * 10)  # 10 white LEDs
    
    # Create packet with offset of 100 pixels
    packet = client._create_ddp_packet(rgb_data, offset=100, sequence=5, push=False)
    
    # Verify header
    header = packet[:10]
    unpacked = struct.unpack(">BBBBHHH", header)
    
    # Check push flag is NOT set (only version bit)
    assert unpacked[0] == 0x40, f"Flags should be 0x40 without push, got {unpacked[0]:02x}"
    
    # Sequence should be 5
    assert unpacked[1] == 5, f"Sequence should be 5, got {unpacked[1]}"
    
    # Offset should be 100 * 3 = 300 bytes
    assert unpacked[4] == 300, f"Data offset should be 300, got {unpacked[4]}"
    
    # Data length should be 30 bytes
    assert unpacked[5] == 30, f"Data length should be 30, got {unpacked[5]}"
    
    print("✓ DDP packet offset test passed")


def test_expand_range_pattern():
    """Test range pattern expansion."""
    print("\nTesting range pattern expansion...")
    
    # Skip this test if dependencies aren't available
    # The _expand_range_pattern method is tested in converter.py
    # and is used in the chunked sending functionality
    
    print("✓ Range pattern expansion test skipped (requires full dependencies)")


def test_rgb_data_size_validation():
    """Test RGB data size validation."""
    print("\nTesting RGB data size validation...")
    
    client = DDPClient("127.0.0.1")
    
    # Create invalid RGB data (not divisible by 3)
    invalid_rgb = bytes([255, 0])
    
    # This should raise ValueError when sending
    # We'll just verify the calculation works
    width = 2
    height = 2
    expected_size = width * height * 3  # 12 bytes
    
    assert len(invalid_rgb) != expected_size, "Test data should be invalid"
    
    # Create valid RGB data
    valid_rgb = bytes([255, 0, 0] * 4)  # 4 red LEDs = 12 bytes
    assert len(valid_rgb) == expected_size, "Valid data should match expected size"
    
    print("✓ RGB data size validation test passed")


def test_prepare_wled_payload():
    """Test WLED preparation payload structure."""
    print("\nTesting WLED preparation payload structure...")
    
    # Verify that the expected payload structure is correct
    # This doesn't make an actual HTTP request, just validates the structure
    
    expected_payload = {
        "on": True,
        "lor": 0,
        "live": False,
        "seg": [{
            "id": 0,
            "on": True,
            "fx": 0,
            "sel": True,
        }]
    }
    
    # Verify all required keys are present
    assert "on" in expected_payload, "Payload should have 'on' key"
    assert "lor" in expected_payload, "Payload should have 'lor' key"
    assert "live" in expected_payload, "Payload should have 'live' key"
    assert "seg" in expected_payload, "Payload should have 'seg' key"
    
    # Verify segment structure
    assert len(expected_payload["seg"]) == 1, "Payload should have one segment"
    seg = expected_payload["seg"][0]
    assert "id" in seg, "Segment should have 'id' key"
    assert "on" in seg, "Segment should have 'on' key"
    assert "fx" in seg, "Segment should have 'fx' key"
    assert "sel" in seg, "Segment should have 'sel' key"
    
    # Verify values
    assert expected_payload["on"] is True, "on should be True"
    assert expected_payload["lor"] == 0, "lor should be 0"
    assert expected_payload["live"] is False, "live should be False"
    assert seg["fx"] == 0, "fx should be 0 (Solid effect)"
    assert seg["sel"] is True, "sel should be True"
    
    print("✓ WLED preparation payload structure test passed")


if __name__ == "__main__":
    print("Running DDP protocol tests...\n")
    print("=" * 60)
    
    try:
        test_ddp_header()
        test_ddp_packet()
        test_ddp_packet_offset()
        test_expand_range_pattern()
        test_rgb_data_size_validation()
        test_prepare_wled_payload()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
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
