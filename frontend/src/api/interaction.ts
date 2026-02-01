import { requestJson, getApiBaseUrl } from './http';

// Types based on api-spec.json schemas

export interface SessionStartRequest {
  podcast_id: string;
  segment_id: string;
}

export interface SessionStartResponse {
  session_id: string;
  podcast_id: string;
  current_segment_id: string;
  status: string;
}

export interface SessionUpdateRequest {
  current_segment_id: string;
  audio_timestamp?: number;
}

export interface SessionUpdateResponse {
  session_id: string;
  status: string;
}

export interface SessionResponse {
  id: string;
  podcast_id: string;
  current_segment_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AskTextRequest {
  session_id: string;
  question: string;
  audio_timestamp?: number;
}

export interface AskResponse {
  exchange_id: string;
  host_acknowledgment: string;
  expert_answer: string;
  host_audio_url?: string | null;
  expert_audio_url?: string | null;
  confidence: string;
  topics_discussed: string[];
}

export interface ContinueRequest {
  session_id: string;
  user_signal?: string;
}

export interface ContinueResponse {
  resume_line: string;
  resume_audio_url?: string | null;
  next_segment_id?: string | null;
}

export interface ProcessVoiceResponse {
  transcription: string;
  is_question: boolean;
  is_continue_signal: boolean;
  exchange?: AskResponse | null;
  resume?: ContinueResponse | null;
}

// --- API Functions ---

/**
 * Start a new listening session for a podcast. Requires auth.
 */
export async function startSession(
  podcastId: string,
  segmentId: string,
  token: string
): Promise<SessionStartResponse> {
  return requestJson<SessionStartResponse>('/api/v1/interaction/session/start', {
    method: 'POST',
    token,
    body: JSON.stringify({
      podcast_id: podcastId,
      segment_id: segmentId,
    } satisfies SessionStartRequest),
  });
}

/**
 * Update current position in listening session. Requires auth.
 */
export async function updateSession(
  sessionId: string,
  segmentId: string,
  token: string,
  audioTimestamp: number = 0
): Promise<SessionUpdateResponse> {
  return requestJson<SessionUpdateResponse>(
    `/api/v1/interaction/session/${sessionId}/update`,
    {
      method: 'POST',
      token,
      body: JSON.stringify({
        current_segment_id: segmentId,
        audio_timestamp: audioTimestamp,
      } satisfies SessionUpdateRequest),
    }
  );
}

/**
 * Get session details. Requires auth.
 */
export async function getSession(
  sessionId: string,
  token: string
): Promise<SessionResponse> {
  return requestJson<SessionResponse>(
    `/api/v1/interaction/session/${sessionId}`,
    {
      method: 'GET',
      token,
    }
  );
}

/**
 * Submit a text question. Requires auth.
 */
export async function askTextQuestion(
  sessionId: string,
  question: string,
  token: string,
  audioTimestamp: number = 0
): Promise<AskResponse> {
  return requestJson<AskResponse>('/api/v1/interaction/ask-text', {
    method: 'POST',
    token,
    body: JSON.stringify({
      session_id: sessionId,
      question,
      audio_timestamp: audioTimestamp,
    } satisfies AskTextRequest),
  });
}

/**
 * Submit a voice question (audio file). Requires auth.
 * Transcribes and processes the audio.
 */
export async function askVoiceQuestion(
  sessionId: string,
  audioBlob: Blob,
  token: string
): Promise<ProcessVoiceResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'question.webm');

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/v1/interaction/ask?session_id=${encodeURIComponent(sessionId)}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    let message = `Request failed (${response.status})`;
    try {
      const payload = JSON.parse(text);
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // ignore parse error
    }
    throw new Error(message);
  }

  return response.json();
}

/**
 * Process continue signal and get resume line. Requires auth.
 */
export async function continueSession(
  sessionId: string,
  token: string,
  userSignal: string = 'okay thanks'
): Promise<ContinueResponse> {
  return requestJson<ContinueResponse>('/api/v1/interaction/continue', {
    method: 'POST',
    token,
    body: JSON.stringify({
      session_id: sessionId,
      user_signal: userSignal,
    } satisfies ContinueRequest),
  });
}
