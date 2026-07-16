"use client";

import { useState } from "react";
import Link from "next/link";
import { searchDocuments } from "@/lib/api";

interface SearchResult {
  chunk_id: number;
  content: string;
  page_number: number;
  section_heading: string | null;
  document_id: number;
  document_title: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true); setSearched(true);
    try {
      const res = await searchDocuments(query);
      setResults(res.results);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className="flex items-center gap-3 mb-6">
          <Link href="/dashboard" className="text-gray-400 hover:text-gray-700"><i className="ti ti-arrow-left" /></Link>
          <h1 className="text-2xl font-semibold text-gray-900">Search all documents</h1>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 mb-8">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search across all your documents…"
            className="flex-1 border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 bg-white"
          />
          <button type="submit" disabled={loading} className="bg-gray-900 text-white rounded-xl px-6 text-sm font-medium hover:bg-gray-700 disabled:opacity-40">Search</button>
        </form>

        {loading ? (
          <p className="text-sm text-gray-400">Searching…</p>
        ) : searched && results.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-10">No matching passages found.</p>
        ) : (
          <div className="space-y-3">
            {results.map(r => (
              <Link key={r.chunk_id} href={`/dashboard/documents/${r.document_id}`}
                className="block bg-white rounded-2xl border border-gray-200 p-5 hover:border-gray-400 transition-colors">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-700">{r.document_title}</span>
                  <span className="text-xs text-gray-400">· page {r.page_number}</span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">{r.content}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
