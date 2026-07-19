# Document Intelligence — RAG-Powered Q&A over your PDFs

Upload any PDF, then ask questions in plain English and get answers grounded in the document, with citations to the exact page. Built with a production RAG (Retrieval-Augmented Generation) pipeline.





## What it does

- Upload PDFs — text is extracted, chunked, embedded, and indexed automatically
- Ask questions about a document — answers are generated only from the document's content, with page-level citations
- Cross-document search — semantic + keyword hybrid search across your whole library
- Live processing status — watch a document move through extract → chunk → embed → ready
- One-click AI summaries

## Architecture

```
Upload PDF
  → extract text per page (PyMuPDF)
  → chunk with overlap + page/section metadata
  → embed each chunk (Voyage AI)
  → store vectors in PostgreSQL (pgvector, HNSW index)

Ask a question
  → embed the question
  → hybrid search: vector similarity + full-text keyword, merged with Reciprocal Rank Fusion
  → send top chunks + question to Claude
  → return grounded answer + cited chunks
```

## Tech stack

- **Backend:** FastAPI (async), SQLAlchemy, PostgreSQL + pgvector
- **RAG:** Voyage AI embeddings, Claude (claude-sonnet-4-6) for generation, custom hybrid retrieval
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind
- **Auth:** JWT with HttpOnly cookies, refresh-token rotation
- **Hosting:** Vercel (frontend), Railway (backend), Supabase (PostgreSQL + pgvector)

## Technical decisions worth calling out

**Why hybrid search instead of pure vector similarity?**
Pure semantic search misses exact keyword matches — searching "PTO policy" can miss a document literally titled "PTO Policy 2026" because the vectors aren't similar enough. I run vector search and PostgreSQL full-text search in parallel and merge the ranked lists with Reciprocal Rank Fusion. This measurably improves retrieval accuracy, which matters because RAG quality is dominated by retrieval, not generation.

**Why store citation metadata on every chunk?**
Each chunk carries its page number and section heading. This lets every answer point back to its source ("page 4"), which both builds user trust and makes the system auditable — if an answer doesn't match its cited chunks, that's a retrieval bug, not a model bug.

**Why pgvector (on Supabase) instead of a dedicated vector database?**
Postgres + pgvector handles tens of millions of vectors and keeps everything in one database — no second service to host, pay for, or keep in sync. Running it on Supabase means pgvector is enabled with one toggle and the same managed database serves both local dev and production. HNSW indexing keeps queries fast.

**Why denormalize user_id onto chunks?**
Multi-tenant isolation happens in the SQL WHERE clause of the vector query. Putting user_id directly on the chunk row avoids a join on the hot retrieval path.

**Why is embedding behind an interface?**
The embedding provider is isolated in one service file. Swapping Voyage for OpenAI or a local model is a one-file change — the rest of the pipeline doesn't know or care which provider produced the vectors.

## What I'd improve next

- Add a reranking step (cross-encoder) after retrieval for another accuracy bump
- Streaming answers token-by-token instead of waiting for the full response
- Support Word docs and plain text, not just PDF
- Track citation-match rate as a retrieval quality metric

## Running locally

See `docs/CLAUDE_CODE_PROMPT.md` for full setup instructions.
