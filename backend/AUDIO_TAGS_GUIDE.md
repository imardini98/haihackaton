# ElevenLabs v3 Audio Tags Guide

## Overview

ElevenLabs v3 API supports audio tags in square brackets `[tag]` that add natural human expressions, pauses, and emotional nuances to generated speech. These tags work because they represent clearly audible actions that the AI can interpret as performance directions.

## How to Use Audio Tags

Simply include tags in square brackets within your text:

```python
text = "[thoughtful] Hmm, let me think about that. [short pause] Yes, I believe that's correct."
audio = await elevenlabs_service.text_to_speech(text, voice_id)
```

## Available Audio Tags

### Breath & Pauses

Perfect for natural conversation rhythm:

- `[inhales]` - Quick breath in
- `[inhales sharply]` - Sharp intake of breath (surprise/shock)
- `[exhales]` - Breath out
- `[exhales sharply]` - Sharp breath out (relief/frustration)
- `[short pause]` - Brief pause for thought
- `[long pause]` - Extended pause for dramatic effect

**Example:**
```python
text = "[inhales] Well, [short pause] that's a fascinating question. [exhales]"
```

### Reactions

Add human reactions to make dialogue more natural:

- `[sighs]` - Expression of tiredness, resignation, or relief
- `[gasps]` - Sudden surprise or shock
- `[gulps]` - Nervousness or anxiety
- `[clears throat]` - Preparing to speak or discomfort
- `[coughs]` - Mild cough

**Example:**
```python
host_text = "[gasps] Really? That's incredible! [short pause] Tell me more."
expert_text = "[clears throat] Yes, the results were quite unexpected. [sighs]"
```

### Laughter

Different types of laughter for various contexts:

- `[laughs]` - Full laugh
- `[chuckles]` - Light, gentle laugh
- `[giggles]` - Playful, light laughter
- `[snorts]` - Uncontrolled laugh through nose

**Example:**
```python
host_text = "[chuckles] That's one way to put it! [laughs]"
```

### Voice Delivery

Change how the text is spoken:

- `[whispers]` - Quiet, intimate tone
- `[shouts]` - Loud, emphatic delivery
- `[stammers]` - Hesitant, uncertain speech

**Example:**
```python
text = "[whispers] This next part is particularly important. [short pause] [shouts] Pay attention!"
```

### Emotion Direction

Add emotional context (especially useful with "hmm/ahh" moments):

- `[thoughtful]` - Contemplative, considering
- `[confused]` - Uncertain, puzzled
- `[nervous]` - Anxious, worried
- `[relieved]` - Feeling relief or satisfaction
- `[sarcastic]` - Ironic or mocking tone

**Example:**
```python
expert_text = "[thoughtful] Hmm, that's an interesting perspective. [confused] But wait, how does that explain the anomaly?"
host_text = "[relieved] Ah, that makes much more sense now!"
```

## Tag Flexibility

The v3 model is flexible with tags - they're not a fixed list. You can experiment with variants:

- `[humming]` - Humming sound
- `[hesitates]` - Uncertain pause
- `[uncertain]` - Doubtful tone
- `[excited]` - Enthusiastic delivery
- `[surprised]` - Surprised tone

## Best Practices

### 1. **Don't Overuse Tags**
Use tags sparingly for maximum effect. Too many tags can make speech sound unnatural.

❌ Bad:
```python
"[thoughtful] Well [short pause] I think [inhales] that's [exhales] interesting [long pause]"
```

✅ Good:
```python
"[thoughtful] Well, I think that's interesting. [short pause] Let me explain why."
```

### 2. **Use Tags at Natural Points**
Place tags where they make sense conversationally:

✅ Good:
```python
"[inhales sharply] Wait, did you just say the results were negative? [confused]"
```

### 3. **Combine Tags for Realism**
Combine tags to create realistic emotional moments:

```python
"[nervous] [gulps] I have to admit, [stammers] I didn't expect this outcome."
```

### 4. **Match Tags to Speaker Personality**

**HOST (warm, curious):**
- Use: `[chuckles]`, `[thoughtful]`, `[gasps]`, `[short pause]`
- Avoid: `[stammers]`, `[nervous]`

```python
host_text = "[gasps] That's fascinating! [chuckles] I never would have guessed. [short pause] So what happened next?"
```

**EXPERT (knowledgeable, confident):**
- Use: `[clears throat]`, `[sighs]`, `[thoughtful]`, `[long pause]`
- Avoid excessive: `[confused]`, `[nervous]`

```python
expert_text = "[clears throat] Let me explain the methodology. [thoughtful] We approached this in three phases. [short pause] First..."
```

## Integration with PodAsk

### In Podcast Generation Prompts

Instruct Gemini to include audio tags in dialogue:

```markdown
Generate a podcast dialogue between HOST and EXPERT.

For natural delivery, include audio tags in square brackets:
- Use [short pause] and [long pause] for pacing
- Use [chuckles], [laughs] for warmth
- Use [thoughtful], [confused] for emotional context
- Use [inhales], [exhales] for natural breath

Example:
HOST: "[chuckles] That's amazing! [short pause] But how did you discover this?"
EXPERT: "[thoughtful] Well, [inhales] it started with an unusual observation..."
```

### In Q&A Responses

Add tags to make answers more engaging:

```python
# Before generating TTS
if "surprising" in question.lower():
    answer = f"[gasps] {answer}"
elif "complex" in question.lower():
    answer = f"[thoughtful] {answer}"
```

### Using Helper Methods

The service includes helper methods:

```python
from app.services.elevenlabs_service import elevenlabs_service

# Add single tag
text = elevenlabs_service.add_audio_tag("Let me think", "thoughtful")
# Output: "[thoughtful] Let me think"

# Wrap with pauses
text = elevenlabs_service.wrap_with_pause("This is important", "short pause")
# Output: "[short pause] This is important [short pause]"

# Generate audio
audio = await elevenlabs_service.text_to_speech(text, voice_id)
```

## Examples for Different Scenarios

### 1. Introducing a Complex Topic

```python
expert_text = "[clears throat] This is a complex topic. [short pause] [thoughtful] Let me break it down step by step. [inhales] First, we need to understand the basics."
```

### 2. Expressing Surprise at Results

```python
host_text = "[gasps] Wait, you're saying it increased by 300%? [short pause] [confused] How is that even possible?"
expert_text = "[chuckles] I know, [thoughtful] it surprised us too. [exhales] Here's what we found..."
```

### 3. Building Suspense

```python
expert_text = "[whispers] What we discovered next changed everything. [long pause] [inhales sharply] The data showed something we never expected."
```

### 4. Expressing Relief or Understanding

```python
host_text = "[relieved] Ah! [laughs] Now it all makes sense. [short pause] So that's why the earlier results were inconsistent!"
```

### 5. Handling Interruptions (Q&A)

```python
# Transition to question
host_text = "[short pause] Any questions so far? [thoughtful] This is a good point to pause."

# Acknowledging question
host_text = "[thoughtful] Hmm, that's a great question. [short pause] What do you think, Expert?"

# Expert answering
expert_text = "[clears throat] Excellent question. [thoughtful] Let me address that. [inhales] The key factor here is..."
```

## Technical Implementation

### Model Configuration

The service is configured to use `eleven_turbo_v2_5` which supports v3 features:

```python
audio = self.client.text_to_speech.convert(
    voice_id=voice_id,
    text=text,  # Text can include [audio tags]
    model_id="eleven_turbo_v2_5",  # v3 compatible model
    output_format="mp3_44100_128"
)
```

### Voice Settings

Adjust voice settings for better tag interpretation:

```python
# In .env or configuration
ELEVENLABS_HOST_VOICE_ID=XA2bIQ92TabjGbpO2xRr    # Warm, expressive
ELEVENLABS_EXPERT_VOICE_ID=PoHUWWWMHFrA8z7Q88pu  # Clear, authoritative
```

## Testing Audio Tags

Test different tags to find what works best:

```python
test_phrases = [
    "[thoughtful] Interesting question.",
    "[chuckles] That's one way to look at it!",
    "[gasps] Really? [short pause] Tell me more.",
    "[sighs] It's complicated. [long pause] Let me explain.",
    "[whispers] This is the crucial part.",
    "[relieved] Finally! [laughs] We got it!"
]

for phrase in test_phrases:
    await elevenlabs_service.text_to_speech(phrase, voice_id, f"test_{i}.mp3")
```

## Tips for Podcast Quality

1. **Start segments with breath**: `[inhales] Welcome back...`
2. **Use pauses before key points**: `[long pause] The most important finding was...`
3. **Add reactions to engage**: `[gasps] That's incredible!`
4. **End with natural cadence**: `...and that's the conclusion. [exhales]`
5. **Match emotion to content**: Serious topics → fewer laughs, lighter topics → more chuckles

## Limitations

- Tags work best with natural, audible actions
- Overly abstract tags may not work well
- Some tags may sound different with different voices
- Tag interpretation can vary slightly between generations

## Further Experimentation

Try custom tags for your use case:
- `[contemplative]`
- `[enthusiastic]`
- `[doubtful]`
- `[amazed]`
- `[understanding]`

The v3 model is trained to interpret a wide range of bracketed emotional and performance directions, so feel free to experiment!
