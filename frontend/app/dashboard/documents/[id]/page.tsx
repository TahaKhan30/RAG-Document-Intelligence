"use client";

import { useEffect, useState, useRef, use } from "react";
import Link from "next/link";
import { getDocument, getChatHistory, askQuestion, getSummary, Document, ChatMessage } from "@/lib/api";

export default function DocumentChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const docId = Number(id);
  const [doc, setDoc] = useState<Document | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getDocument(docId).then(setDoc);
    getChatHistory(docId).then(setMessages);
  }, [docId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || asking) return;
    setQuestion("");
    setMessages(m => [...m, { role: "user", content: q, cited_chunks: null }]);
    setAsking(true);
    try {
      const res = await askQuestion(docId, q);
      setMessages(m => [...m, { role: "assistant", content: res.answer, cited_chunks: res.cited_chunks }]);
    } catch (err: any) {
      setMessages(m => [...m, { role: "assistant", content: `Error: ${err.message}`, cited_chunks: null }]);
    } finally {
      setAsking(false);
    }
  }

  async function loadSummary() {
    setSummaryLoading(true);
    try { setSummary((await getSummary(docId)).summary); }
    finally { setSummaryLoading(false); }
  }

  const suggestions = ["What is this document about?", "Summarize the key points", "What are the main conclusions?"];

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <Link href="/dashboard" className="text-gray-400 hover:text-gray-700 flex-shrink-0"><i className="ti ti-arrow-left" /></Link>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{doc?.title || "Loading…"}</p>
            {doc && <p className="text-xs text-gray-400">{doc.page_count} pages · {doc.chunk_count} chunks</p>}
          </div>
        </div>
        <button onClick={loadSummary} disabled={summaryLoading} className="text-xs text-gray-500 hover:text-gray-800 flex-shrink-0">
          {summaryLoading ? "Summarizing…" : "Summarize"}
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {summary && (
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4">
              <p className="text-xs font-medium text-blue-600 mb-1.5 uppercase tracking-wide">Summary</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{summary}</p>
            </div>
          )}

          {messages.length === 0 && !summary && (
            <div className="text-center py-10">
              <p className="text-sm text-gray-400 mb-4">Ask anything about this document.</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {suggestions.map(s => (
                  <button key={s} onClick={() => setQuestion(s)} className="text-xs text-gray-600 border border-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-100">{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${m.role === "user" ? "bg-gray-900 text-white" : "bg-white border border-gray-200 text-gray-800"}`}>
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{m.content}</p>
                {m.cited_chunks && m.cited_chunks.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2.5 pt-2.5 border-t border-gray-100">
                    {m.cited_chunks.map((c, j) => (
                      <span key={j} className="text-xs bg-gray-100 text-gray-600 rounded-md px-2 py-0.5">
                        <i className="ti ti-file-text text-[10px]" /> p.{c.page_number}{c.section_heading ? ` · ${c.section_heading}` : ""}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {asking && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2.5">
                <p className="text-sm text-gray-400">Thinking…</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <form onSubmit={handleAsk} className="max-w-2xl mx-auto flex gap-2">
          <input
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Ask a question about this document…"
            className="flex-1 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
          />
          <button type="submit" disabled={asking || !question.trim()} className="bg-gray-900 text-white rounded-xl px-5 text-sm font-medium hover:bg-gray-700 disabled:opacity-40">Ask</button>
        </form>
      </div>
    </main>
  );
}
