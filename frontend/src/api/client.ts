// src/api/client.ts
// Central API client — tất cả call backend đi qua đây

function normalizeApiBaseUrl(value: string): string {
  return (value || "").trim().replace(/\/+$/, "");
}

function inferRenderBackendUrl(): string {
  if (typeof window === "undefined") return "";
  const host = window.location.hostname;
  if (!host.endsWith(".onrender.com")) return "";

  // Convention fallback: <name>-frontend.onrender.com -> <name>-backend.onrender.com
  const derivedHost = host.replace(/-frontend(?=\.onrender\.com$)/, "-backend");
  if (derivedHost === host) return "";
  return `${window.location.protocol}//${derivedHost}`;
}

const envApiBaseUrl = normalizeApiBaseUrl((import.meta as any).env?.VITE_API_URL || "");
const inferredApiBaseUrl = normalizeApiBaseUrl(inferRenderBackendUrl());

export const API_BASE_URL = envApiBaseUrl || inferredApiBaseUrl || "http://localhost:8000";
const API_TIMEOUT_MS = Number((import.meta as any).env?.VITE_API_TIMEOUT_MS || 15000);
const API_AUTH_TIMEOUT_MS = Number((import.meta as any).env?.VITE_API_AUTH_TIMEOUT_MS || 20000);
const UI_LANGUAGE_KEY = "ui_language";
const SUPPORTED_UI_LANGUAGES = new Set(["vi", "en", "zh", "ja", "fr"]);

function getUiLanguageHeader(): string {
  if (typeof window === "undefined") return "vi";
  const raw = (window.localStorage.getItem(UI_LANGUAGE_KEY) || "").trim().toLowerCase();
  return SUPPORTED_UI_LANGUAGES.has(raw) ? raw : "vi";
}

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

export interface User {
  id: number;
  username: string;
  email: string;
  nickname: string;
  language?: string;
  created_at: string;
}

export interface UserProfile {
  user_id: number;
  language?: string;
  role: "reader" | "writer" | "both";
  age_group: string;
  updated_at: string;
}

export interface UserWithProfile extends User {
  profile: UserProfile | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Paragraph {
  id: string;
  text: string;
}

export interface Document {
  document_id: string;
  title: string | null;
  source_type: "text" | "url" | "file";
  source_ref: string | null;
  paragraph_count: number;
  paragraphs: Paragraph[];
  created_at: string;
}

export interface DocumentSummary {
  document_id: string;
  title: string | null;
  source_type: string;
  paragraph_count: number;
  created_at: string;
}

export interface ToneAnalysis {
  overall_tone: string;
  sentiment: string;
  confidence_score: number;
}

export interface ParagraphAnalysis {
  paragraph_id: string;
  main_idea: string;
  notes: string;
}

export interface ReaderSummaryBreakdown {
  main_points: string[] | null;
  figures: string[] | null;
  argument_flow: string[] | null;
}

export interface DeepStyleAnalysis {
  emotional_tone: string | null;
  inflammatory_word_frequency: string | null;
  group_bias_level: string | null;
  notes: string | null;
}

export interface LogicDiagnostic {
  paragraph_id: string;
  issue_type: "fallacy" | "conclusion_jump" | "fear_appeal" | "spelling_grammar" | string;
  description: string;
  evidence: string | null;
  severity: "low" | "medium" | "high" | string | null;
}

export interface AnalysisResult {
  analysis_id: number;
  document_id: string;
  mode: "reader" | "writer";
  ai_provider: string | null;
  processing_ms: number | null;
  created_at: string;
  summary: string | null;
  tone_analysis: ToneAnalysis | null;
  paragraph_analyses: ParagraphAnalysis[] | null;
  // reader
  key_takeaways: string[] | null;
  reading_difficulty: string | null;
  readability_metrics: {
    accessibility_score: number | null;
    accessibility_label: string | null;
    avg_sentence_length_words: number | null;
    long_sentence_ratio: number | null;
    lexical_diversity: number | null;
    recommended_reader_profile: string | null;
    note: string | null;
  } | null;
  claim_checks: {
    paragraph_id: string;
    claim: string;
    evidence_in_text: string | null;
    support_level: string | null;
    risk_if_believed: string | null;
    verification_prompt: string | null;
  }[] | null;
  critical_reading_guard: {
    persuasion_risk: string | null;
    manipulation_signals: string[] | null;
    missing_context_flags: string[] | null;
    fact_check_actions: string[] | null;
    alternative_views: string[] | null;
    do_not_conclude_yet: string[] | null;
  } | null;
  logic_issues: { paragraph_id: string; issue: string }[] | null;
  reader_summary_breakdown: ReaderSummaryBreakdown | null;
  deep_style_analysis: DeepStyleAnalysis | null;
  logic_diagnostics: LogicDiagnostic[] | null;
  // writer
  style_issues: { paragraph_id: string; issue: string; severity: string }[] | null;
  rewrite_suggestions: { paragraph_id: string; original: string; suggestion: string }[] | null;
  overall_score: { clarity: number; coherence: number; style: number; note: string } | null;
}

export interface RewriteResult {
  rewrite_id: number;
  paragraph_id: string;
  goal: string;
  original_text: string;
  rewritten_text: string;
  explanation: string;
  ai_provider: string | null;
  processing_ms: number | null;
  created_at: string;
}

export interface ChatResponse {
  session_id: number;
  document_id: string;
  message_id: number;
  answer: string;
  referenced_paragraphs: string[];
  confidence: "high" | "medium" | "low" | null;
  out_of_scope: boolean;
  processing_ms: number | null;
  created_at: string;
}

export interface ChatMessage {
  message_id: number;
  role: "user" | "assistant";
  content: string;
  referenced_paragraphs: string[] | null;
  confidence: string | null;
  out_of_scope: boolean | null;
  processing_ms: number | null;
  created_at: string;
}

export interface ChatHistory {
  session_id: number;
  document_id: string;
  messages: ChatMessage[];
  created_at: string;
}

export interface HistoryStats {
  total_analyses: number;
  total_rewrites: number;
  total_chat_sessions: number;
  analyses_by_mode: Record<string, number>;
  most_active_document_id: string | null;
  most_active_document_title: string | null;
}

// ─────────────────────────────────────────────────────────────
// Core fetch wrapper
// ─────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (error: any) {
    if (error?.name === "AbortError") {
      throw new ApiError(408, "Yêu cầu quá thời gian, vui lòng thử lại");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

// ─────────────────────────────────────────────────────────────
// Token Storage (localStorage) - define early for apiFetch
// ─────────────────────────────────────────────────────────────

const TOKEN_KEY = "access_token";
const AUTH_TOKEN_EXCLUDED_PATHS = new Set(["/auth/login", "/auth/register"]);

function parseJwtExp(token: string): number | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const json = atob(padded);
    const payload = JSON.parse(json) as { exp?: unknown };
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

function getUsableToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;

  const exp = parseJwtExp(token);
  // If exp exists, treat token as expired 30s early to avoid race at edge of expiry.
  if (typeof exp === "number") {
    const nowSeconds = Math.floor(Date.now() / 1000);
    if (exp <= nowSeconds + 30) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
  }

  return token;
}

function shouldInvalidateAuthForUnauthorized(requestToken: string | null): boolean {
  const latestToken = localStorage.getItem(TOKEN_KEY);
  if (!requestToken) return !latestToken;
  return latestToken === requestToken;
}

export const tokenHelper = {
  save: (token: string) => {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clearLocal: () => {
    localStorage.removeItem(TOKEN_KEY);
  },
  clear: async () => {
    localStorage.removeItem(TOKEN_KEY);
    // Best-effort cookie cleanup without going through apiFetch 401 handler.
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Ignore network/logout errors
    }
  },
  get: () => {
    return getUsableToken();
  },
  exists: () => {
    return !!getUsableToken();
  },
};

// ─────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const shouldAttachToken = !AUTH_TOKEN_EXCLUDED_PATHS.has(path);
  const requestToken = shouldAttachToken ? tokenHelper.get() : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> ?? {}),
  };
  headers["X-UI-Language"] = getUiLanguageHeader();

  // Add Authorization header if token exists
  if (requestToken) {
    headers["Authorization"] = `Bearer ${requestToken}`;
  }

  const timeoutMs = path.startsWith("/auth/") ? API_AUTH_TIMEOUT_MS : API_TIMEOUT_MS;
  const res = await fetchWithTimeout(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",  // Still send cookies if they exist
    headers,
  }, timeoutMs);

  if (res.status === 401) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail ?? "Phiên đăng nhập hết hạn";
    const isAuthEntryPoint = path === "/auth/login" || path === "/auth/register";

    if (!isAuthEntryPoint) {
      // Guard against stale in-flight requests logging out a newly authenticated session.
      if (shouldInvalidateAuthForUnauthorized(requestToken)) {
        tokenHelper.clearLocal();
        window.dispatchEvent(new Event("auth:logout"));
      }
    }

    throw new ApiError(401, detail);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body?.detail ?? `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const requestToken = tokenHelper.get();
  const headers: HeadersInit = {};
  headers["X-UI-Language"] = getUiLanguageHeader();

  // Add Authorization header if token exists
  if (requestToken) {
    headers["Authorization"] = `Bearer ${requestToken}`;
  }

  const res = await fetchWithTimeout(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",  // Send cookies with upload
    body: formData,
    headers,
    // NOTE: không set Content-Type — browser tự set multipart/form-data + boundary
  }, API_TIMEOUT_MS);

  if (res.status === 401) {
    if (shouldInvalidateAuthForUnauthorized(requestToken)) {
      tokenHelper.clearLocal();
      window.dispatchEvent(new Event("auth:logout"));
    }
    throw new ApiError(401, "Phiên đăng nhập hết hạn");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body?.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

async function apiFetchBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const requestToken = tokenHelper.get();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> ?? {}),
  };
  headers["X-UI-Language"] = getUiLanguageHeader();

  if (requestToken) {
    headers["Authorization"] = `Bearer ${requestToken}`;
  }

  const res = await fetchWithTimeout(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  }, API_TIMEOUT_MS);

  if (res.status === 401) {
    if (shouldInvalidateAuthForUnauthorized(requestToken)) {
      tokenHelper.clearLocal();
      window.dispatchEvent(new Event("auth:logout"));
    }
    throw new ApiError(401, "Phiên đăng nhập hết hạn");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body?.detail ?? `HTTP ${res.status}`);
  }

  return res.blob();
}

// ─────────────────────────────────────────────────────────────
// Auth API
// ─────────────────────────────────────────────────────────────

export const authApi = {
  register: (payload: {
    username: string;
    password: string;
    nickname: string;
    age_group?: string;
  }) =>
    apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (username: string, password: string) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  refresh: () =>
    apiFetch<AuthResponse>("/auth/refresh", {
      method: "POST",
    }),

  me: () => apiFetch<UserWithProfile>("/auth/me"),

  updateProfile: (payload: Partial<Pick<UserProfile, "role" | "age_group">>) =>
    apiFetch<UserProfile>("/auth/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
};

// ─────────────────────────────────────────────────────────────
// Texts API
// ─────────────────────────────────────────────────────────────

export const textsApi = {
  uploadText: (payload: { text: string }) =>
    apiFetch<Document>("/texts/from-text", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadUrl: (payload: { url: string }) =>
    apiFetch<Document>("/texts/from-url", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadFile: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiUpload<Document>("/texts/from-file", fd);
  },

  list: () => apiFetch<DocumentSummary[]>("/texts/"),

  get: (documentId: string) => apiFetch<Document>(`/texts/${documentId}`),

  delete: (documentId: string) =>
    apiFetch<void>(`/texts/${documentId}`, { method: "DELETE" }),

  getOriginalFile: (documentId: string) =>
    apiFetchBlob(`/texts/${documentId}/original`),
};

// ─────────────────────────────────────────────────────────────
// Analysis API
// ─────────────────────────────────────────────────────────────

export const analysisApi = {
  analyze: (payload: {
    document_id: string;
    mode: "reader" | "writer";
    paragraphs: { id: string; text: string }[];
  }) =>
    apiFetch<AnalysisResult>("/analysis/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  get: (analysisId: number) => apiFetch<AnalysisResult>(`/analysis/${analysisId}`),

  history: (limit = 20, offset = 0) =>
    apiFetch<AnalysisResult[]>(`/analysis/history?limit=${limit}&offset=${offset}`),
};

// ─────────────────────────────────────────────────────────────
// Rewrite API
// ─────────────────────────────────────────────────────────────

export const rewriteApi = {
  presets: () => apiFetch<string[]>("/rewrite/presets"),

  rewrite: (payload: {
    paragraph_id: string;
    original_text: string;
    goal: string;
    document_id?: string;
  }) =>
    apiFetch<RewriteResult>("/rewrite/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  get: (rewriteId: number) => apiFetch<RewriteResult>(`/rewrite/${rewriteId}`),

  history: (limit = 20, offset = 0) =>
    apiFetch<RewriteResult[]>(`/rewrite/history?limit=${limit}&offset=${offset}`),
};

// ─────────────────────────────────────────────────────────────
// Chat API
// ─────────────────────────────────────────────────────────────

export const chatApi = {
  chat: (payload: {
    document_id?: string;
    context_text?: string;
    user_question: string;
    session_id: number | null;
  }) =>
    apiFetch<ChatResponse>("/chat/", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getSession: (sessionId: number) =>
    apiFetch<ChatHistory>(`/chat/sessions/${sessionId}`),

  listSessions: () =>
    apiFetch<{ session_id: number; document_id: string; message_count: number; created_at: string }[]>(
      "/chat/sessions"
    ),

  deleteSession: (sessionId: number) =>
    apiFetch<void>(`/chat/sessions/${sessionId}`, { method: "DELETE" }),
};

// ─────────────────────────────────────────────────────────────
// History API
// ─────────────────────────────────────────────────────────────

export const historyApi = {
  all: (limit = 30) => apiFetch<unknown[]>(`/history/all?limit=${limit}`),

  analyses: (params?: { mode?: string; document_id?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.mode) q.set("mode", params.mode);
    if (params?.document_id) q.set("document_id", params.document_id);
    if (params?.limit) q.set("limit", String(params.limit));
    return apiFetch<unknown[]>(`/history/analysis?${q}`);
  },

  rewrites: (documentId?: string) => {
    const q = documentId ? `?document_id=${documentId}` : "";
    return apiFetch<unknown[]>(`/history/rewrites${q}`);
  },

  chats: (documentId?: string) => {
    const q = documentId ? `?document_id=${documentId}` : "";
    return apiFetch<unknown[]>(`/history/chats${q}`);
  },

  stats: () => apiFetch<HistoryStats>("/history/stats"),
};

