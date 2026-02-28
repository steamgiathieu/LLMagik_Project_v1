// src/api/client.ts
// Central API client — tất cả call backend đi qua đây

export const API_BASE_URL = (import.meta as any).env?.VITE_API_URL ?? "http://localhost:8000";

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
  language: string;
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

// ─────────────────────────────────────────────────────────────
// Token Storage (localStorage) - define early for apiFetch
// ─────────────────────────────────────────────────────────────

const TOKEN_KEY = "access_token";

export const tokenHelper = {
  save: (token: string) => {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    // Call logout endpoint to clear backend cookies
    return apiFetch<void>("/auth/logout", { method: "POST" }).catch(() => {
      // Ignore errors on logout
    });
  },
  get: () => {
    return localStorage.getItem(TOKEN_KEY);
  },
  exists: () => {
    return !!localStorage.getItem(TOKEN_KEY);
  },
};

// ─────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = tokenHelper.get();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> ?? {}),
  };

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    console.log(`[apiFetch] Sending request to ${path} with token`);
  } else {
    console.log(`[apiFetch] Sending request to ${path} WITHOUT token`);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",  // Still send cookies if they exist
    headers,
  });

  console.log(`[apiFetch] Response status: ${res.status} from ${path}`);

  if (res.status === 401) {
    console.log(`[apiFetch] Got 401, clearing token and dispatching logout`);
    // Clear auth state on unauthorized
    tokenHelper.clear();
    window.dispatchEvent(new Event("auth:logout"));
    throw new ApiError(401, "Phiên đăng nhập hết hạn");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body?.detail ?? `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = tokenHelper.get();
  const headers: HeadersInit = {};

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    console.log(`[apiUpload] Sending request to ${path} with token`);
  } else {
    console.log(`[apiUpload] Sending request to ${path} WITHOUT token`);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",  // Send cookies with upload
    body: formData,
    headers,
    // NOTE: không set Content-Type — browser tự set multipart/form-data + boundary
  });

  console.log(`[apiUpload] Response status: ${res.status} from ${path}`);

  if (res.status === 401) {
    console.log(`[apiUpload] Got 401, clearing token and dispatching logout`);
    tokenHelper.clear();
    window.dispatchEvent(new Event("auth:logout"));
    throw new ApiError(401, "Phiên đăng nhập hết hạn");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body?.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

async function apiFetchBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  const token = tokenHelper.get();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> ?? {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (res.status === 401) {
    tokenHelper.clear();
    window.dispatchEvent(new Event("auth:logout"));
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
    email: string;
    password: string;
    nickname: string;
    language?: string;
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

  updateProfile: (payload: Partial<Pick<UserProfile, "language" | "role" | "age_group">>) =>
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
    document_id: string;
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

