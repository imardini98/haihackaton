import { requestJson } from './http';

// Types based on api-spec.json schemas

export interface ArxivPaper {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  pdf_url: string;
  published_date: string;
  categories: string[];
}

export interface Paper {
  id: string;
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract?: string | null;
  content?: string | null;
  pdf_url?: string | null;
  published_date?: string | null;
  categories: string[];
  created_at: string;
}

export interface PaperListResponse {
  papers: Paper[];
  total: number;
}

export interface PaperSearchRequest {
  query: string;
  max_results?: number;
  sort_by?: string;
}

export interface PaperIngestRequest {
  arxiv_id: string;
}

/**
 * Search ArXiv for papers. No auth required.
 */
export async function searchPapers(
  query: string,
  maxResults: number = 5
): Promise<ArxivPaper[]> {
  return requestJson<ArxivPaper[]>('/api/v1/papers/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      max_results: maxResults,
      sort_by: 'submitted',
    } satisfies PaperSearchRequest),
  });
}

/**
 * Ingest a paper from ArXiv by ID. Requires auth.
 */
export async function ingestPaper(
  arxivId: string,
  token: string
): Promise<Paper> {
  return requestJson<Paper>('/api/v1/papers/ingest', {
    method: 'POST',
    token,
    body: JSON.stringify({ arxiv_id: arxivId } satisfies PaperIngestRequest),
  });
}

/**
 * List all papers for the current user. Requires auth.
 */
export async function listPapers(token: string): Promise<PaperListResponse> {
  return requestJson<PaperListResponse>('/api/v1/papers', {
    method: 'GET',
    token,
  });
}

/**
 * Get a specific paper by ID. Requires auth.
 */
export async function getPaper(paperId: string, token: string): Promise<Paper> {
  return requestJson<Paper>(`/api/v1/papers/${paperId}`, {
    method: 'GET',
    token,
  });
}

/**
 * Delete a paper. Requires auth.
 */
export async function deletePaper(
  paperId: string,
  token: string
): Promise<void> {
  await requestJson(`/api/v1/papers/${paperId}`, {
    method: 'DELETE',
    token,
  });
}
