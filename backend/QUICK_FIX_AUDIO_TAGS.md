# 🚨 IMMEDIATE FIX: Audio Tags Being Spoken As Words

## The Problem

You're hearing: "gasps, That's incredible" or "inhales loudly" 
Instead of: *actual gasp sound* "That's incredible"

## Quick Fixes (Try in Order)

### ✅ FIX #1: Disable Audio Tags (Recommended - Works Immediately)

Add this to your `.env` file:

```bash
ENABLE_AUDIO_TAGS=false
```

**Restart your server** and the tags will be stripped out automatically.

**Result:** Text like `"[gasps] Hello"` becomes `"Hello"` - clean audio without artifacts.

---

### ✅ FIX #2: Try Different Model

Some models handle tags better than others. Edit your `.env`:

```bash
# Try these in order:
ELEVENLABS_MODEL_ID=eleven_v3
# or
ELEVENLABS_MODEL_ID=eleven_ttv_v3
# or
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
```

Test with:
```bash
python troubleshoot_audio_tags.py
```

---

### ✅ FIX #3: Use Natural Language Instead

Instead of relying on audio tags, modify your prompts to use natural conversational language:

**Before (with tags):**
```json
{
  "speaker": "host",
  "text": "[gasps] That's incredible! [short pause] Tell me more."
}
```

**After (natural language):**
```json
{
  "speaker": "host",
  "text": "Wow! That's incredible! ... Tell me more."
}
```

Update the prompts to instruct Gemini:
- Use "Hmm" instead of `[thoughtful]`
- Use "Wow!" or "Oh!" instead of `[gasps]`
- Use "..." for pauses instead of `[short pause]`
- Use "Haha" or "Ha!" instead of `[chuckles]`

---

## Testing Your Fix

Run the troubleshooting tool:

```bash
cd backend
python troubleshoot_audio_tags.py
```

This will:
1. Test different models
2. Test different approaches (with/without tags)
3. Help you find what works best for your voices

---

## Understanding Why This Happens

**Audio tags are experimental.** They work inconsistently because:

1. **Voice Compatibility:** Not all voices interpret tags correctly
2. **Model Versions:** Different models have different tag support
3. **API Tier:** Some features may be tier-specific
4. **Language/Accent:** Tags work better with some voices than others

**The bottom line:** Audio tags are hit-or-miss. Natural language is more reliable.

---

## Recommended Production Setup

### Option A: Disable Tags, Use Natural Language

```bash
# .env
ENABLE_AUDIO_TAGS=false
```

Then update your prompts to use natural conversational text without tags.

**Pros:**
- ✅ Reliable and consistent
- ✅ No artifacts or weird spoken tags
- ✅ Works with all voices

**Cons:**
- ❌ Less control over specific sounds
- ❌ Miss out on potential expressiveness

### Option B: Keep Tags, But Use Sparingly

```bash
# .env
ENABLE_AUDIO_TAGS=true
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
```

Use ONLY these tags (most reliable):
- Natural interjections: "Hmm", "Ah", "Oh" (in text, not as tags)
- Ellipses for pauses: "..."
- Exclamations: "!" "?"

**Pros:**
- ✅ Some expressiveness
- ✅ Natural rhythm

**Cons:**
- ❌ Still might have issues
- ❌ Need to test extensively

---

## Files to Update

### 1. `.env`
```bash
# Add these lines:
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5
ENABLE_AUDIO_TAGS=false  # Set to false to disable
```

### 2. Update Prompts (Optional)

If disabling tags, update your prompts to not generate them:

**`prompts/podcast_generation.md`**

Remove the audio tags section and replace with:

```markdown
### Natural Conversational Style

Use natural language for expression:
- "Hmm" or "Ah" for thoughtful moments
- "Wow!" or "Really?" for surprise
- "..." (ellipsis) for pauses
- "Haha" or "Ha!" for laughter

Example:
HOST: "Wow! That's amazing! ... Tell me more about that."
EXPERT: "Well, let me explain... It's quite interesting actually."
```

---

## Test Commands

```bash
# 1. Test current setup
python test_audio_tags.py

# 2. Run troubleshooting tool (interactive)
python troubleshoot_audio_tags.py

# 3. Generate a real podcast and listen
# (Start server and make podcast generation request)
```

---

## Summary

**IMMEDIATE ACTION:**

1. Open `.env`
2. Add: `ENABLE_AUDIO_TAGS=false`
3. Restart server
4. Test again

**RESULT:** Tags will be stripped automatically, giving you clean audio without spoken tags.

**NEXT STEP:** Decide if you want to:
- A) Keep tags disabled and use natural language (recommended)
- B) Try different models to see if any work better with your voices
- C) Contact ElevenLabs support about tag support for your specific voices

---

## Need More Help?

- **Troubleshooting Tool:** `python troubleshoot_audio_tags.py`
- **Full Guide:** `AUDIO_TAGS_TROUBLESHOOTING.md`
- **Test Suite:** `python test_audio_tags.py`

---

**Status:** This is a known limitation with audio tags. They're experimental and don't work reliably with all voices. Disabling them and using natural language is the most reliable solution.
