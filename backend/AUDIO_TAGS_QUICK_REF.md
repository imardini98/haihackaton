# ElevenLabs v3 Audio Tags - Quick Reference

## 🎯 Quick Start

```python
from app.services.elevenlabs_service import elevenlabs_service

# Basic usage with audio tags
text = "[thoughtful] Let me explain. [short pause] The key is..."
audio_path = await elevenlabs_service.text_to_speech(text, voice_id)
```

## 📝 Audio Tags Cheat Sheet

| Category | Tags | Use Case |
|----------|------|----------|
| **Pauses** | `[short pause]`, `[long pause]` | Pacing, emphasis |
| **Breath** | `[inhales]`, `[exhales]` | Natural rhythm |
| **Reactions** | `[sighs]`, `[gasps]`, `[gulps]` | Emotional moments |
| **Clearing** | `[clears throat]`, `[coughs]` | Before speaking |
| **Laughter** | `[laughs]`, `[chuckles]`, `[giggles]` | Warmth, humor |
| **Emotion** | `[thoughtful]`, `[confused]`, `[nervous]` | Context, tone |
| **Delivery** | `[whispers]`, `[shouts]` | Emphasis |

## 🎭 Character-Specific Tags

### HOST (Warm & Curious)
```python
# Good for HOST
"[gasps] That's amazing! [chuckles]"
"[thoughtful] So what you're saying is..."
"[short pause] Tell me more about that."

# Avoid for HOST
"[stammers]"  # Too uncertain
"[nervous]"   # Not confident enough
```

### EXPERT (Knowledgeable & Clear)
```python
# Good for EXPERT
"[clears throat] Let me explain."
"[thoughtful] The key finding was..."
"[inhales] It's complex. [short pause] Here's how..."

# Avoid for EXPERT
"[giggles]"   # Too casual
"[confused]"  # Not authoritative enough
```

## 🛠️ Helper Methods

```python
# Add single tag
text = elevenlabs_service.add_audio_tag("Question for you", "thoughtful")
# Output: "[thoughtful] Question for you"

# Wrap with pauses
text = elevenlabs_service.wrap_with_pause("Important point", "short pause")
# Output: "[short pause] Important point [short pause]"
```

## ✅ Best Practices

### DO ✅
- Use tags sparingly (1-2 per sentence max)
- Match tags to speaker personality
- Place at natural conversation points
- Test with actual voices

```python
# Good
"[thoughtful] That's interesting. [short pause] Let me think about it."
```

### DON'T ❌
- Overuse tags
- Use conflicting emotions
- Place mid-word or awkwardly

```python
# Bad - too many tags
"[thoughtful] Well [pause] I [inhales] think [exhales] that's good"
```

## 🎬 Common Patterns

### Opening a Segment
```python
"[inhales] Welcome back. [short pause] Today we're discussing..."
```

### Expressing Surprise
```python
"[gasps] Really? [short pause] That's incredible!"
```

### Explaining Complex Topics
```python
"[clears throat] Let me break this down. [thoughtful] First..."
```

### Transitioning
```python
"[inhales] Alright, let's move on to the next topic."
```

### Acknowledging a Question
```python
"[thoughtful] Oh, that's a great question! [short pause] Well..."
```

### Building Suspense
```python
"[whispers] What we found next was surprising. [long pause] [gasps]"
```

## 🧪 Testing Tags

```bash
# Run test suite
python backend/test_audio_tags.py

# Check generated audio
ls audio_files/test_*.mp3
```

## 🔧 Configuration

```bash
# .env
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
ELEVENLABS_HOST_VOICE_ID=XA2bIQ92TabjGbpO2xRr
ELEVENLABS_EXPERT_VOICE_ID=PoHUWWWMHFrA8z7Q88pu
```

## 📚 Full Documentation

- **Comprehensive Guide:** `backend/AUDIO_TAGS_GUIDE.md`
- **Migration Guide:** `backend/ELEVENLABS_V3_MIGRATION.md`
- **Service Code:** `backend/app/services/elevenlabs_service.py`

## 🐛 Troubleshooting

**Tags not working?**
1. Check model is `eleven_turbo_v2_5` or newer
2. Verify ElevenLabs API version >= 1.9.0
3. Test with simple tags first (`[short pause]`)

**Sounds unnatural?**
1. Reduce tag frequency
2. Try different tag combinations
3. Match tags to voice personality

**Need custom tags?**
- Try variants: `[hesitates]`, `[excited]`, `[amazed]`
- v3 model interprets most bracketed directions

## 💡 Pro Tips

1. **Start simple** - Use `[short pause]` and `[inhales]` first
2. **Listen & iterate** - Test different tags for same phrase
3. **Context matters** - Same tag sounds different in different contexts
4. **Less is more** - Strategic placement > frequent use
5. **Match content** - Serious topics = fewer playful tags

## 🚀 Quick Examples

```python
# Question acknowledgment
host = "[thoughtful] Great question! [short pause] What do you think?"

# Expert explanation
expert = "[clears throat] The answer is quite interesting. [inhales] Let me explain the three key factors. [short pause] First..."

# Excited reaction
host = "[gasps] That's incredible! [chuckles] I never would have guessed!"

# Transitioning after Q&A
host = "[inhales] Alright, let's get back to the discussion."

# Building to key point
expert = "[thoughtful] This is where it gets interesting. [long pause] The data showed something unexpected."
```

## 🎯 Tag Selection Flowchart

```
Starting dialogue?
└─ Use: [clears throat], [inhales]

Emphasizing point?
└─ Use: [short pause], [long pause]

Showing emotion?
├─ Surprise: [gasps]
├─ Humor: [chuckles], [laughs]
├─ Thinking: [thoughtful]
└─ Relief: [relieved]

Reacting to content?
├─ Complex: [sighs]
├─ Unexpected: [gasps]
└─ Nervous: [gulps]

Transitioning?
└─ Use: [inhales], [short pause]
```

---

**Remember:** Audio tags are a v3 enhancement. They're optional but make dialogue more engaging and natural!
