const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

// credentials: "include" is mandatory — tells browser to send HttpOnly cookies
async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
}

export async function register(email: string, password: string, full_name?: string): Promise<User> {
  const res = await apiFetch("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail);
  }
  return res.json();
}

export async function login(email: string, password: string): Promise<User> {
  const res = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail);
  }
  // FastAPI sets the HttpOnly cookies in the response — we just return the user
  return res.json();
}

export async function logout(): Promise<void> {
  await apiFetch("/api/auth/logout", { method: "POST" });
  // FastAPI clears the cookies in the response
}

export async function getMe(): Promise<User | null> {
  const res = await apiFetch("/api/auth/me");
  if (res.status === 401) return null;
  if (!res.ok) return null;
  return res.json();
}

export async function refreshTokens(): Promise<boolean> {
  const res = await apiFetch("/api/auth/refresh", { method: "POST" });
  return res.ok;
}

// ── Documents ─────────────────────────────────────────────────────────────

export interface Document {
  id: number;
  filename: string;
  title: string;
  page_count: number;
  word_count: number;
  chunk_count: number;
  status: string;
  error_message: string | null;
  uploaded_at: string;
  indexed_at: string | null;
}

export interface DocumentStatus {
  id: number;
  status: string;
  chunk_count: number;
  error_message: string | null;
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  // No Content-Type header here — the browser sets the multipart boundary itself
  const res = await fetch(`${API_URL}/api/documents`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail);
  }
  return res.json();
}

export async function listDocuments(): Promise<Document[]> {
  const res = await apiFetch("/api/documents");
  if (!res.ok) throw new Error("Failed to load documents");
  return res.json();
}

export async function getDocument(id: number): Promise<Document> {
  const res = await apiFetch(`/api/documents/${id}`);
  if (!res.ok) throw new Error("Failed to load document");
  return res.json();
}

export async function getDocumentStatus(id: number): Promise<DocumentStatus> {
  const res = await apiFetch(`/api/documents/${id}/status`);
  if (!res.ok) throw new Error("Failed to load document status");
  return res.json();
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await apiFetch(`/api/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete document");
}

export async function getSummary(documentId: number): Promise<{ summary: string }> {
  const res = await apiFetch(`/api/documents/${documentId}/summary`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to summarize" }));
    throw new Error(err.detail);
  }
  return res.json();
}

// ── Chat ──────────────────────────────────────────────────────────────────

export interface CitedChunk {
  chunk_id: number;
  page_number: number;
  section_heading: string | null;
  document_id: number;
  document_title: string;
}

export interface ChatMessage {
  role: string;
  content: string;
  cited_chunks: CitedChunk[] | null;
}

export async function getChatHistory(documentId: number): Promise<ChatMessage[]> {
  const res = await apiFetch(`/api/documents/${documentId}/chat`);
  if (!res.ok) throw new Error("Failed to load chat history");
  return res.json();
}

export async function askQuestion(documentId: number, question: string): Promise<{ answer: string; cited_chunks: CitedChunk[] }> {
  const res = await apiFetch(`/api/documents/${documentId}/chat`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to get an answer" }));
    throw new Error(err.detail);
  }
  return res.json();
}

// ── Search ────────────────────────────────────────────────────────────────

export interface SearchResult {
  chunk_id: number;
  content: string;
  page_number: number;
  section_heading: string | null;
  document_id: number;
  document_title: string;
}

export async function searchDocuments(query: string): Promise<{ results: SearchResult[] }> {
  const res = await apiFetch("/api/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}
