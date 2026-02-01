"""
Quick test with the CORRECT v3 model (eleven_v3)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.elevenlabs_service import elevenlabs_service
from app.config import get_settings


async def test_v3_model():
    """Test with the actual eleven_v3 model."""
    print("=" * 60)
    print("Testing eleven_v3 Model (Correct V3)")
    print("=" * 60)
    
    settings = get_settings()
    
    test_cases = [
        ("basic", "Hello, this is a basic test."),
        ("with_pause", "Hello. [short pause] This is a test with a pause."),
        ("with_gasp", "[gasps] That's incredible!"),
        ("with_chuckle", "[chuckles] That's pretty funny!"),
        ("with_thoughtful", "[thoughtful] Hmm, let me think about that."),
        ("complex", "[inhales] Well, [thoughtful] that's interesting. [short pause] Tell me more."),
    ]
    
    print(f"\n📋 Configuration:")
    print(f"   Model: eleven_v3")
    print(f"   HOST Voice: {settings.elevenlabs_host_voice_id}")
    print(f"   Tags Enabled: {settings.enable_audio_tags}")
    print()
    
    for name, text in test_cases:
        print(f"\n🎯 Test: {name}")
        print(f"   Text: {text}")
        
        try:
            audio_path = await elevenlabs_service.text_to_speech(
                text=text,
                voice_id=settings.elevenlabs_host_voice_id,
                filename=f"v3_test_{name}.mp3",
                model_id="eleven_v3"  # Use actual v3 model
            )
            print(f"✅ Generated: {audio_path}")
            print(f"   Listen carefully: Are the tags PERFORMED or SPOKEN?")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if "model" in str(e).lower():
                print(f"   NOTE: eleven_v3 might require specific API access")
                print(f"   Try eleven_ttv_v3 instead if this fails")
        
        input("\nPress Enter to continue to next test...")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\n📝 What to check:")
    print("   - Do [gasps] sound like actual gasps?")
    print("   - Or does the AI say the word 'gasps'?")
    print("   - Are [short pause] tags creating actual pauses?")
    print()
    print("If tags are still spoken as words:")
    print("   1. Try eleven_ttv_v3 model instead")
    print("   2. Check if your API tier supports v3")
    print("   3. Contact ElevenLabs about v3 access")
    print("   4. Or disable tags: ENABLE_AUDIO_TAGS=false")
    print()


async def compare_models():
    """Compare v3 models side by side."""
    print("=" * 60)
    print("Comparing V3 Models")
    print("=" * 60)
    
    settings = get_settings()
    test_text = "[gasps] That's incredible! [short pause] Tell me more."
    
    models_to_test = [
        ("eleven_v3", "V3 (Text to Speech)"),
        ("eleven_ttv_v3", "V3 (Text to Voice)"),
    ]
    
    for model_id, description in models_to_test:
        print(f"\n🎯 Testing: {description}")
        print(f"   Model: {model_id}")
        print(f"   Text: {test_text}")
        
        try:
            audio_path = await elevenlabs_service.text_to_speech(
                text=test_text,
                voice_id=settings.elevenlabs_host_voice_id,
                filename=f"compare_{model_id}.mp3",
                model_id=model_id
            )
            print(f"✅ Generated: {audio_path}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        input("\nPress Enter to test next model...")


async def main():
    """Run tests."""
    print("\n🎉 CORRECT V3 MODEL TEST")
    print("=" * 60)
    print("\nWe're now using the CORRECT model names:")
    print("  - eleven_v3 (main v3 model)")
    print("  - eleven_ttv_v3 (text to voice v3)")
    print()
    print("This should fix the issue of tags being spoken!\n")
    
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("❌ ELEVENLABS_API_KEY not configured")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("Choose test:")
        print("=" * 60)
        print("1. Test all audio tags with eleven_v3")
        print("2. Compare eleven_v3 vs eleven_ttv_v3")
        print("3. Exit")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            await test_v3_model()
        elif choice == "2":
            await compare_models()
        elif choice == "3":
            break
        else:
            print("Invalid choice")
    
    print("\n✨ Done! Check audio_files/ for generated audio.")
    print("\n📚 See QUICK_FIX_AUDIO_TAGS.md for more help.")


if __name__ == "__main__":
    asyncio.run(main())
