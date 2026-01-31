const baseUrlInput = document.getElementById("baseUrl");
const podcastJsonInput = document.getElementById("podcastJson");
const hostGenderInput = document.getElementById("hostGender");
const expertGenderInput = document.getElementById("expertGender");
const hostVoiceIdInput = document.getElementById("hostVoiceId");
const expertVoiceIdInput = document.getElementById("expertVoiceId");
const sessionIdEl = document.getElementById("sessionId");
const sessionVoicesEl = document.getElementById("sessionVoices");
const logEl = document.getElementById("log");
const raiseHandTextInput = document.getElementById("raiseHandText");
const answerJsonInput = document.getElementById("answerJson");
const segmentIdInput = document.getElementById("segmentId");

const createSessionBtn = document.getElementById("createSessionBtn");
const getVoicesBtn = document.getElementById("getVoicesBtn");
const startSegmentBtn = document.getElementById("startSegmentBtn");
const raiseHandTextBtn = document.getElementById("raiseHandTextBtn");
const clarifyBtn = document.getElementById("clarifyBtn");
const answerBtn = document.getElementById("answerBtn");
const resumeBtn = document.getElementById("resumeBtn");
const refreshStateBtn = document.getElementById("refreshStateBtn");
const getSessionVoicesBtn = document.getElementById("getSessionVoicesBtn");
const generateSegmentAudioBtn = document.getElementById("generateSegmentAudioBtn");

let currentSessionId = null;

const defaultPodcast = {
  metadata: {
    title: "Transformers in Medical Imaging: A Deep Dive",
    summary:
      "We explore three groundbreaking papers on applying transformer architectures to medical image analysis, breaking down the novel attention mechanisms and what the clinical results actually mean.",
    sources_analyzed: 3,
    estimated_duration_minutes: 14,
    primary_topics: [
      "transformers",
      "medical imaging",
      "attention mechanisms",
      "clinical AI",
    ],
    voices: {
      host: "host_voice_id",
      expert: "expert_voice_id",
    },
  },
  segments: [
    {
      id: 1,
      topic_label: "Introduction",
      dialogue: [
        {
          speaker: "host",
          text: "Welcome to PodAsk. Today—transformers in medical imaging. Three papers, some big claims. What's the story?",
        },
        {
          speaker: "expert",
          text: "Transformers are now being used for CT scans, MRIs, X-rays. These papers focus on tumor detection with different approaches.",
        },
      ],
      key_terms: ["transformers", "medical imaging", "tumor detection"],
      difficulty_level: "beginner",
      source_reference: "Introduction synthesis",
      is_interruptible: true,
      transition_to_question: "Any questions before we dive in?",
      resume_phrase: "Alright, let's look at Stanford's approach.",
    },
    {
      id: 2,
      topic_label: "Stanford's Method",
      dialogue: [
        { speaker: "host", text: "Stanford's claiming 23% improvement. How?" },
        {
          speaker: "expert",
          text: "Hierarchical attention pooling. The model zooms into suspicious regions first, then analyzes in detail—like a radiologist would.",
        },
      ],
      key_terms: ["hierarchical attention pooling", "attention mechanism"],
      difficulty_level: "intermediate",
      source_reference: "Paper_01_Chen_et_al_Stanford",
      is_interruptible: true,
      transition_to_question: "Questions on the methodology?",
      resume_phrase: "Okay, let's talk about how they measured that 23%.",
    },
    {
      id: 3,
      topic_label: "Validation Results",
      dialogue: [
        { speaker: "host", text: "How did they validate those numbers?" },
        {
          speaker: "expert",
          text: "F1 score: 0.89 versus 0.72 baseline. Tested across 12,000 CT scans from three hospitals. P-value under 0.001.",
        },
      ],
      key_terms: ["F1 score", "cross-hospital validation", "p-value"],
      difficulty_level: "intermediate",
      source_reference: "Paper_01_Section_4.2",
      is_interruptible: true,
      transition_to_question: "Any questions on the stats?",
      resume_phrase: "Now, what does this mean for actual hospitals?",
    },
    {
      id: 4,
      topic_label: "Clinical Implications",
      dialogue: [
        { speaker: "host", text: "When will we see this in clinics?" },
        {
          speaker: "expert",
          text: "Accuracy is there, but FDA approval, system integration, and training take time. Realistically, 2-3 years out.",
        },
      ],
      key_terms: ["FDA approval", "clinical integration"],
      difficulty_level: "beginner",
      source_reference: "Paper_01_Discussion",
      is_interruptible: true,
      transition_to_question: "Questions on the timeline?",
      resume_phrase: "Let's wrap up with the key takeaways.",
    },
  ],
};

const defaultAnswer = [
  { speaker: "host", text: "Great question! Here's the short version." },
  {
    speaker: "expert",
    text: "The p-value shows how unlikely the results are if there was no real effect. Under 0.001 is very strong.",
  },
  { speaker: "host", text: "And that makes the result statistically robust." },
];

function log(data) {
  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  logEl.textContent = `${new Date().toLocaleTimeString()}:\n${text}\n\n${
    logEl.textContent || ""
  }`;
}

function getBaseUrl() {
  return baseUrlInput.value.replace(/\/$/, "");
}

function requireSession() {
  if (!currentSessionId) {
    throw new Error("No session ID. Create a session first.");
  }
  return currentSessionId;
}

function setSession(sessionId, voices) {
  currentSessionId = sessionId;
  sessionIdEl.textContent = sessionId || "Not created";
  sessionVoicesEl.textContent = voices
    ? JSON.stringify(voices)
    : "Not assigned";
}

function parseJsonSafe(value) {
  try {
    return JSON.parse(value);
  } catch (err) {
    throw new Error(`Invalid JSON: ${err.message}`);
  }
}

async function request(path, options = {}) {
  const url = `${getBaseUrl()}${path}`;
  const res = await fetch(url, options);
  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    throw new Error(
      typeof data === "string" ? data : JSON.stringify(data, null, 2)
    );
  }
  return data;
}

createSessionBtn.addEventListener("click", async () => {
  try {
    const podcast = parseJsonSafe(podcastJsonInput.value);
    const payload = {
      podcast,
      host_gender: hostGenderInput.value || null,
      expert_gender: expertGenderInput.value || null,
      host_voice_id: hostVoiceIdInput.value || null,
      expert_voice_id: expertVoiceIdInput.value || null,
    };

    const data = await request("/podcast/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSession(data.session_id, data.voices);
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

getVoicesBtn.addEventListener("click", async () => {
  try {
    const data = await request("/podcast/voices");
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

startSegmentBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const data = await request(`/podcast/session/${sessionId}/start`, {
      method: "POST",
    });
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

raiseHandTextBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const question = raiseHandTextInput.value.trim();
    if (!question) throw new Error("Please enter a question.");

    const data = await request(`/podcast/session/${sessionId}/raise-hand`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

clarifyBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const data = await request(`/podcast/session/${sessionId}/clarify`, {
      method: "POST",
    });
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

answerBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const answerDialogue = parseJsonSafe(answerJsonInput.value);
    const data = await request(`/podcast/session/${sessionId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer_dialogue: answerDialogue }),
    });
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

resumeBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const data = await request(`/podcast/session/${sessionId}/resume`, {
      method: "POST",
    });
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

refreshStateBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const data = await request(`/podcast/session/${sessionId}`);
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

getSessionVoicesBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const data = await request(`/podcast/session/${sessionId}/voices`);
    setSession(sessionId, data);
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

generateSegmentAudioBtn.addEventListener("click", async () => {
  try {
    const sessionId = requireSession();
    const segmentId = segmentIdInput.value || "1";
    const data = await request(
      `/podcast/session/${sessionId}/generate-segment-audio/${segmentId}`,
      { method: "POST" }
    );
    log(data);
  } catch (err) {
    log(`Error: ${err.message}`);
  }
});

podcastJsonInput.value = JSON.stringify(defaultPodcast, null, 2);
answerJsonInput.value = JSON.stringify(defaultAnswer, null, 2);
