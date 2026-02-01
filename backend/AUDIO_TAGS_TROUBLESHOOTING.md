# 🔧 Audio Tags Troubleshooting Guide

## Issue: Tags Being Spoken Instead of Performed

If you're hearing the AI say "gasps" or "inhales" as words instead of actually performing those actions, here are the solutions:

### Problem

```
Input:  "[gasps] That's incredible!"
Output: "gasps, That's incredible!" (spoken as words)
Expected: *actual gasp sound* "That's incredible!"
```

### Root Causes & Solutions

## 1. Model Compatibility ⚡ MOST COMMON

**Problem:** Not all ElevenLabs models support audio tags equally.

**Solution:** Try these models in order of audio tag support:

```bash
# In your .env file, try these models:

# Option 1: V3 Model (best for audio tags - NEW!)
ELEVENLABS_MODEL_ID=eleven_v3

# Option 2: Turbo TTV v3 (also supports audio tags)
ELEVENLABS_MODEL_ID=eleven_ttv_v3

# Option 3: Turbo v2.5 (good for speed)
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5

# Option 4: Multilingual v2 (good for multiple languages)
ELEVENLABS_MODEL_ID=eleven_multilingual_v2

# Option 5: Flash v2.5 (experimental)
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
```

**Test each model:** After changing, run:
```bash
python test_audio_tags.py
```

## 2. Voice Compatibility 🎤

**Problem:** Some voices don't support audio tags well.

**Solution:** Try different voices from your ElevenLabs account:

```bash
# List available voices in Python:
from elevenlabs import ElevenLabs
client = ElevenLabs(api_key="your_key")
voices = client.voices.get_all()
for voice in voices.voices:
    print(f"{voice.name}: {voice.voice_id}")
```

**Recommended voice types for audio tags:**
- Professional voices (clear enunciation)
- Narrative voices (storytelling style)
- Avoid: Singing voices, character voices with heavy effects

## 3. API Version 📦

**Problem:** Older ElevenLabs Python SDK versions don't support v3 features.

**Solution:** Update the SDK:

```bash
pip install --upgrade elevenlabs

# Or force specific version:
pip install elevenlabs>=1.9.0
```

**Check your version:**
```python
import elevenlabs
print(elevenlabs.__version__)  # Should be >= 1.9.0
```

## 4. Syntax Issues ✍️

**Problem:** Incorrect tag syntax.

**Correct syntax:**
```python
# ✅ Correct
"[gasps] That's incredible!"
"[short pause] Let me think."
"[thoughtful] Hmm..."

# ❌ Incorrect
"<gasps> That's incredible!"  # Wrong brackets
"(gasps) That's incredible!"  # Wrong brackets
"*gasps* That's incredible!"  # Wrong format
"[gasp] That's incredible!"   # Singular (use [gasps])
```

## 5. Tag Overload 🚫

**Problem:** Too many tags confuse the model.

**Bad example:**
```python
"[thoughtful] [inhales] Well, [pause] I think [exhales] that's [pause] interesting"
```

**Good example:**
```python
"[thoughtful] Well, I think that's interesting. [short pause]"
```

**Rule:** Maximum 2-3 tags per sentence.

## 6. Alternative Approach: Simplified Tags 🎯

If complex tags don't work, use simpler ones that models understand better:

### Works More Reliably:
```python
"[pause] That's incredible!"
"Hmm... that's interesting"  # Natural interjections
"Ah, I see"
"Oh! Really?"
```

### Less Reliable:
```python
"[gasps intensely]"  # Too specific
"[inhales sharply with surprise]"  # Too descriptive
"[thoughtfully pauses]"  # Compound tags
```

## 7. Test Different Tag Categories

Some tag categories work better than others. Test in this order:

### Tier 1: Most Reliable
- `[pause]` or `[short pause]`
- Simple interjections in text: "Hmm", "Ah", "Oh"
- Natural speech patterns

### Tier 2: Usually Works
- `[chuckles]`, `[laughs]`
- `[sighs]`
- `[inhales]`, `[exhales]`

### Tier 3: Hit or Miss
- `[gasps]` - sometimes spoken as word
- `[clears throat]` - sometimes spoken as word
- `[thoughtful]` - often ignored or spoken
- Emotion tags like `[nervous]`, `[confused]`

## 8. Workaround: Natural Language Alternative

Instead of tags, use natural language that implies the action:

### Instead of Tags:
```python
"[gasps] That's incredible!"
"[thoughtful] Hmm, let me think..."
"[clears throat] Let me explain."
```

### Use Natural Language:
```python
"Wow! That's incredible!"  # Implies excitement
"Hmm... let me think about that..."  # Natural pause
"So, let me explain..."  # Natural transition
```

This often produces more natural results because the AI is trained on conversational speech.

## 9. Check ElevenLabs Dashboard Settings

Log into your ElevenLabs dashboard:

1. Go to your voice settings
2. Check if "Enhanced" or "Turbo" models are enabled
3. Try regenerating the voice with different settings
4. Some voices have "expressiveness" sliders - adjust these

## 10. Python Code for Testing

Create a test file to systematically test different approaches:

```python
# test_tag_approaches.py
import asyncio
from app.services.elevenlabs_service import elevenlabs_service
from app.config import get_settings

async def test_approaches():
    settings = get_settings()
    
    test_cases = [
        # Approach 1: With tags
        ("WITH TAGS", "[gasps] That's incredible!"),
        
        # Approach 2: Natural language
        ("NATURAL", "Wow! That's incredible!"),
        
        # Approach 3: Simple pauses
        ("SIMPLE PAUSE", "That's incredible. ... Really amazing."),
        
        # Approach 4: Written interjections
        ("INTERJECTIONS", "Hmm, that's incredible!"),
    ]
    
    for name, text in test_cases:
        print(f"\nTesting: {name}")
        print(f"Text: {text}")
        
        audio_path = await elevenlabs_service.text_to_speech(
            text=text,
            voice_id=settings.elevenlabs_host_voice_id,
            filename=f"test_{name.lower().replace(' ', '_')}.mp3"
        )
        print(f"Generated: {audio_path}")
        input("Press Enter to continue...")

asyncio.run(test_approaches())
```

Run this and listen to which approach sounds best.

## 11. Contact ElevenLabs Support

If none of these work, the issue might be:
- Your specific voice doesn't support tags
- Your API tier doesn't include v3 features
- Regional differences in model availability

Contact: https://elevenlabs.io/support

## Quick Fix Recommendations

### RECOMMENDED SOLUTION #1: Use Natural Language
**Abandon audio tags, use natural conversational text instead:**

```python
# Instead of this:
"[gasps] That's incredible! [short pause] Tell me more."

# Use this:
"Wow! That's incredible! ... Tell me more."
```

### RECOMMENDED SOLUTION #2: Minimal Tags
**Use only the most reliable tags:**

```python
# Only use:
- Natural interjections: "Hmm", "Ah", "Oh", "Wow"
- Ellipses for pauses: "..."
- Exclamations for emphasis: "!"

# Example:
"Hmm... that's really interesting! Tell me more about that."
```

### RECOMMENDED SOLUTION #3: Update Model
**Try the flash model which may have better tag support:**

```bash
# In .env
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
```

## Summary

**If tags are being spoken as words:**

1. ✅ **First try:** Change model to `eleven_flash_v2_5`
2. ✅ **If that fails:** Use natural language instead of tags
3. ✅ **If you need tags:** Use only simple tags like `[pause]`
4. ✅ **Best practice:** Test with different voices from your account
5. ✅ **Ultimate solution:** Accept that audio tags are experimental and use natural conversational text

## Updated Code Recommendation

Based on real-world testing, here's what works best:

```python
# backend/app/services/elevenlabs_service.py

async def text_to_speech(
    self,
    text: str,
    voice_id: str,
    filename: Optional[str] = None,
    model_id: Optional[str] = None,
    enable_audio_tags: bool = False  # NEW: Optional flag
) -> str:
    """
    Convert text to speech and save to file.
    
    Args:
        enable_audio_tags: If False, strips audio tags before generation
                          (recommended if tags are being spoken as words)
    """
    if not filename:
        filename = f"{uuid.uuid4()}.mp3"

    audio_path = self._get_audio_path(filename)

    settings = get_settings()
    if model_id is None:
        model_id = settings.elevenlabs_model_id

    # Optionally strip audio tags if they're not working
    if not enable_audio_tags:
        import re
        text = re.sub(r'\[.*?\]', '', text)  # Remove all [tags]
        text = text.strip()

    audio = self.client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model_id,
        output_format="mp3_44100_128"
    )

    with open(audio_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return str(audio_path)
```

## Need More Help?

1. Share the specific voice IDs you're using
2. Share the exact model_id from your .env
3. Share an audio sample we can listen to
4. Check ElevenLabs API documentation for your specific voices
