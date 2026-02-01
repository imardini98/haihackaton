import { requestJson } from './http';

// Types based on updated api-spec.json schemas

// --- Search Types (Semantic Search) ---

export interface ArxivSearchRequest {
  query: string;
  context?: string;
  max_results?: number; // default 20
  top_n?: number; // default 5
  max_pdf_pages?: number; // default 50
}

export interface RefinedQuery {
  refined_query: string;
  key_concepts: string[];
  search_focus: string;
  additional_filters?: Record<string, unknown> | null;
}

export interface PaperSummary {
  index: number;
  title: string;
  authors: string; // Note: string, not array
  arxiv_id: string;
  summary: string;
  published: string;
  updated: string;
  categories: string[];
  primary_category: string;
  pdf_link: string;
  abstract_link: string;
  page_count?: number | null;
  relevance_score?: number | null;
  relevance_reason?: string | null;
  key_contributions?: string | null;
}

export interface ArxivSearchResponse {
  query: string;
  timestamp: string;
  total_papers_found: number;
  papers_excluded_by_page_limit: number;
  papers_after_filtering: number;
  top_papers_count: number;
  refined_query: RefinedQuery;
  overall_analysis: string;
  top_papers: PaperSummary[];
  top_5_links: string[];
  excluded_papers?: Record<string, unknown>[] | null;
}

// --- Ingested Paper Types ---

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

export interface PaperIngestRequest {
  arxiv_id: string;
}

// --- API Functions ---

/**
 * Semantic search for ArXiv papers using Gemini AI. No auth required.
 * Returns ranked papers with relevance scores and key contributions.
 */
export async function searchPapers(
  query: string,
  options: {
    context?: string;
    maxResults?: number;
    topN?: number;
    maxPdfPages?: number;
  } = {}
): Promise<ArxivSearchResponse> {
  return requestJson<ArxivSearchResponse>('/api/v1/papers/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      context: options.context || '',
      max_results: 10,
      top_n: options.topN ?? 5,
      max_pdf_pages: options.maxPdfPages ?? 50,
    } satisfies ArxivSearchRequest),
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
