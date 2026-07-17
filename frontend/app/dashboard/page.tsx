"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";
import { getMe, listDocuments, uploadDocument, deleteDocument, getDocumentStatus, Document, User } from "@/lib/api";

const IN_PROGRESS_STATUSES = ["uploading", "extracting", "chunking", "embedding"];

const STATUS_LABELS: Record<string, string> = {
  uploading: "Uploading",
  extracting: "Extracting",
  chunking: "Chunking",
  embedding: "Indexing",
  ready: "Ready",
  failed: "Failed",
};

function StatusBadge({ status }: { status: string }) {
  const label = STATUS_LABELS[status] || status;
  const color =
    status === "ready" ? "bg-green-50 text-green-700"
    : status === "failed" ? "bg-red-50 text-red-600"
    : "bg-blue-50 text-blue-600";
  return <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${color}`}>{label}</span>;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getMe().then(setUser);
    listDocuments()
      .then(setDocuments)
      .finally(() => setLoading(false));
  }, []);

  // Poll status for any document still processing, every 2s, until it's ready/failed
  useEffect(() => {
    const pending = documents.filter(d => IN_PROGRESS_STATUSES.includes(d.status));
    if (pending.length === 0) return;

    const interval = setInterval(async () => {
      const updates = await Promise.all(
        pending.map(d => getDocumentStatus(d.id).catch(() => null))
      );
      setDocuments(docs =>
        docs.map(d => {
          const update = updates.find(u => u && u.id === d.id);
          return update ? { ...d, ...update } : d;
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleFileSelect = useCallback(async (file: File | undefined) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      setDocuments(docs => [doc, ...docs]);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, []);

  async function handleDelete(id: number) {
    setDocuments(docs => docs.filter(d => d.id !== id));
    try {
      await deleteDocument(id);
    } catch {
      // Best-effort — reload the list if the delete failed server-side
      listDocuments().then(setDocuments);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-10">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Your documents</h1>
            {user && <p className="text-sm text-gray-400 mt-0.5">Signed in as {user.email}</p>}
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard/search" className="text-sm text-gray-500 hover:text-gray-800">
              <i className="ti ti-search" /> Search all
            </Link>
            <LogoutButton />
          </div>
        </div>

        <label className="block bg-white rounded-2xl border-2 border-dashed border-gray-300 p-8 text-center mb-6 cursor-pointer hover:border-gray-400 transition-colors">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            disabled={uploading}
            onChange={e => handleFileSelect(e.target.files?.[0])}
          />
          <i className="ti ti-upload text-2xl text-gray-400" />
          <p className="text-sm text-gray-600 mt-2">
            {uploading ? "Uploading…" : "Click to upload a PDF"}
          </p>
          <p className="text-xs text-gray-400 mt-1">Up to 20MB</p>
        </label>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 rounded-lg px-4 py-2 mb-6">{error}</p>
        )}

        {loading ? (
          <p className="text-sm text-gray-400 text-center py-10">Loading…</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-10">No documents yet — upload one to get started.</p>
        ) : (
          <div className="space-y-3">
            {documents.map(doc => (
              <div key={doc.id} className="bg-white rounded-2xl border border-gray-200 p-5 flex items-center justify-between gap-4">
                {doc.status === "ready" ? (
                  <Link href={`/dashboard/documents/${doc.id}`} className="min-w-0 flex-1 group">
                    <p className="text-sm font-medium text-gray-900 truncate group-hover:underline">{doc.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{doc.page_count} pages · {doc.chunk_count} chunks</p>
                  </Link>
                ) : (
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
                    {doc.status === "failed" && doc.error_message && (
                      <p className="text-xs text-red-500 mt-0.5 truncate">{doc.error_message}</p>
                    )}
                  </div>
                )}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <StatusBadge status={doc.status} />
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="text-gray-300 hover:text-red-500 transition-colors"
                    aria-label="Delete document"
                  >
                    <i className="ti ti-trash" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
