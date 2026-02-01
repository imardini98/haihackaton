/**
 * PodAsk – AI Development Podcast Simulation with Streaming Audio
 * Uses ElevenLabs streaming TTS for immediate playback.
 */

// ============== DOM Elements ==============
const startPodcastBtn = document.getElementById("startPodcastBtn");
const sessionInfoEl = document.getElementById("sessionInfo");
const playerSection = document.getElementById("playerSection");
const audioPlayer = document.getElementById("audioPlayer");
const playbackStatus = document.getElementById("playbackStatus");
const statusIcon = document.getElementById("statusIcon");
const segmentTopicEl = document.getElementById("segmentTopic");
const segmentDialogueEl = document.getElementById("segmentDialogue");
const skipSegmentBtn = document.getElementById("skipSegmentBtn");
const raiseHandSection = document.getElementById("raiseHandSection");
const qaPausedHint = document.getElementById("qaPausedHint");
const questionInput = document.getElementById("questionInput");
const raiseHandBtn = document.getElementById("raiseHandBtn");
const answerBox = document.getElementById("answerBox");
const answerContent = document.getElementById("answerContent");
const resumeAfterQaBtn = document.getElementById("resumeAfterQaBtn");
const logEl = document.getElementById("log");
const testConnectionBtn = document.getElementById("testConnectionBtn");

// ============== State ==============
let sessionId = null;
let sessionVoices = null;
let currentSegment = null;
let dialogueQueue = [];    // [{speaker, text, index}, ...]
let currentDialogueIndex = 0;
let isInQa = false;
let podcastFinished = false;
let isPlaying = false;

// ============== Helpers ==============
function getBaseUrl() {
  const input = document.getElementById("baseUrl");
  return (input ? input.value : "http://127.0.0.1:8001").replace(/\/$/, "");
}

function log(msg) {
  const line = `[${new Date().toLocaleTimeString()}] ${typeof msg === "string" ? msg : JSON.stringify(msg)}`;
  if (logEl) logEl.textContent = line + "\n" + (logEl.textContent || "");
}

function setStatus(text, type = "playing") {
  if (playbackStatus) playbackStatus.textContent = text;
  if (statusIcon) {
    statusIcon.textContent = type === "generating" ? "⏳" : type === "playing" ? "🔊" : "⏸️";
  }
  if (playbackStatus) {
    playbackStatus.classList.remove("generating", "playing", "paused");
    playbackStatus.classList.add(type);
  }
}

function setLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("loading", loading);
  const spinner = btn.querySelector(".spinner");
  if (loading && !spinner) {
    const s = document.createElement("span");
    s.className = "spinner";
    btn.prepend(s);
  } else if (!loading && spinner) spinner.remove();
}

const REQUEST_TIMEOUT_MS = 30000;

async function request(path, options = {}) {
  const url = `${getBaseUrl()}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);
    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await res.json() : await res.text();
    if (!res.ok) throw new Error(typeof data === "string" ? data : (data.detail || JSON.stringify(data)));
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") throw new Error("Request timed out");
    throw err;
  }
}

async function testConnection() {
  const url = getBaseUrl() + "/api/v1/simulation/ping";
  const statusEl = document.getElementById("connectionStatus");
  if (statusEl) statusEl.textContent = "Checking…";
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (res.ok && data.ok) {
      if (statusEl) statusEl.textContent = "Backend OK";
      log("Connection OK");
    } else {
      if (statusEl) statusEl.textContent = "Unexpected response";
    }
  } catch (err) {
    if (statusEl) statusEl.textContent = "Not reachable";
    log("Connection failed: " + err.message);
  }
}

// ============== Display ==============
function displaySegment(segment) {
  if (!segment) return;
  currentSegment = segment;
  segmentTopicEl.textContent = `Segment ${segment.id}: ${segment.topic_label || "–"}`;
  segmentDialogueEl.innerHTML = (segment.dialogue || [])
    .map((line, i) => `<div class="dialogue-line" data-index="${i}"><span class="speaker">${line.speaker}:</span> ${line.text}</div>`)
    .join("");
  playerSection.style.display = "block";
  raiseHandSection.style.display = "block";
}

function highlightLine(index, container = segmentDialogueEl) {
  const lines = container.querySelectorAll(".dialogue-line");
  lines.forEach((el, i) => el.classList.toggle("active", i === index));
}

function showAnswer(dialogue) {
  if (!dialogue || !dialogue.length) return;
  answerContent.innerHTML = dialogue
    .map((line, i) => `<div class="dialogue-line" data-index="${i}"><span class="speaker">${line.speaker}:</span> ${line.text}</div>`)
    .join("");
  answerBox.style.display = "block";
}

// ============== Streaming Audio Playback ==============
function getVoiceId(speaker) {
  if (!sessionVoices) return null;
  return speaker === "host" ? sessionVoices.host : sessionVoices.expert;
}

function buildStreamUrl(text, voiceId) {
  const params = new URLSearchParams({ text });
  if (voiceId) params.append("voice_id", voiceId);
  return `${getBaseUrl()}/api/v1/audio/stream?${params.toString()}`;
}

function playDialogueQueue(onComplete) {
  if (isInQa || currentDialogueIndex >= dialogueQueue.length) {
    isPlaying = false;
    if (onComplete) onComplete();
    return;
  }
  
  isPlaying = true;
  const item = dialogueQueue[currentDialogueIndex];
  const voiceId = getVoiceId(item.speaker);
  const streamUrl = buildStreamUrl(item.text, voiceId);
  
  highlightLine(item.index);
  setStatus(`Playing: ${item.speaker}`, "playing");
  log(`Streaming: ${item.speaker} (line ${item.index + 1})`);
  
  audioPlayer.src = streamUrl;
  audioPlayer.onended = () => {
    currentDialogueIndex++;
    playDialogueQueue(onComplete);
  };
  audioPlayer.onerror = (e) => {
    log("Audio error, skipping line");
    currentDialogueIndex++;
    playDialogueQueue(onComplete);
  };
  audioPlayer.play().catch((e) => {
    log("Playback error: " + e.message);
    currentDialogueIndex++;
    playDialogueQueue(onComplete);
  });
}

function stopPlayback() {
  audioPlayer.pause();
  audioPlayer.src = "";
  isPlaying = false;
}

// ============== Play Segment ==============
function playSegment(segment) {
  if (!segment || !segment.dialogue) return;
  
  dialogueQueue = segment.dialogue.map((line, i) => ({
    speaker: line.speaker,
    text: line.text,
    index: i
  }));
  currentDialogueIndex = 0;
  
  log(`Playing segment ${segment.id}: ${segment.topic_label}`);
  setStatus("Starting…", "generating");
  
  playDialogueQueue(() => {
    if (!isInQa && !podcastFinished) {
      log("Segment complete. Moving to next…");
      advanceToNextSegment();
    }
  });
}

// ============== Segment Navigation ==============
async function advanceToNextSegment() {
  if (!sessionId || isInQa) return;
  stopPlayback();
  try {
    const res = await request(`/api/v1/interaction/continue?session_id=${sessionId}`, { method: "POST" });
    if (res.message && res.message.includes("complete")) {
      podcastFinished = true;
      log("Podcast complete!");
      setStatus("Podcast complete", "paused");
      segmentTopicEl.textContent = "Podcast complete";
      segmentDialogueEl.innerHTML = "<p>Thanks for listening!</p>";
      return;
    }
    if (res.next_segment) {
      displaySegment(res.next_segment);
      playSegment(res.next_segment);
    }
  } catch (err) {
    log("Error: " + err.message);
  }
}

// ============== Event Listeners ==============
if (testConnectionBtn) testConnectionBtn.addEventListener("click", testConnection);

startPodcastBtn.addEventListener("click", async () => {
  try {
    setLoading(startPodcastBtn, true);
    isInQa = false;
    podcastFinished = false;
    stopPlayback();
    
    log("Loading AI Development podcast…");
    const podcast = await request("/api/v1/simulation/podcast");
    
    log("Creating session…");
    const session = await request("/api/v1/podcasts/session?host_gender=female&expert_gender=male", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(podcast),
    });
    sessionId = session.id;
    sessionVoices = session.voices;
    sessionInfoEl.textContent = sessionId;
    log("Session: " + sessionId + " (voices: " + JSON.stringify(sessionVoices) + ")");
    
    const start = await request(`/api/v1/podcasts/session/${sessionId}/start`, { method: "POST" });
    const seg = start.segment || start.current_segment || start;
    
    if (!seg || !seg.id) {
      log("Error: No segment found in response");
      return;
    }
    
    displaySegment(seg);
    playSegment(seg);
    
    if (qaPausedHint) qaPausedHint.style.display = "none";
    if (resumeAfterQaBtn) resumeAfterQaBtn.style.display = "none";
  } catch (err) {
    log("Error: " + (err.message || String(err)));
  } finally {
    setLoading(startPodcastBtn, false);
  }
});

skipSegmentBtn.addEventListener("click", () => {
  if (!sessionId) return;
  advanceToNextSegment();
});

// ============== Raise Hand ==============
raiseHandBtn.addEventListener("click", async () => {
  const question = questionInput ? questionInput.value.trim() : "";
  if (!sessionId) {
    log("Start the podcast first.");
    return;
  }
  if (!question) {
    log("Type a question first.");
    return;
  }
  try {
    setLoading(raiseHandBtn, true);
    
    // Pause audio and enter Q&A mode
    stopPlayback();
    isInQa = true;
    if (qaPausedHint) qaPausedHint.style.display = "block";
    answerBox.style.display = "none";
    
    log("Raising hand: " + question);
    setStatus("Paused – asking question", "paused");
    
    await request("/api/v1/interaction/ask-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question }),
    });
    
    log("Simulating research…");
    setStatus("Researching…", "generating");
    await new Promise((r) => setTimeout(r, 1500));
    
    const sim = await request("/api/v1/simulation/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const answerDialogue = sim.answer_dialogue || [];
    
    // Store answer in backend
    await request(`/api/v1/interaction/${sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer_dialogue: answerDialogue }),
    });
    
    showAnswer(answerDialogue);
    
    // Play answer using streaming
    log("Playing answer…");
    const answerQueue = answerDialogue.map((line, i) => ({
      speaker: line.speaker,
      text: line.text,
      index: i
    }));
    
    let answerIndex = 0;
    const playAnswerNext = () => {
      if (answerIndex >= answerQueue.length) {
        log("Answer complete. Click 'Resume podcast' to continue.");
        setStatus("Answer complete", "paused");
        if (resumeAfterQaBtn) resumeAfterQaBtn.style.display = "inline-block";
        return;
      }
      const item = answerQueue[answerIndex];
      const voiceId = getVoiceId(item.speaker);
      const streamUrl = buildStreamUrl(item.text, voiceId);
      
      highlightLine(item.index, answerContent);
      setStatus(`Answer: ${item.speaker}`, "playing");
      
      audioPlayer.src = streamUrl;
      audioPlayer.onended = () => {
        answerIndex++;
        playAnswerNext();
      };
      audioPlayer.onerror = () => {
        answerIndex++;
        playAnswerNext();
      };
      audioPlayer.play().catch(() => {
        answerIndex++;
        playAnswerNext();
      });
    };
    
    playAnswerNext();
    
  } catch (err) {
    log("Error: " + (err.message || String(err)));
    isInQa = false;
  } finally {
    setLoading(raiseHandBtn, false);
  }
});

// ============== Resume After Q&A ==============
resumeAfterQaBtn.addEventListener("click", async () => {
  if (!sessionId) return;
  try {
    setLoading(resumeAfterQaBtn, true);
    isInQa = false;
    if (qaPausedHint) qaPausedHint.style.display = "none";
    answerBox.style.display = "none";
    if (resumeAfterQaBtn) resumeAfterQaBtn.style.display = "none";
    
    const res = await request(`/api/v1/interaction/continue?session_id=${sessionId}`, { method: "POST" });
    if (res.message && res.message.includes("complete")) {
      podcastFinished = true;
      log("Podcast complete!");
      setStatus("Podcast complete", "paused");
      segmentTopicEl.textContent = "Podcast complete";
      segmentDialogueEl.innerHTML = "<p>Thanks for listening!</p>";
    } else if (res.next_segment) {
      displaySegment(res.next_segment);
      playSegment(res.next_segment);
    }
  } catch (err) {
    log("Error: " + err.message);
  } finally {
    setLoading(resumeAfterQaBtn, false);
  }
});
