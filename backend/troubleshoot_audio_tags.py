"""
Quick script to test different solutions for audio tags being spoken as words.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.elevenlabs_service import elevenlabs_service
from app.config import get_settings


MODELS_TO_TEST = [
    "eleven_v3",  # Actual v3 model with audio tags support
    "eleven_turbo_v2_5",
    "eleven_multilingual_v2",
    "eleven_flash_v2_5",
    "eleven_monolingual_v1"
]


async def test_with_different_models():
    """Test the same phrase with different models."""
    print("=" * 60)
    print("Testing Different Models for Audio Tag Support")
    print("=" * 60)
    
    settings = get_settings()
    test_text = "[gasps] That's incredible! [short pause] Tell me more."
    
    print(f"\nTest text: {test_text}")
    print(f"Voice ID: {settings.elevenlabs_host_voice_id}")
    print("\n")
    
    for i, model in enumerate(MODELS_TO_TEST, 1):
        print(f"\n🎯 Test {i}/{len(MODELS_TO_TEST)}: {model}")
        print("-" * 60)
        
        try:
            audio_path = await elevenlabs_service.text_to_speech(
                text=test_text,
                voice_id=settings.elevenlabs_host_voice_id,
                filename=f"test_model_{model}.mp3",
                model_id=model
            )
            print(f"✅ Generated: {audio_path}")
            print(f"   Listen to this file and check if tags are performed or spoken")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if "model" in str(e).lower():
                print(f"   Model '{model}' may not be available for your account")
        
        input("\nPress Enter to test next model...")


async def test_workarounds():
    """Test different workarounds for audio tags."""
    print("\n" + "=" * 60)
    print("Testing Workaround Approaches")
    print("=" * 60)
    
    settings = get_settings()
    
    test_cases = [
        ("1_with_tags", "[gasps] That's incredible! [short pause] Tell me more."),
        ("2_natural_language", "Wow! That's incredible! ... Tell me more."),
        ("3_interjections", "Hmm, that's incredible! Tell me more about that."),
        ("4_exclamations", "That's incredible!! Tell me more."),
        ("5_ellipsis_pauses", "That's incredible... really amazing... tell me more."),
    ]
    
    for filename, text in test_cases:
        print(f"\n🎯 Testing: {filename}")
        print(f"   Text: {text}")
        
        try:
            audio_path = await elevenlabs_service.text_to_speech(
                text=text,
                voice_id=settings.elevenlabs_host_voice_id,
                filename=f"workaround_{filename}.mp3"
            )
            print(f"✅ Generated: {audio_path}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("Press Enter to continue...")


async def test_stripped_tags():
    """Test with audio tags stripped out."""
    print("\n" + "=" * 60)
    print("Testing With Tags Stripped (Safe Fallback)")
    print("=" * 60)
    
    settings = get_settings()
    
    # Temporarily disable tags
    import re
    
    test_text_with_tags = "[gasps] That's incredible! [short pause] Tell me more about [thoughtful] how you discovered this."
    test_text_stripped = re.sub(r'\[.*?\]', '', test_text_with_tags)
    test_text_stripped = re.sub(r'\s+', ' ', test_text_stripped).strip()
    
    print(f"\nOriginal (with tags): {test_text_with_tags}")
    print(f"Stripped (no tags):   {test_text_stripped}")
    
    try:
        audio_path = await elevenlabs_service.text_to_speech(
            text=test_text_stripped,
            voice_id=settings.elevenlabs_host_voice_id,
            filename=f"test_stripped_tags.mp3"
        )
        print(f"\n✅ Generated: {audio_path}")
        print("   This should sound natural without any tag artifacts")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests."""
    print("🔧 Audio Tags Troubleshooting Tool")
    print("=" * 60)
    print("\nThis script will help you find the best solution")
    print("for your audio tag issues.\n")
    
    # Check configuration
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("❌ ELEVENLABS_API_KEY not configured in .env")
        return
    
    print(f"📋 Current Configuration:")
    print(f"   Model: {settings.elevenlabs_model_id}")
    print(f"   HOST Voice: {settings.elevenlabs_host_voice_id}")
    print(f"   Tags Enabled: {settings.enable_audio_tags}")
    print()
    
    # Menu
    while True:
        print("\n" + "=" * 60)
        print("What would you like to test?")
        print("=" * 60)
        print("1. Test different models (find which works best)")
        print("2. Test workaround approaches (natural language)")
        print("3. Test with tags stripped (safe fallback)")
        print("4. Run all tests")
        print("5. Exit")
        print()
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            await test_with_different_models()
        elif choice == "2":
            await test_workarounds()
        elif choice == "3":
            await test_stripped_tags()
        elif choice == "4":
            await test_with_different_models()
            await test_workarounds()
            await test_stripped_tags()
        elif choice == "5":
            print("\n✨ Done! Check the audio_files/ directory for generated files.")
            break
        else:
            print("Invalid choice. Try again.")
    
    print("\n📚 For more help, see: AUDIO_TAGS_TROUBLESHOOTING.md")


if __name__ == "__main__":
    asyncio.run(main())
