# TRAIT AI Customer Support Agent

A modular, RAG-based AI customer support application for TRAIT Innovation. Customers
chat with an agent grounded in your uploaded knowledge base (PDF/TXT/DOCX); the agent
refuses to guess when it lacks sufficient information and offers escalation to a
human instead.

> **Development status — please read before demoing or deploying:**
> This code has been written carefully and syntax-checked (`python -m py_compile`
> passes on every file), and every cross-module function call was manually verified
> against its definition. **It has not been executed end-to-end**, because this
> environment has no network access to install dependencies (FastAPI, ChromaDB,
> OpenAI SDK, Streamlit, etc. could not be `pip install`-ed here). Before you rely
> on this, run it yourself locally per the instructions below and work through the
> "Known Limitations / Needs Testing" section.

---

## 1. Architecture Summary

```
Streamlit Frontend  →  FastAPI Backend  →  Agent Orchestrator  →  RAG (Chroma + OpenAI embeddings)
                                        ↘                      ↘
                                     SQLite (history,      LLM (OpenAI-compatible
                                     documents,             chat completion)
                                     escalations)
```

- **Frontend** (`frontend/`): Streamlit app with a customer chat page and an admin panel.
- **Backend** (`backend/`): FastAPI app exposing `/chat`, `/admin/*`, `/health`.
- **Agent** (`agents/support_agent.py`): explicit retrieve → confidence-check →
  generate → escalate logic.
- **RAG** (`rag/`): document loading, chunking, embeddings, ChromaDB vector store, retriever.
- **Services** (`services/`): LLM wrapper, document ingestion pipeline, conversation logging.
- **Database** (`database/`): SQLite access layer (documents, conversations, escalations).
- **Models** (`models/schemas.py`): Pydantic request/response contracts.
- **Utils** (`utils/`): validation, security (admin auth), logging.
- **Config** (`config/settings.py`): all environment-driven settings.

See the full architecture/data-flow/security writeup that preceded this code for
the detailed reasoning.

---

## 2. Folder Structure

```
trait-support-agent/
├── backend/
│   ├── main.py
│   └── routers/{chat.py, admin.py, health.py}
├── frontend/
│   ├── app.py
│   ├── api_client.py
│   └── pages/{1_Customer_Chat.py, 2_Admin_Panel.py}
├── database/
│   ├── db.py
│   └── schema.sql
├── services/
│   ├── llm_service.py
│   ├── document_service.py
│   └── conversation_service.py
├── rag/
│   ├── document_loader.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── retriever.py
├── agents/
│   └── support_agent.py
├── models/
│   └── schemas.py
├── utils/
│   ├── validators.py
│   ├── security.py
│   └── logger.py
├── config/
│   └── settings.py
├── tests/
│   ├── conftest.py
│   ├── test_chunking.py
│   ├── test_validators.py
│   ├── test_confidence.py
│   └── test_api.py
├── data/                # created at runtime (gitignored): chroma/ + support.db
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 3. Installation

Requires Python 3.11+ (developed against 3.12).

```bash
cd trait-support-agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```
OPENAI_API_KEY=sk-...your real key...
ADMIN_API_KEY=pick-a-strong-random-string
```

All other variables have sensible defaults (see `.env.example` for the full list
and explanations: `CONFIDENCE_THRESHOLD`, `TOP_K_RESULTS`, `CHUNK_SIZE`,
`CHUNK_OVERLAP`, `MAX_UPLOAD_MB`, `CHROMA_PERSIST_DIR`, `SQLITE_DB_PATH`, etc.)

**If you use a non-OpenAI OpenAI-compatible provider** (Azure OpenAI, a local
vLLM/Ollama gateway, etc.), set `OPENAI_BASE_URL` accordingly and adjust
`LLM_MODEL`/`EMBEDDING_MODEL` to that provider's model names.

## 5. Running the Backend

From the project root (with venv activated and `.env` configured):

```bash
uvicorn backend.main:app --reload --port 8000
```

- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 6. Running the Frontend

In a second terminal (same venv):

```bash
cd frontend
streamlit run app.py
```

This opens the app in your browser (default http://localhost:8501) with a
sidebar linking to **Customer Chat** and **Admin Panel**. The frontend calls
the backend at `BACKEND_URL` (default `http://localhost:8000`) — set this env
var if your backend runs elsewhere.

**Order matters:** start the backend first, then the frontend.

## 7. Testing the Application

```bash
pytest tests/ -v
```

What's covered without needing a live OpenAI key:
- Text chunking behavior (`test_chunking.py`)
- File/input validators, filename sanitization, injection-pattern flagging (`test_validators.py`)
- Confidence-gating decision logic, with the vector store mocked (`test_confidence.py`)
- API wiring: health check, admin auth rejection/acceptance, chat input validation (`test_api.py`)

**Not covered by automated tests here** (requires a real `OPENAI_API_KEY` and
network access): actual embedding generation, actual LLM answer generation,
and a full upload → index → ask → get-grounded-answer manual walkthrough.
**You must run this manual walkthrough yourself** before considering this
production-ready — see the next section.

### Manual end-to-end test checklist (do this yourself)

1. Start backend + frontend as above with a real `OPENAI_API_KEY`.
2. In Admin Panel, enter your `ADMIN_API_KEY`, upload a short `.txt` file with
   a couple of made-up "company policies" (e.g., a return policy, a support-hours
   line).
3. Confirm it shows status `indexed` with a nonzero chunk count.
4. In Customer Chat, ask a question directly answerable from that file. Confirm
   the answer is grounded and cites the source in "Sources used."
5. Ask an unrelated question (e.g., "What's the capital of France?"). Confirm
   you get the fallback message and an escalation option — not a fabricated
   company-specific answer.
6. Click "Talk to a human agent," then confirm the escalation appears in the
   Admin Panel's Escalations tab.
7. Try uploading a `.exe` or an oversized file — confirm it's rejected with a
   clear error, not a crash.

---

## 8. Example Customer Questions

Once a knowledge base is loaded, try things like:
- "What is your return policy?"
- "How do I reset my password?"
- "What are your support hours?"
- "Do you offer refunds for annual subscriptions?"
- "What's the weather today?" *(should trigger the fallback + escalation — this is intentionally outside any company knowledge base)*

---

## 9. Known Limitations

- **Not executed end-to-end** in this environment (see status note at top) —
  treat as a strong first draft requiring your own verification pass.
- **Admin auth is a single shared API key**, not real authentication/authorization.
  Fine for an internal demo; not acceptable for production — needs real
  identity/session management and RBAC.
- **Confidence score is a heuristic** derived from vector distance, not a
  calibrated probability. It's a reasonable proxy but should be tuned against
  real traffic (`CONFIDENCE_THRESHOLD`).
- **Prompt-injection defense is layered but not absolute**: retrieved content
  is isolated from instructions via prompt structure and a keyword-based
  admin-facing warning flag, but a sufficiently adversarial document could
  still attempt manipulation. Don't treat uploaded documents as fully trusted
  even from internal sources.
- **No OCR** for scanned/image-only PDFs — text extraction will fail cleanly
  with a clear error, but won't extract text from images.
- **No streaming responses** — the chat call is synchronous request/response.
- **No rate limiting** on the API — add this before public exposure.
- **SQLite** is fine for a prototype/small deployment; will need Postgres for
  concurrent production load.
- **CORS is wide open (`*`)** for local dev convenience — restrict before deployment.

## 10. Recommended Next Improvements

1. **Real authentication**: replace the shared admin key with proper user
   accounts/JWT and role-based access control, as a first step toward the
   broader TRAIT AI Agent Platform's multi-tenant needs.
2. **Streaming answers** via Server-Sent Events or WebSockets for a snappier chat UX.
3. **Feedback loop**: let customers thumbs-up/down answers; use this to tune
   `CONFIDENCE_THRESHOLD` and flag knowledge-base gaps.
4. **Source citations inline** in the answer text (not just a separate "Sources" panel).
5. **Multi-turn context**: currently each question is retrieved independently;
   incorporating recent conversation history into the retrieval query would
   improve follow-up question handling.
6. **Swap SQLite → Postgres** and containerize (Docker Compose for backend +
   frontend + Postgres) for a real deployment target.
7. **Agent platform hooks**: formalize `agents/support_agent.py` behind a
   common "Agent" interface (input → tools → output) so it can be registered
   as one agent among several in the TRAIT AI Agent Platform.
8. **Structured document metadata**: let admins tag documents by category/product
   line, and filter retrieval by tag for multi-product support scenarios.
9. **Automated re-indexing**: detect when a document is re-uploaded/updated and
   replace rather than duplicate its chunks.
10. **Load/observability**: add request logging, latency metrics, and basic
    dashboards (this is also where LangSmith or similar tracing would help
    since LangChain is already in the chunking path).

---

## Security Notes (recap)

- API keys are read only from environment variables server-side; never exposed
  to the frontend or logged.
- File uploads are validated by extension, size, and filename-sanitized against
  path traversal.
- Retrieved document content is structurally separated from the system prompt's
  instructions, and the LLM is explicitly told to treat it as data, not commands.
- User chat input is length-checked and stripped before use.
- Admin routes require a header-based key check (see limitations above regarding
  production-readiness of this approach).
