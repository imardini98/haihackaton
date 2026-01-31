# Project Plan & Timeline – pod.ask

This document captures the **execution plan and work distribution** during the hackathon.
It exists to make the team’s approach, priorities, and decision-making transparent.

---

## 👥 Role Overview

**Kevin**  
Product direction, USP, scope control, pitch & demo narrative

**Sam**  
Autonomous research, synthesis, content segmentation, Q&A logic

**Rajn**  
Audio generation (podcast + answers) using ElevenLabs

**Ivan**  
Interaction logic, latency handling, audio playback & resume

**Florian**  
Branding, UI/UX, overall experience clarity

---

## ⏱ Project Timeline

# Saturday
### 14:00–15:00 | Alignment & Scope

**All**

- Lock product definition:
  Topic → autonomous research → podcast → ✋ interrupt → question → spoken answer → resume
- User input: **topic only**

**Responsibilities**
- Kevin: USP definition, demo story, scope freeze
- Florian: UI wireframes (v0)
- Sam: Prompt strategy & segment schema

---

### 15:00–17:00 | Autonomous Research & Synthesis

**Sam** (Gemini, Manus, Cursor)

- Topic-based source discovery (papers, newsletters)
- Filtering & cross-source synthesis
- Output:
  - Podcast script
  - Segment-aware JSON structure

**Kevin**
- Validate clarity and narrative quality

---

### 16:00–18:00 | Audio Pipeline & Player

**Rajn** (ElevenLabs)

- Script → podcast audio
- Short answers → audio snippets

**Ivan** (Cursor)

- Audio player
- Play / pause / resume
- Timestamp tracking

---

### 18:00–20:00 | End-to-End Podcast Flow

**Florian** (v0)

- Final UI:
  - Topic input
  - Audio player
  - ✋ interrupt button

**Ivan**
- UI ↔ audio integration

**Sam**
- Prompt tuning for spoken language

**Milestone**
- Enter topic → podcast plays end-to-end

---

### 20:00–22:00 | ✋ Raise Hand (Core Feature)

**Ivan**
- Pause on ✋
- Precise resume after answer

**Sam**
- Segment-aware Q&A (explanation-only, no derailment)

**Rajn**
- Fast spoken answer generation

**Milestone**
- Interrupt → ask → spoken answer → resume seamlessly

---

### 22:00–00:00 | Stability & Polish

- Florian: UI polish
- Ivan: Latency & edge cases
- Sam: Shorter, clearer answers

---
# Sunday
### 09:00 - 10:00 | Demo Preparation

- Kevin: Pitch & demo script
- All: Live demo rehearsal

---

### 11:00–12:00 | Freeze & Backup

- Final fixes
- Optional demo video
- Code freeze

### 14:00 | Submit of the Project

**Rule:**  
If it doesn’t improve the ✋ interruption experience, it doesn’t ship.
