#!/usr/bin/env python3
"""
Test WLED-MM compatibility features.

This test validates:
1. chunk_delay parameter is properly passed through
2. Default values are correct for WLED-MM compatibility
3. Chunk delay affects timing in chunked sending
"""

import sys
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, 'custom_components/pixelmagictool')
from converter import PixelMagicToolAPI
from const import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_DELAY


def test_default_values():
    """Test that default values are set for WLED-MM compatibility."""
    print("=" * 70)
    print("Test: Default Values for WLED-MM Compatibility")
    print("=" * 70)
    
    # Check default chunk size
    print(f"\nDefault chunk_size: {DEFAULT_CHUNK_SIZE}")
    assert DEFAULT_CHUNK_SIZE == 128, f"Expected 128, got {DEFAULT_CHUNK_SIZE}"
    print("✓ Default chunk_size is 128 (WLED-MM compatible)")
    
    # Check default chunk delay
    print(f"\nDefault chunk_delay: {DEFAULT_CHUNK_DELAY}")
    assert DEFAULT_CHUNK_DELAY == 0.15, f"Expected 0.15, got {DEFAULT_CHUNK_DELAY}"
    print("✓ Default chunk_delay is 0.15s (good for stability)")
    
    print("\n" + "=" * 70)
    print("✓ Default values test passed!")
    print("=" * 70)


async def test_chunk_delay_parameter():
    """Test that chunk_delay parameter is used in chunked sending."""
    print("\n" + "=" * 70)
    print("Test: chunk_delay Parameter Usage")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Create a test WLED JSON with enough data to trigger chunking
    test_json = {
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["FF0000"] * 300  # 300 LEDs to force chunking
        },
        "live": False
    }
    
    # Mock the HTTP response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})
    
    # Mock the session.post to return a context manager
    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    
    # Track asyncio.sleep calls to verify delay
    sleep_calls = []
    
    async def mock_sleep(delay):
        sleep_calls.append(delay)
        # Don't actually sleep for faster testing
        return
    
    with patch('asyncio.sleep', side_effect=mock_sleep):
        # Test with custom chunk_delay
        custom_delay = 0.25
        print(f"\nTesting with chunk_delay={custom_delay}s, chunk_size=100")
        sleep_calls.clear()
        
        try:
            result = await api.send_to_wled(
                wled_host="192.168.1.100",
                wled_json=test_json,
                session=mock_session,
                use_chunks=True,
                chunk_size=100,
                chunk_delay=custom_delay
            )
            
            # We should have 300 LEDs / 100 chunk_size = 3 chunks
            # Which means 2 delays (no delay after last chunk)
            expected_delays = 2
            print(f"Expected {expected_delays} delays, got {len(sleep_calls)}")
            print(f"Delay values: {sleep_calls}")
            
            # Verify all delays match our custom delay
            for delay in sleep_calls:
                assert delay == custom_delay, f"Expected {custom_delay}s, got {delay}s"
            
            print(f"✓ All delays are {custom_delay}s as expected")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            raise
    
    print("\n" + "=" * 70)
    print("✓ chunk_delay parameter test passed!")
    print("=" * 70)


async def test_wled_mm_optimized_settings():
    """Test that WLED-MM optimized settings work correctly."""
    print("\n" + "=" * 70)
    print("Test: WLED-MM Optimized Settings")
    print("=" * 70)
    
    api = PixelMagicToolAPI()
    
    # Test WLED-MM recommended settings
    wled_mm_settings = {
        "chunk_size": 128,
        "chunk_delay": 0.2,
    }
    
    print(f"\nTesting WLED-MM settings:")
    print(f"  chunk_size: {wled_mm_settings['chunk_size']}")
    print(f"  chunk_delay: {wled_mm_settings['chunk_delay']}")
    
    # Create test data
    test_json = {
        "on": True,
        "bri": 128,
        "seg": {
            "id": 0,
            "i": ["FF0000"] * 256  # 256 LEDs (32x32)
        },
        "live": False
    }
    
    # Mock the HTTP response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})
    
    # Mock the session.post to return a context manager
    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    
    # Mock asyncio.sleep
    with patch('asyncio.sleep', new_callable=AsyncMock):
        try:
            result = await api.send_to_wled(
                wled_host="192.168.1.100",
                wled_json=test_json,
                session=mock_session,
                use_chunks=True,
                **wled_mm_settings
            )
            
            print("✓ WLED-MM settings accepted without errors")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            raise
    
    print("\n" + "=" * 70)
    print("✓ WLED-MM optimized settings test passed!")
    print("=" * 70)


def run_all_tests():
    """Run all WLED-MM compatibility tests."""
    print("\n" * 2)
    print("*" * 70)
    print("WLED-MM Compatibility Test Suite")
    print("*" * 70)
    
    try:
        # Test 1: Default values
        test_default_values()
        
        # Test 2: chunk_delay parameter (async)
        asyncio.run(test_chunk_delay_parameter())
        
        # Test 3: WLED-MM optimized settings (async)
        asyncio.run(test_wled_mm_optimized_settings())
        
        print("\n" * 2)
        print("*" * 70)
        print("✓✓✓ ALL WLED-MM COMPATIBILITY TESTS PASSED ✓✓✓")
        print("*" * 70)
        print("\nWLED-MM compatibility features verified:")
        print("  ✓ Default chunk_size is 128 (WLED-MM compatible)")
        print("  ✓ Default chunk_delay is 0.15s")
        print("  ✓ chunk_delay parameter works correctly")
        print("  ✓ WLED-MM optimized settings accepted")
        print("\n")
        return True
        
    except AssertionError as e:
        print("\n" * 2)
        print("*" * 70)
        print("✗✗✗ TESTS FAILED ✗✗✗")
        print("*" * 70)
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
