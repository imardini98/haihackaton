# ElevenLabs v3 API Migration Guide

## Overview

This document outlines the migration from ElevenLabs v2 to v3 API, including the new audio tags feature that enhances podcast naturalness.

## What Changed

### 1. Model Version

**Before (v2):**
```python
audio = self.client.text_to_speech.convert(
    voice_id=voice_id,
    text=text,
    model_id="eleven_multilingual_v2"
)
```

**After (v3):**
```python
audio = self.client.text_to_speech.convert(
    voice_id=voice_id,
    text=text,
    model_id="eleven_turbo_v2_5",  # v3 compatible
    output_format="mp3_44100_128"   # Explicit format
)
```

### 2. Audio Tags Support

v3 introduces performance direction tags that make speech more natural:

```python
# v2 - Plain text only
text = "Let me think about that. Yes, I believe that's correct."

# v3 - With expressive audio tags
text = "[thoughtful] Hmm, let me think about that. [short pause] Yes, I believe that's correct."
```

### 3. Configuration

Added new environment variable:

```bash
# .env
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
```

Updated `config.py`:

```python
class Settings(BaseSettings):
    elevenlabs_model_id: str = "eleven_turbo_v2_5"
```

## Audio Tags Catalog

### Breath & Pauses
- `[inhales]`, `[inhales sharply]`
- `[exhales]`, `[exhales sharply]`
- `[short pause]`, `[long pause]`

### Reactions
- `[sighs]`, `[gasps]`, `[gulps]`
- `[clears throat]`, `[coughs]`

### Laughter
- `[laughs]`, `[chuckles]`, `[giggles]`, `[snorts]`

### Voice Delivery
- `[whispers]`, `[shouts]`, `[stammers]`

### Emotion
- `[thoughtful]`, `[confused]`, `[nervous]`
- `[relieved]`, `[sarcastic]`

### Custom Tags
The model is flexible - try variants:
- `[humming]`, `[hesitates]`, `[uncertain]`
- `[excited]`, `[surprised]`, `[amazed]`

## Implementation Changes

### ElevenLabsService

Added helper methods for audio tag manipulation:

```python
# Add single tag
text = elevenlabs_service.add_audio_tag("Let me think", "thoughtful")
# Returns: "[thoughtful] Let me think"

# Wrap with pauses
text = elevenlabs_service.wrap_with_pause("Important point", "short pause")
# Returns: "[short pause] Important point [short pause]"
```

Updated `text_to_speech` method signature:

```python
async def text_to_speech(
    self,
    text: str,
    voice_id: str,
    filename: Optional[str] = None,
    model_id: Optional[str] = None  # Now configurable
) -> str:
```

### Prompt Templates

All three prompt templates updated to include audio tag instructions:

1. **podcast_generation.md**
   - Added audio tags section to dialogue style guidelines
   - Updated examples with audio tags
   - Instructs Gemini to use tags sparingly

2. **question_answer.md**
   - Added audio tags to voice guidelines
   - Updated examples with natural pauses and reactions

3. **resume_conversation.md**
   - Added audio tags for natural transitions
   - Updated examples with `[inhales]` and `[short pause]`

## Usage Examples

### Podcast Generation

**HOST dialogue with tags:**
```json
{
  "speaker": "host",
  "text": "[gasps] That's incredible! [short pause] Tell me more about that."
}
```

**EXPERT dialogue with tags:**
```json
{
  "speaker": "expert",
  "text": "[clears throat] Let me explain. [thoughtful] The key finding was a 23% improvement. [short pause] Here's how we measured it."
}
```

### Q&A Responses

**HOST acknowledgment:**
```python
host_text = "[thoughtful] Oh, that's a great question! [short pause] What do you think?"
await elevenlabs_service.generate_host_audio(host_text)
```

**EXPERT answer:**
```python
expert_text = "[clears throat] So the answer is quite interesting. [inhales] First, let me explain the methodology..."
await elevenlabs_service.generate_expert_audio(expert_text)
```

### Resume Transitions

```python
resume_text = "[inhales] Alright, let's move on to the next topic."
await elevenlabs_service.generate_host_audio(resume_text)
```

## Best Practices

### 1. Use Tags Sparingly

❌ **Bad** - Overuse:
```python
"[thoughtful] Well [short pause] I think [inhales] that's [exhales] interesting"
```

✅ **Good** - Strategic use:
```python
"[thoughtful] Well, I think that's interesting. [short pause] Let me explain."
```

### 2. Match Tags to Speaker

**HOST (warm, engaging):**
- Use: `[chuckles]`, `[gasps]`, `[thoughtful]`
- Avoid: `[stammers]`, `[nervous]`

**EXPERT (confident, knowledgeable):**
- Use: `[clears throat]`, `[inhales]`, `[short pause]`
- Avoid excessive: `[confused]`, `[giggles]`

### 3. Natural Placement

Place tags where they make conversational sense:

✅ **Good:**
```python
"[inhales sharply] Wait, did you say 300%? [confused] How is that possible?"
```

### 4. Combine for Realism

```python
"[nervous] [gulps] I have to admit, [stammers] this is unexpected."
```

## Testing

Test audio tags with sample phrases:

```python
from app.services.elevenlabs_service import elevenlabs_service
from app.config import get_settings

settings = get_settings()

test_cases = [
    ("[thoughtful] Interesting question.", "thoughtful"),
    ("[chuckles] That's clever!", "chuckles"),
    ("[gasps] Really? [short pause] Tell me more.", "gasps_pause"),
    ("[clears throat] Let me explain. [inhales]", "explain"),
]

for text, name in test_cases:
    audio_path = await elevenlabs_service.text_to_speech(
        text=text,
        voice_id=settings.elevenlabs_host_voice_id,
        filename=f"test_{name}.mp3"
    )
    print(f"Generated: {audio_path}")
```

## Migration Checklist

- [x] Updated `requirements.txt` to `elevenlabs>=1.9.0`
- [x] Updated model to `eleven_turbo_v2_5` in service
- [x] Added `elevenlabs_model_id` to config
- [x] Added helper methods to `ElevenLabsService`
- [x] Updated all prompt templates with audio tag instructions
- [x] Updated `.env.example` with v3 configuration
- [x] Created `AUDIO_TAGS_GUIDE.md` documentation
- [x] Updated examples in prompts to include audio tags

## Rollback Plan

If issues arise, revert by:

1. Change model back in config:
   ```python
   elevenlabs_model_id: str = "eleven_multilingual_v2"
   ```

2. Remove audio tags from generated text (they'll be ignored by v2):
   ```python
   import re
   text = re.sub(r'\[.*?\]', '', text)  # Strip all tags
   ```

## Performance Considerations

- **v3 vs v2 latency:** Similar generation times
- **Audio quality:** Improved with v3, especially for expressive content
- **Cost:** Same pricing tier
- **Compatibility:** v3 tags are backward compatible (ignored by v2 models)

## Support & Resources

- **Audio Tags Guide:** `backend/AUDIO_TAGS_GUIDE.md`
- **ElevenLabs v3 Docs:** https://elevenlabs.io/docs
- **Service Implementation:** `backend/app/services/elevenlabs_service.py`
- **Prompt Templates:** `backend/prompts/`

## Future Enhancements

Potential improvements:

1. **Dynamic tag selection** based on content sentiment
2. **Tag optimization** based on user feedback
3. **A/B testing** tagged vs untagged audio
4. **Custom voice profiles** tuned for specific tag types
5. **Real-time tag preview** in UI before generation

## Contact

For questions about v3 implementation, see:
- Technical docs: `backend/AUDIO_TAGS_GUIDE.md`
- Implementation: `backend/app/services/elevenlabs_service.py`
- Configuration: `backend/app/config.py`
