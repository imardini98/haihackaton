"""
Test script for ElevenLabs v3 audio tags functionality.

Usage:
    python test_audio_tags.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.elevenlabs_service import elevenlabs_service
from app.config import get_settings


async def test_basic_tts():
    """Test basic text-to-speech without tags."""
    print("🎯 Test 1: Basic TTS (no tags)")
    
    text = "Hello, this is a test of the text to speech system."
    settings = get_settings()
    
    try:
        audio_path = await elevenlabs_service.text_to_speech(
            text=text,
            voice_id=settings.elevenlabs_host_voice_id,
            filename="test_basic.mp3"
        )
        print(f"✅ Generated: {audio_path}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_audio_tags():
    """Test v3 audio tags."""
    print("\n🎯 Test 2: Audio Tags")
    
    test_cases = [
        (
            "[thoughtful] Hmm, that's an interesting question. [short pause] Let me think.",
            "thoughtful_pause"
        ),
        (
            "[chuckles] That's actually pretty clever!",
            "chuckles"
        ),
        (
            "[gasps] Wait, really? [confused] How is that possible?",
            "gasps_confused"
        ),
        (
            "[clears throat] Let me explain. [inhales] The key factor here is...",
            "clears_throat"
        ),
        (
            "[whispers] This is the important part. [long pause] [shouts] Pay attention!",
            "whispers_shouts"
        )
    ]
    
    settings = get_settings()
    results = []
    
    for text, name in test_cases:
        try:
            audio_path = await elevenlabs_service.text_to_speech(
                text=text,
                voice_id=settings.elevenlabs_host_voice_id,
                filename=f"test_{name}.mp3"
            )
            print(f"✅ Generated: {audio_path}")
            print(f"   Text: {text[:50]}...")
            results.append(True)
        except Exception as e:
            print(f"❌ Error for '{name}': {e}")
            results.append(False)
    
    return all(results)


async def test_helper_methods():
    """Test helper methods for audio tags."""
    print("\n🎯 Test 3: Helper Methods")
    
    # Test add_audio_tag
    text1 = elevenlabs_service.add_audio_tag("Let me think about that", "thoughtful")
    expected1 = "[thoughtful] Let me think about that"
    assert text1 == expected1, f"Expected '{expected1}', got '{text1}'"
    print(f"✅ add_audio_tag: {text1}")
    
    # Test wrap_with_pause
    text2 = elevenlabs_service.wrap_with_pause("This is important", "short pause")
    expected2 = "[short pause] This is important [short pause]"
    assert text2 == expected2, f"Expected '{expected2}', got '{text2}'"
    print(f"✅ wrap_with_pause: {text2}")
    
    # Test with long pause
    text3 = elevenlabs_service.wrap_with_pause("Critical information", "long pause")
    expected3 = "[long pause] Critical information [long pause]"
    assert text3 == expected3, f"Expected '{expected3}', got '{text3}'"
    print(f"✅ wrap_with_pause (long): {text3}")
    
    return True


async def test_podcast_style():
    """Test podcast-style dialogue with tags."""
    print("\n🎯 Test 4: Podcast Style Dialogue")
    
    settings = get_settings()
    
    # HOST line
    host_text = "[gasps] That's incredible! [short pause] Tell me more about how you discovered this."
    try:
        host_audio = await elevenlabs_service.text_to_speech(
            text=host_text,
            voice_id=settings.elevenlabs_host_voice_id,
            filename="test_host_line.mp3"
        )
        print(f"✅ HOST: {host_audio}")
        print(f"   Text: {host_text}")
    except Exception as e:
        print(f"❌ HOST Error: {e}")
        return False
    
    # EXPERT line
    expert_text = "[clears throat] Well, [thoughtful] it all started with an unusual observation. [inhales] We noticed a 23% improvement in the results."
    try:
        expert_audio = await elevenlabs_service.text_to_speech(
            text=expert_text,
            voice_id=settings.elevenlabs_expert_voice_id,
            filename="test_expert_line.mp3"
        )
        print(f"✅ EXPERT: {expert_audio}")
        print(f"   Text: {expert_text}")
    except Exception as e:
        print(f"❌ EXPERT Error: {e}")
        return False
    
    return True


async def test_model_configuration():
    """Test model configuration."""
    print("\n🎯 Test 5: Model Configuration")
    
    settings = get_settings()
    print(f"📋 Configured model: {settings.elevenlabs_model_id}")
    
    # Test with explicit model override
    text = "[thoughtful] Testing model override."
    try:
        audio_path = await elevenlabs_service.text_to_speech(
            text=text,
            voice_id=settings.elevenlabs_host_voice_id,
            filename="test_model_override.mp3",
            model_id="eleven_turbo_v2_5"
        )
        print(f"✅ Model override works: {audio_path}")
        return True
    except Exception as e:
        print(f"❌ Model override error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("ElevenLabs v3 Audio Tags Test Suite")
    print("=" * 60)
    
    # Check configuration
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("❌ ELEVENLABS_API_KEY not configured in .env")
        return
    
    print(f"📋 API Key: {'*' * 20}{settings.elevenlabs_api_key[-8:]}")
    print(f"📋 HOST Voice: {settings.elevenlabs_host_voice_id}")
    print(f"📋 EXPERT Voice: {settings.elevenlabs_expert_voice_id}")
    print(f"📋 Model: {settings.elevenlabs_model_id}")
    print()
    
    results = []
    
    # Run tests
    results.append(("Basic TTS", await test_basic_tts()))
    results.append(("Audio Tags", await test_audio_tags()))
    results.append(("Helper Methods", await test_helper_methods()))
    results.append(("Podcast Style", await test_podcast_style()))
    results.append(("Model Config", await test_model_configuration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    print("\n📁 Generated audio files are in: ./audio_files/")


if __name__ == "__main__":
    asyncio.run(main())
