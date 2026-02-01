import { requestJson, getApiBaseUrl } from './http';

// Types based on api-spec.json schemas

export interface DialogueLine {
  speaker: string;
  text: string;
  audio_url?: string | null;
}

export interface Segment {
  id: string;
  sequence: number;
  topic_label?: string | null;
  dialogue: DialogueLine[];
  key_terms: string[];
  difficulty_level?: string | null;
  audio_url?: string | null;
  duration_seconds?: number | null;
  transition_to_question?: string | null;
  resume_phrase?: string | null;
}

export interface Podcast {
  id: string;
  title: string;
  summary?: string | null;
  topic?: string | null;
  paper_ids: string[];
  status: 'pending' | 'generating' | 'ready' | 'failed';
  total_duration_seconds?: number | null;
  error_message?: string | null;
  created_at: string;
  segments: Segment[];
}

export interface PodcastListResponse {
  podcasts: Podcast[];
  total: number;
}

export interface PodcastStatusResponse {
  id: string;
  status: string;
  error_message?: string | null;
}

export interface PodcastGenerateRequest {
  paper_ids: string[];
  topic: string;
  difficulty_level?: string;
}

// --- API Functions ---

/**
 * Start podcast generation from papers. Requires auth.
 * Returns immediately, generation happens in background.
 */
export async function generatePodcast(
  paperIds: string[],
  topic: string,
  token: string,
  difficultyLevel: string = 'intermediate'
): Promise<Podcast> {
  return requestJson<Podcast>('/api/v1/podcasts/generate', {
    method: 'POST',
    token,
    body: JSON.stringify({
      paper_ids: paperIds,
      topic,
      difficulty_level: difficultyLevel,
    } satisfies PodcastGenerateRequest),
  });
}

/**
 * Get podcast generation status (for polling). Requires auth.
 */
export async function getPodcastStatus(
  podcastId: string,
  token: string
): Promise<PodcastStatusResponse> {
  return requestJson<PodcastStatusResponse>(
    `/api/v1/podcasts/${podcastId}/status`,
    {
      method: 'GET',
      token,
    }
  );
}

/**
 * Get podcast with all segments. Requires auth.
 */
export async function getPodcast(
  podcastId: string,
  token: string
): Promise<Podcast> {
  return requestJson<Podcast>(`/api/v1/podcasts/${podcastId}`, {
    method: 'GET',
    token,
  });
}

/**
 * List all podcasts for the current user. Requires auth.
 */
export async function listPodcasts(token: string): Promise<PodcastListResponse> {
  return requestJson<PodcastListResponse>('/api/v1/podcasts', {
    method: 'GET',
    token,
  });
}

/**
 * Delete a podcast and its segments. Requires auth.
 */
export async function deletePodcast(
  podcastId: string,
  token: string
): Promise<void> {
  await requestJson(`/api/v1/podcasts/${podcastId}`, {
    method: 'DELETE',
    token,
  });
}

/**
 * Get the audio URL for a specific segment.
 * Note: Returns URL string to use with Audio element.
 * Token must be passed as Authorization header when fetching.
 */
export function getSegmentAudioUrl(
  podcastId: string,
  segmentSequence: number
): string {
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}/api/v1/podcasts/${podcastId}/audio/${segmentSequence}`;
}

/**
 * Poll podcast status until ready or failed.
 */
export async function pollPodcastStatus(
  podcastId: string,
  token: string,
  options: {
    onStatusChange?: (status: PodcastStatusResponse) => void;
    intervalMs?: number;
    maxAttempts?: number;
  } = {}
): Promise<PodcastStatusResponse> {
  const { onStatusChange, intervalMs = 3000, maxAttempts = 100 } = options;
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getPodcastStatus(podcastId, token);

    if (onStatusChange) {
      onStatusChange(status);
    }

    if (status.status === 'ready') {
      return status;
    }

    if (status.status === 'failed') {
      throw new Error(status.error_message || 'Podcast generation failed');
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
    attempts++;
  }

  throw new Error('Podcast generation timed out');
}
