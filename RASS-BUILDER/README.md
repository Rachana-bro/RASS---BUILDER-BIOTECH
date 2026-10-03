# RASS-BUILDER
Advance Pattern Detection in Complex DNA Sequencing Reads Data Records Framework System

## Architecture Overview
- `frontend/`: React + TypeScript + Vite UI workstation
- `backend/`: FastAPI Python bioinformatics & deep learning microservice
- `data/demo/`: Sample sequencing reads and demo FASTQ datasets
- `models/`: PyTorch neural transformer and pattern detection modules
- `tests/`: End-to-end integration and unit test suite (90 tests across Stages 1–9)


---

## Genomic Analysis Pipeline

```
FASTQ / FASTA Raw Reads
          ↓
Stage 1: Data Ingestion (4-line FASTQ parsing & Phred quality extraction)
          ↓
Stage 2: Quality Control & Filtering (Mean Q, Q20, Q30, N-fraction, cycle profiles)
          ↓
Stage 3: Sequence Normalization (Whitespace, uppercase, reverse complement)
          ↓
Stage 4: DNA Tokenization & Model Interface Contract
          ↓
STAGE 5: DNA TRANSFORMER / AI ANALYSIS LAYER
          ↓
- DNA Tokenizer (<PAD>, <UNK>, <START>, <END>, A, C, G, T, N)
- Token IDs Generation & Bidirectional Mapping
- PyTorch Multi-Head Self-Attention Transformer
- Sequence Embeddings (d_model = 64 float32 vector)
- Model Attention / Computational Representation Extraction
- Modular Pattern Detection Head
- Confidence & Clinical Verification Safeguards
- Structured Analysis Result Object
```

---

## STAGE 5 — DNA TRANSFORMER / AI ANALYSIS LAYER

Stage 5 introduces a genuine, modular PyTorch Transformer foundation for DNA sequence analysis. It is explicitly engineered as an authentic deep learning infrastructure layer ready for fine-tuning on validated genomic cohorts, while strictly adhering to scientific integrity guidelines (no simulated clinical claims or fabricated confidence scores).

### 1. Model Architecture
- **Framework:** PyTorch (with deterministic mathematical NumPy fallback for non-GPU/minimal environments).
- **Token Embedding:** `nn.Embedding(vocab_size=9, d_model=64, padding_idx=0)`.
- **Positional Encoding:** Sinusoidal positional encoding (`sin` / `cos` geometric frequency bands up to 2000 bp).
- **Encoder Layers:** 2 Transformer Encoder blocks with Pre-LayerNorm (`nn.LayerNorm(64)`), 4-head Multi-Head Self-Attention (`DNAMultiHeadAttention`), GELU-activated feedforward sublayers (`dim_feedforward=128`), and residual skip connections.
- **Sequence Pooling:** Masked mean-pooling across valid non-pad tokens to derive sequence-level latent vector representation.
- **Pattern Analysis Head:** Modular MLP (`d_model -> hidden_dim(32) -> GELU -> LayerNorm -> num_patterns(4)`) decoupled from the core encoder for downstream fine-tuning.

### 2. DNA Tokenizer
Located in `bioinformatics/tokenizer.py` (`DNATokenizer` class):
- **Normalization:** Strips whitespace, converts lowercase to uppercase, and validates base composition.
- **Vocabulary (Size = 9):**
  - `<PAD>`: ID 0 (padding for batched inputs)
  - `<UNK>`: ID 1 (unknown/unrecognized characters)
  - `<START>`: ID 2 (sequence commencement delimiter)
  - `<END>`: ID 3 (sequence termination delimiter)
  - `A`: ID 4, `C`: ID 5, `G`: ID 6, `T`: ID 7, `N`: ID 8
- **Invalid Base Detection:** Scans sequences for characters outside `{A, C, G, T, N}` and maps them safely to `<UNK>` without crashing or inventing biological assumptions.
- **Bidirectional Mapping:** Full serialization via `encode()` and `decode()`.

### 3. Sequence Embeddings
- The Transformer produces a numerical embedding vector representing the input sequence in a continuous 64-dimensional latent space (`float32`).
- Returns metadata including `dimension` (64), `norm` (L2 vector magnitude), `vector_sample` (first 8 floats for preview), and total sequence/token length.

### 4. Attention / Computational Representation
- The multi-head self-attention mechanism computes query-key affinity matrices across all heads.
- **Labeling Standard:** All attention telemetry in the API and UI is strictly labeled as **"Model Attention / Computational Representation"**.
- **Scientific Disclaimer:** *"Attention values reflect internal Transformer layer weight distribution, not validated biological importance."*

### 5. Modular Pattern Detection Interface
Structure:
```json
{
  "pattern_detected": false,
  "patterns": [],
  "confidence": null,
  "model_status": "untrained"
}
```
If an untrained model or missing checkpoint is detected, the pipeline sets `pattern_detected = false`, `patterns = []`, and `model_status = "untrained"`.

### 6. Confidence & Scientific Safeguards
- **Zero Fabrication Policy:** Confidence is never synthesized, hallucinated, or randomly generated.
- When no certified checkpoint is loaded:
  - `confidence = null`
  - Display message: `"Confidence unavailable — validated model required."`
  - `clinical_interpretation = false`
  - Regulatory notice: *"Clinical claims prohibited without certified training and regulatory validation."*
- Prohibits displaying `"PATHOGENIC"`, `"DISEASE DETECTED"`, or clinical decisions without accredited model weights.

### 7. Model Checkpoint Requirements & Loading Interface
The clean model interface exposes:
- `load_model(checkpoint_path: Optional[str]) -> bool`
- `analyze_sequence(sequence: str, read_id: str) -> dict`
- `get_embeddings(tokens: list[int]) -> dict`
- `detect_patterns(embeddings, sequence, tokens) -> dict`

If no checkpoint is found:
- Reports: `"Model checkpoint not available — analysis model requires training/validation."`
- Does **NOT** silently substitute random uncalibrated weights as real predictions.

### 8. How a Validated Model Can Be Connected Later
1. Train the `PyTorchDNATransformer` on annotated genomic datasets (e.g. ClinVar, gnomAD, or target panel BAMs).
2. Save the validated PyTorch weights:
   ```python
   torch.save(model.state_dict(), "backend/models/checkpoints/stage5_transformer.pt")
   ```
3. Pass calibration thresholds in `Stage5DNAEngine.load_model()`. The pipeline will automatically detect the checkpoint, set `checkpoint_loaded = True`, and route calibrated confidence scores to the structured output.

### 9. Current Limitations
- Current model weights are uninitialized foundation weights awaiting clinical cohort training.
- Sequence embeddings represent mathematical Transformer representations and must not be used for diagnostic decisions.
- Maximum supported sequence window per API call is 10,000 bp.

---

## API Endpoints

### Stage 5 DNA Analysis
- **`POST /api/analyze/dna`** (also mirrored at `/api/v1/analysis/dna`)
- **Request Body:**
  ```json
  {
    "sequence": "ACGTACGTACGTACGTACGT",
    "read_id": "READ_001"
  }
  ```
- **Response Body:**
  ```json
  {
    "stage": 5,
    "status": "completed",
    "sequence_length": 20,
    "token_count": 22,
    "read_id": "READ_001",
    "model": {
      "name": "RASS-DNA-Transformer",
      "version": "0.5.0-foundation",
      "checkpoint_loaded": false,
      "checkpoint_status": "Model checkpoint not available — analysis model requires training/validation.",
      "framework": "PyTorch v2.14.1+cpu",
      "device": "cpu"
    },
    "embedding": {
      "dimension": 64,
      "generated": true,
      "norm": 1.0234,
      "vector_sample": [-0.041, 0.118, 0.005, -0.089, 0.032, -0.154, 0.088, -0.012]
    },
    "attention": {
      "available": true,
      "type": "Model Attention / Computational Representation",
      "note": "Attention values reflect internal Transformer layer weight distribution, not validated biological importance.",
      "token_labels": ["<START>", "A", "C", "G", "T", "..."],
      "token_weights": [0.045, 0.052, "..."]
    },
    "pattern_analysis": {
      "status": "pending_validation",
      "patterns": [],
      "pattern_detected": false,
      "model_status": "untrained"
    },
    "confidence": null,
    "confidence_display": "Confidence unavailable — validated model required.",
    "clinical_interpretation": false,
    "clinical_disclaimer": "Stage 5 technical foundation ready for validated model checkpoint. Clinical claims prohibited without certified training and regulatory validation."
  }
  ```

---

## STAGE 6 — VARIANT & PATTERN RESULTS UI

Stage 6 implements the complete clinical results dashboard consuming the structured output from the Stage 5 DNA Transformer without fabricating clinical results or unvalidated mutations.

### 1. Stage 5 → Stage 6 Data Flow
```
FASTQ / FASTA Raw Reads
          ↓
Stage 4 Processing (Normalization & Tokenization)
          ↓
Stage 5 DNA Transformer (Embeddings & Attention)
          ↓
Structured Analysis Result (Stage5AnalysisResult)
          ↓
STAGE 6: RESULTS DASHBOARD (PipelineStage6.tsx)
    ├── A. Analysis Status (Completed / Validation Required)
    ├── B. Sequence Summary (Length, Tokens, Format, Read ID)
    ├── C. Model Information (Name, Version, Checkpoint Status, Embedding Dim)
    ├── D. Detected Genomic Patterns Table (NO VALIDATED PATTERN AVAILABLE)
    ├── E. Genomic Variant Call Records (No validated variants available)
    ├── F. Confidence Display (Not Available / Reason: Validated model confidence unavailable)
    ├── G. Interpretation (Separated Computational Analysis vs Clinical Disclaimer)
    ├── H. Sequence Coordinate Map (5' -> 3' Linear Representation)
    ├── I. Technical Analysis Details (Collapsible telemetry, tokens, vector samples)
    └── J. Export Preparation (JSON Export, Draft Report Download, Print PDF hooks)
```

### 2. Results Dashboard Structure
- **Analysis Status Card:** Shows actual pipeline state (`✓ Pipeline Completed` or `⚠ Validation Required`), Stage 6/10 progress, and non-diagnostic verification level.
- **Sequence Summary Card:** Displays sequence length (bp), token count, input format, read identifier, and canonical base ratio without inventing data.
- **Model Information Card:** Displays model name (`RASS-DNA-Transformer`), version (`0.5.0-foundation`), checkpoint status (`Trained model checkpoint unavailable.`), and embedding dimensions (`64 float32`).
- **Pattern Visualization (5' → 3'):** Clean linear nucleotide coordinate map with orientation markers and interactive base hover inspection, without arbitrary synthetic mutation markers.

### 3. Pattern & Variant Tables
- **Detected Patterns Table:** If no validated checkpoint exists, displays `NO VALIDATED PATTERN AVAILABLE` (Reason: *A trained and validated model checkpoint is required*). RASS-BUILDER strictly avoids fabricating mutations.
- **Variant Results Table:** Displays `No validated variants available. Model output is currently limited to computational sequence representation.` Ready to accept real variant calls when certified callsets are supplied.

### 4. Confidence & Model-Status Handling
- If `confidence = null`, displays `CONFIDENCE: Not Available` (Reason: *Validated model confidence unavailable*).
- Zero synthetic confidence policy: Prohibits displaying fake 98% or 99.8% scores.

### 5. Interpretation Separation & Disclaimers
- **Computational Analysis:** Displays latent vector L2 norm, multi-head self-attention layer representation, and token count.
- **Clinical Interpretation:** Strictly displays `"Clinical interpretation is not provided by this prototype."` Computational outputs must not be used for medical decisions without certified pathologist oversight and regulatory clearance.

### 6. Export Preparation
- UI hooks for `Export Analysis (JSON)`, `Download Report (Draft)`, and `Print Report (PDF)`. Ready for full persistence and export wiring in Stage 10.

---

## Running Tests

From `RASS-BUILDER/`:
```bash
backend\.venv\Scripts\pytest.exe -v
```
All 41 tests covering Stages 1 through 6 run and pass out-of-the-box:
- 11 Stage 4 pipeline & API tests
- 20 Stage 5 Transformer, tokenizer, and embedding tests
- 10 Stage 6 results contract, schema compatibility, and safeguard tests

Frontend verification:
```bash
cd frontend && npm run build
```
Builds cleanly with zero TypeScript or Vite errors (`tsc -b && vite build`).

---

## Stage 7: Asynchronous Job Processing & Queue Infrastructure

Stage 7 transforms the RASS-BUILDER computational pipeline from a synchronous request-response flow into a non-blocking, asynchronous background execution architecture.

### Architectural Flow

```
USER SUBMITS ANALYSIS
        ↓
CREATE JOB (`POST /api/jobs`)
        ↓
QUEUE JOB (FIFO in-memory queue)
        ↓
BACKGROUND WORKER
        ↓
STAGE 4 (Ingestion & Quality Control)
        ↓
STAGE 5 (DNA Tokenizer & PyTorch Transformer)
        ↓
STAGE 6 (Structured Output)
        ↓
UPDATE JOB STATUS (`COMPLETED` / `FAILED`)
        ↓
FRONTEND STATUS POLLING (`GET /api/jobs/{job_id}`)
        ↓
VIEW RESULTS IN STAGE 6 DASHBOARD
```

### Job Model & Lifecycle

Every asynchronous analysis job is assigned a unique identifier (`JOB-XXXXXXXX`) and tracked through deterministic, measurable stage transitions:

| Stage / Status | Progress | Description |
|---|---|---|
| `QUEUED` | 10% | Job validated, initial state stored, dispatched to worker queue. |
| `DATA_INGESTION` | 20% | Worker picks up job, verifies sequence format and input parameters. |
| `QUALITY_CONTROL` | 40% | Stage 4 sequence normalization and read quality score filtering. |
| `TRANSFORMER_ANALYSIS` | 60% | DNA Tokenization and PyTorch Transformer forward pass (embedding extraction). |
| `PATTERN_ANALYSIS` | 80% | Multi-head self-attention mapping and pattern validation checkpoint evaluation. |
| `COMPLETED` | 100% | Pipeline finished; structured Stage 5/6 result object stored for dashboard display. |
| `FAILED` | Variable | Execution terminated due to input error; sanitized user-safe error message recorded. |
| `CANCELLED` | Terminal | Job safely cancelled by user before or during pipeline execution. |

### API Endpoints Added

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/jobs` (and `/api/v1/jobs`) | Enqueue analysis job. Returns immediately with `status: "QUEUED"`. |
| `GET` | `/api/jobs/{job_id}` (and `/api/v1/jobs/{job_id}`) | Poll job status, stage progress, and live descriptive messages. |
| `GET` | `/api/jobs/{job_id}/result` (and `/api/v1/jobs/{job_id}/result`) | Retrieve completed Stage 5/6 structured analysis payload (HTTP 409 if active). |
| `POST` | `/api/jobs/{job_id}/cancel` (and `/api/v1/jobs/{job_id}/cancel`) | Safely cancels a queued or running job. |
| `GET` | `/api/jobs` (and `/api/v1/jobs`) | List recent jobs for the Job History view (sanitized, limit query param). |

### Background Worker & Persistence Strategy

- **Worker Thread:** `BackgroundJobWorker` operates as an independent concurrent processor using `queue.Queue` with daemon thread management, keeping the HTTP event loop responsive.
- **Repository Abstraction:** Implements `JobRepository` abstract interface with `InMemoryJobRepository` (protected with `threading.RLock`). This architectural boundary enables drop-in migration to relational databases (SQLite / PostgreSQL) in Stage 8 without refactoring APIs or workers.
- **Duplicate Job Protection:** Submissions with identical sequences or idempotency keys return existing active jobs to prevent accidental double-clicks.
- **Security & Zero-Leakage:** Public status endpoints and history lists strictly exclude raw sequences, filesystem paths, and internal stack traces.

### Limitations & Future Enhancements

- **Polling:** Frontend uses lightweight, reliable polling at 1.5-second intervals with automatic termination on completion or failure. WebSockets or Server-Sent Events (SSE) can be introduced in a future stage for push-based notifications.
- **Worker Scale:** Operates as a single-node in-memory queue. Production scaling to distributed queues (Celery/Redis) will follow in later deployment stages.

---

## Stage 8: Database & Persistent Storage

Stage 8 integrates relational SQLite persistence into the RASS-BUILDER architecture. Job states, execution lifecycles, and structured Stage 5/6 analysis results are now preserved permanently across frontend page refreshes and backend server restarts.

### Architectural Flow

```
                 RASS-BUILDER
                      │
                FASTQ / FASTA
                      ↓
              STAGE 4 — PIPELINE
                      ↓
             STAGE 5 — AI LAYER
                      ↓
          Tokenization + Transformer
                      ↓
              Embeddings / Attention
                      ↓
             Pattern Analysis
                      ↓
          ┌─────────────────────┐
          │ STAGE 6             │
          │ RESULTS DASHBOARD   │
          └─────────────────────┘
                      ↓
          ┌─────────────────────┐
          │ STAGE 7             │
          │ ASYNC JOB QUEUE     │
          └─────────────────────┘
                      ↓
          ┌─────────────────────┐
          │ STAGE 8             │
          │ PERSISTENT DATABASE │
          └─────────────────────┘
             │       │       │
           Jobs   Results  Recovery
```

### Relational Schema Design

The SQLite database (`backend/data/rass_builder.db`) enforces relational integrity, Write-Ahead Logging (WAL) concurrency, and foreign-key cascading:

#### 1. `jobs` Table
Tracks job lifecycles across reboots:

| Column | Type | Description |
|---|---|---|
| `job_id` | `TEXT PRIMARY KEY` | Unique identifier (`JOB-XXXXXXXX`). |
| `status` | `TEXT NOT NULL` | `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `RECOVERY_REQUIRED`. |
| `current_stage` | `TEXT NOT NULL` | Active pipeline stage. |
| `progress` | `INTEGER NOT NULL` | Stage percentage (10% to 100%). |
| `created_at` | `TEXT NOT NULL` | ISO 8601 UTC timestamp. |
| `started_at` | `TEXT` | Execution start timestamp. |
| `completed_at` | `TEXT` | Execution finish timestamp. |
| `message` | `TEXT NOT NULL` | Descriptive status message. |
| `input_metadata` | `TEXT NOT NULL` | Sanitized JSON (read ID, sequence length, format). |
| `raw_sequence` | `TEXT` | Internal execution payload (never exposed in public APIs). |
| `file_path` | `TEXT` | Internal FASTQ path (never exposed in public APIs). |
| `error` | `TEXT` | Sanitized error message if failed. |
| `idempotency_key` | `TEXT` | Hash fingerprint for duplicate prevention. |
| `cancelled` | `INTEGER NOT NULL` | Boolean flag (0 or 1). |

#### 2. `analysis_results` Table
Stores structured computational results emitted by Stage 5/6:

| Column | Type | Description |
|---|---|---|
| `result_id` | `TEXT PRIMARY KEY` | Unique result identifier (`RES-XXXXXXXX`). |
| `job_id` | `TEXT NOT NULL UNIQUE` | Foreign key referencing `jobs(job_id) ON DELETE CASCADE`. |
| `sequence_metadata` | `TEXT NOT NULL` | JSON: sequence length, token count, read ID. |
| `model_metadata` | `TEXT NOT NULL` | JSON: model name, version, checkpoint status. |
| `embedding_metadata`| `TEXT NOT NULL` | JSON: tensor dimensions, norm, status. |
| `pattern_results` | `TEXT NOT NULL` | JSON: validated patterns array (zero fabrication). |
| `variant_results` | `TEXT NOT NULL` | JSON: variant calls array. |
| `confidence` | `REAL` | Calibration confidence (strictly `NULL` for untrained foundation). |
| `analysis_status` | `TEXT NOT NULL` | Pipeline status (`completed`). |
| `created_at` | `TEXT NOT NULL` | Result creation timestamp. |
| `raw_result` | `TEXT NOT NULL` | Complete Stage 5/6 structured JSON payload. |

#### 3. `schema_versions` Table
Maintains versioned migration tracking (`version: 1`).

### Worker Recovery Strategy (Requirement 13)

When the backend server boots up (via FastAPI `lifespan` handler):
1. Runs `init_db()` to ensure tables, indexes, and versioning exist without modifying existing data.
2. Queries the `jobs` table for any jobs stranded in `status = 'RUNNING'` when the server lost power or restarted.
3. Rather than silently assuming completion, transitions stranded jobs to:
   - `status = 'RECOVERY_REQUIRED'`
   - `current_stage = 'RECOVERY_REQUIRED'`
   - `message = 'Analysis process was interrupted by server restart. Manual recovery required.'`
   - `error = 'Execution interrupted by host process restart.'`
This preserves complete laboratory audit integrity and prevents corrupted/half-executed results.

### API Endpoints

- `GET /api/jobs`: Retrieves persistent job history from SQLite (sanitized, limit query param).
- `GET /api/jobs/{job_id}`: Retrieves persistent job metadata and progress.
- `GET /api/jobs/{job_id}/result`: Retrieves the structured Stage 6 result directly from `analysis_results`.
- `POST /api/jobs`: Atomically inserts job into `jobs` table and dispatches to queue.
- `POST /api/jobs/{job_id}/cancel`: Updates job status to `CANCELLED` in database.

### Production Migration Path

The database layer follows the Clean Architecture Repository Pattern:
- `JobRepository` (abstract base class in `backend/jobs/repository.py`)
- `SqliteJobRepository` (implementation in `backend/database/repository.py`)
To migrate to PostgreSQL or another production relational database in future stages, implement `PostgresJobRepository` implementing the exact same `JobRepository` interface without modifying API routes, workers, or business logic.

---

## STAGE 9 — AUTHENTICATION & ACCESS CONTROL

Stage 9 introduces enterprise-grade user authentication, session security, and role-based access control (RBAC) to the RASS-BUILDER workstation, ensuring complete data isolation and Insecure Direct Object Reference (IDOR) prevention while preserving 100% of Stages 1–8 functionality.

### End-to-End Target Flow

```
User
  ↓
Stage 9: Authentication (Registration / Login / Bearer Token)
  ↓
Authorized Workstation Session
  ↓
FASTQ / FASTA Upload
  ↓
Stage 4 Pipeline (Quality Filtering, Normalization, Tokenization)
  ↓
Stage 5 AI Layer (PyTorch DNA Transformer, Embeddings, Attention Map)
  ↓
Stage 6 Results (Variant Detection, Pattern Analysis, Zero-Fabrication Guarantees)
  ↓
Stage 7 Async Jobs (Queue Infrastructure & Background Worker)
  ↓
Stage 8 Persistent Database (SQLite Relational Persistence with WAL)
  ↓
Stage 9 Data Isolation (Ownership Verification & RBAC Boundary Enforcement)
```

### 1. User Authentication & Password Hashing
- **PBKDF2 HMAC SHA-256:** Cryptographically secure password hashing using standard library `hashlib.pbkdf2_hmac` with 100,000 iterations and per-user 16-byte unique cryptographic salts (`secrets.token_hex(16)`).
- **Constant-Time Verification:** Uses `hmac.compare_digest` to prevent timing attacks.
- **Zero Plaintext Storage:** Passwords, hashes, and salts are never leaked to frontend clients, log files, or unauthenticated responses.
- **Password Complexity Rules:** Enforces minimum 8 characters, at least one letter, and at least one numeric digit or special symbol.

### 2. User & Session Database Schema
Integrated seamlessly into the Stage 8 SQLite persistence layer:

#### `users` Table
| Column | Type | Description |
|---|---|---|
| `user_id` | `TEXT PRIMARY KEY` | Structured identifier (`USR-XXXXXXXX`). |
| `name` | `TEXT NOT NULL` | User's full or display name. |
| `email` | `TEXT NOT NULL UNIQUE` | Case-insensitive email or username. |
| `password_hash` | `TEXT NOT NULL` | PBKDF2 HMAC SHA-256 derived key hex. |
| `salt` | `TEXT NOT NULL` | Unique per-user cryptographic salt hex. |
| `role` | `TEXT NOT NULL DEFAULT 'USER'` | `USER` or `ADMIN`. |
| `account_status` | `TEXT NOT NULL DEFAULT 'ACTIVE'` | `ACTIVE` or `SUSPENDED`. |
| `created_at` | `TEXT NOT NULL` | ISO 8601 UTC creation timestamp. |
| `updated_at` | `TEXT NOT NULL` | ISO 8601 UTC last update timestamp. |

#### `sessions` Table
| Column | Type | Description |
|---|---|---|
| `session_id` | `TEXT PRIMARY KEY` | Structured identifier (`SES-XXXXXXXX`). |
| `user_id` | `TEXT NOT NULL` | Foreign key referencing `users(user_id) ON DELETE CASCADE`. |
| `token` | `TEXT NOT NULL UNIQUE` | 256-bit high-entropy URL-safe bearer token. |
| `created_at` | `TEXT NOT NULL` | Session issuance timestamp. |
| `expires_at` | `TEXT NOT NULL` | Session expiry timestamp (24-hour default TTL). |
| `is_active` | `INTEGER NOT NULL DEFAULT 1` | Active flag (revoked on logout). |

#### Relational Relationship
- `jobs.user_id` links jobs directly to `users(user_id)`.
- Pre-existing/legacy jobs without user attribution remain safely intact with `user_id = NULL`.

### 3. Role-Based Access Control (RBAC)
- **`USER` Role:**
  - Can submit DNA sequences and upload FASTQ files.
  - Can monitor progress of their own analysis jobs.
  - Can view and export their own structured analysis results.
  - Strictly restricted from accessing administrative endpoints (returns HTTP 403 Forbidden).
- **`ADMIN` Role:**
  - Can view all analysis jobs across the laboratory workstation.
  - Can monitor queue status, worker thread state, and database health via `GET /api/admin/system/status`.
  - Can list all registered workstation users and their job counts via `GET /api/admin/users`.
  - Can trigger recovery for interrupted jobs via `POST /api/admin/recovery`.

### 4. Data Isolation & IDOR Protection
- **Ownership Verification:** Before retrieving job status (`GET /api/jobs/{id}`), results (`GET /api/jobs/{id}/result`), or cancelling a job (`POST /api/jobs/{id}/cancel`), the backend strictly verifies ownership:
  - If `job.user_id == current_user.user_id` -> Access permitted (HTTP 200).
  - If `current_user.role == "ADMIN"` -> Access permitted (HTTP 200).
  - If `current_user.user_id != job.user_id` -> Access denied (HTTP 403 Forbidden).
  - If request is unauthenticated and job has an owner -> Access denied (HTTP 401 Unauthorized).
- **Sanitized Job History:** Standard users only see their own jobs when listing `GET /api/jobs`. Administrators receive the complete system-wide job history.

### 5. API Endpoints
- `POST /api/auth/register` (and `/api/v1/auth/register`): User registration with validation and initial token issuance.
- `POST /api/auth/login` (and `/api/v1/auth/login`): User login and token generation.
- `POST /api/auth/logout` (and `/api/v1/auth/logout`): Invalidation of current session token.
- `GET /api/auth/me` (and `/api/v1/auth/me`): Authenticated user profile retrieval.
- `GET /api/admin/users`: [Admin only] Workstation users list with job counts.
- `GET /api/admin/system/status`: [Admin only] System status, database health, and queue metrics.
- `POST /api/admin/recovery`: [Admin only] Interrupted job recovery execution.

### 6. Scientific & Regulatory Integrity
Authentication is purely an application security and access control mechanism. It provides no clinical validation, medical diagnosis, or patient certification claims.

---

## STAGE 10 — PRODUCTION HARDENING, SECURITY & OBSERVABILITY

Stage 10 hardens the RASS-BUILDER workstation into an enterprise-ready, observable, and resilient genomic analysis platform. It introduces defense-in-depth HTTP security, request correlation, structured log redaction, sliding-window rate limiting, persistent audit logging, comprehensive health/readiness probes, and guaranteed worker error recovery.

### Architectural Overview

```
Client (Web UI / API Consumer)
  │  (X-Request-ID / Bearer Token)
  ▼
[SecurityHeadersMiddleware]
  ├── Production Headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
  ├── Request Payload Size Guard (rejects requests > 25MB with 413)
  └── Telemetry Latency Tracking
  ▼
[CorrelationIdMiddleware]
  └── ContextVar Request ID propagation (X-Request-ID)
  ▼
[RateLimiter Guard]
  └── In-memory sliding window checks (returns HTTP 429 + Retry-After)
  ▼
[API Routes & Error Handlers]
  ├── Unified Error Payload: { error: { code, message, request_id }, detail }
  ├── Input Sanitization & Path-Traversal Defense
  └── FASTQ / FASTA Structure Validation
  ▼
[Audit Logging Subsystem]
  └── Immutable persistent SQLite audit_logs table (redacted credentials & sequences)
  ▼
[Async Background Worker]
  ├── Correlation propagation into job execution logs
  └── Guaranteed terminal status (COMPLETED / FAILED, never stuck in RUNNING)
```

---

### 1. Security Features

- **Production HTTP Headers:** Every response is augmented with:
  - `X-Content-Type-Options: nosniff` (MIME-sniffing prevention)
  - `X-Frame-Options: DENY` (clickjacking defense)
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (enforces TLS)
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- **Explicit CORS Configuration:** Replaces unrestricted wildcards with strict allowed origins configured through `RASS_CORS_ORIGINS` (defaults to local development hosts `http://localhost:3000`, `http://localhost:5173`).
- **Request Size Limits:** Inspects `Content-Length` headers and stream bytes. Uploads or API bodies exceeding `RASS_MAX_UPLOAD_SIZE_MB` (default: 25 MB) are rejected immediately with HTTP 413 `PAYLOAD_TOO_LARGE`.
- **Path Traversal Defense:** Uploaded filenames are stripped of directory separators using `os.path.basename` and resolved destination paths are asserted to reside strictly inside the `uploads/` root directory.
- **Data Leakage Prevention:** Global exception handlers guarantee that database connection strings, operating system paths (e.g., `C:\...`, `/Users/...`), stack traces, and internal exceptions are NEVER returned to API clients.

---

### 2. Rate Limiting & Abuse Protection

A thread-safe sliding-window rate limiter protects sensitive and compute-intensive endpoints:
- **Authentication Endpoints:** `/api/auth/register`, `/api/auth/login` (100 requests/minute per client IP)
- **Upload Endpoints:** `/api/v1/uploads/fastq`, `/api/v1/uploads/fasta` (25–60 requests/minute per client IP)
- **Job Creation Endpoints:** `/api/jobs`, `/api/v1/jobs` (40–100 requests/minute per client IP)
- **DNA Transformer Analysis:** `/api/analyze/dna` (30–60 requests/minute per client IP)

When limits are exceeded:
- Returns **HTTP 429 Too Many Requests**
- Returns `Retry-After: <seconds>` header
- Returns standardized error JSON payload with code `RATE_LIMIT_EXCEEDED`

Rate limiting can be toggled via `RASS_RATE_LIMIT_ENABLED=1|0`.

---

### 3. Audit Logging

Security-relevant operations are written to an immutable `audit_logs` table in SQLite:
- **Tracked Events:** `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`, `AUTH_FAILURE`, `UNAUTHORIZED_ACCESS`, `FORBIDDEN_ACCESS`, `FILE_UPLOAD`, `FILE_UPLOAD_FAILED`, `JOB_CREATED`, `JOB_COMPLETED`, `JOB_FAILED`, `JOB_CANCELLED`, `CONFIG_VALIDATION`.
- **Audit Record Schema:**
  - `log_id`: Unique identifier (`aud_XXXXXXXXXXXX`)
  - `timestamp`: ISO-8601 UTC timestamp
  - `event_type`: Categorical event code
  - `user_id`: Authenticated user ID (or `NULL` if anonymous)
  - `request_id`: Correlated request identifier
  - `status`: `SUCCESS` or `FAILURE`
  - `ip_address`: Client IP address
  - `details`: JSON dictionary of sanitized contextual metadata
- **Redaction Guarantees:** Passwords, password confirmation fields, bearer tokens, cryptographic salts, API secrets, and biological sequence strings are strictly redacted before database write.
- **Admin Audit Query:** Administrators can query the audit trail via `GET /api/admin/audit-logs`.

---

### 4. Request & Job Correlation

- **`X-Request-ID`:** Every incoming HTTP request receives or inherits a correlation ID (e.g. `req_9896e1ad5b4b`).
- **ContextVar Propagation:** Correlation IDs are tracked via Python's asynchronous `contextvars` and included in:
  - Backend log lines
  - API response headers (`X-Request-ID`)
  - Standardized error response JSON bodies
  - Asynchronous Job metadata (`job.input_metadata["request_id"]`)
  - Worker processing execution logs and audit records
- Enables full end-to-end traceability from HTTP request → async job execution → analysis result.

---

### 5. Structured Logging & Redaction

- Replaces ad-hoc `print` calls with Python's standard `logging` configured with custom `RedactingFormatter`.
- Log output format:
  ```
  2026-10-03 07:51:41 [INFO] [req:req_9896e1ad5b4b] rass_builder: Ingesting sequence data...
  ```
- **Automated Masking:**
  - Passwords and auth tokens: `password: [REDACTED]`
  - Bearer headers: `Bearer [REDACTED_TOKEN]`
  - DNA sequences > 50 bp: `[DNA_SEQUENCE_120BP_MASKED]` to prevent flooding operational logs with genomic sequence dumps.

---

### 6. Consistent Error Handling

Standardized error payloads returned across all endpoints:

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Malformed FASTQ file: missing '@' header.",
    "request_id": "req_84b295ff"
  },
  "detail": "Malformed FASTQ file: missing '@' header."
}
```

- Provides both modern structured `error` object and backward-compatible top-level `detail` string for existing API consumers.
- Explicit codes: `BAD_REQUEST`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `PAYLOAD_TOO_LARGE`, `VALIDATION_ERROR`, `RATE_LIMIT_EXCEEDED`, `INTERNAL_SERVER_ERROR`, `SERVICE_UNAVAILABLE`.

---

### 7. Health & Readiness Endpoints

- **`GET /health` (and `/api/v1/health`):** Lightweight liveness probe confirming the FastAPI process is responsive.
- **`GET /ready` (and `/api/v1/ready`):** Deep readiness check evaluating runtime dependencies:
  1. Relational database connectivity (`SELECT 1;`)
  2. Background asynchronous worker thread status (`is_alive()`)
  3. Storage directory accessibility (`uploads/`)
  - Returns HTTP 200 `{"status": "ready", ...}` when all dependencies are healthy.
  - Returns HTTP 503 `{"status": "not_ready", ...}` if any critical dependency is unavailable.

---

### 8. Async Worker Reliability & Safety

- **Guaranteed Terminal Status:** Wrap-around exception handlers ensure that any unexpected parsing, PyTorch execution, or IO error moves the job to `status = 'FAILED'` with sanitized status messages. Jobs never remain indefinitely stuck in `RUNNING`.
- **Startup Recovery:** Interrupted jobs from host process terminations are detected on application startup and marked `RECOVERY_REQUIRED`.
- **Graceful Shutdown:** Worker thread receives a termination event and drains cleanly during server shutdown.

---

### 9. Operational Observability & Metrics

Administrative endpoint `GET /api/admin/metrics` (restricted to `ADMIN` role) returns real-time system telemetry:
- **HTTP Metrics:** Total requests, failed requests, rate-limit blocks, HTTP status code distribution, rolling average and maximum latency (ms).
- **Job Pipeline Metrics:** Enqueued, completed, failed, and cancelled job counters.
- **System Errors:** Database errors and worker errors.

---

### 10. Environment Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `RASS_ENV` | string | `production` | Environment mode (`production`, `development`, `testing`). |
| `RASS_LOG_LEVEL` | string | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `RASS_DB_PATH` | string | `backend/data/rass_builder.db` | Filesystem path for persistent SQLite database. |
| `RASS_CORS_ORIGINS` | string (CSV) | `http://localhost:3000,http://localhost:5173` | Allowed CORS client origins. |
| `RASS_MAX_UPLOAD_SIZE_MB` | integer | `25` | Maximum allowable upload file and request payload size in MB. |
| `RASS_RATE_LIMIT_ENABLED` | boolean | `1` | Enable (`1`) or disable (`0`) in-memory sliding-window rate limiting. |
| `RASS_REQUIRE_AUTH` | boolean | `0` | Enforce mandatory authentication globally across all endpoints. |

---

### 11. Verification & Test Execution

Run the complete 110-test suite across all Stages 4–10:

```bash
# Run complete test suite
backend/.venv/Scripts/pytest -v

# Run Stage 10 tests only
backend/.venv/Scripts/pytest -v tests/test_stage10_hardening_and_observability.py
```

All 110 tests pass with zero regressions:
- 34 Stage 4/5 Transformer & Bioinformatic tests
- 9 Stage 6 Structured Results tests
- 16 Stage 7 Asynchronous Queue & Worker tests
- 13 Stage 8 Persistent Relational Database tests
- 18 Stage 9 Authentication & Access Control tests
- 20 Stage 10 Production Hardening, Security & Observability tests

---

### 12. Production Deployment Considerations

1. **Reverse Proxy:** Deploy behind NGINX, Cloudflare, or AWS ALB for TLS/SSL termination, HTTP/2 or HTTP/3 support, and edge-level DDoS mitigation.
2. **Process Management:** Run backend with an ASGI server such as `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1` (or manage worker processes via systemd/supervisord).
3. **Storage Persistence:** Ensure the `backend/data/` (SQLite database) and `uploads/` directories reside on persistent, backed-up volumes.
4. **Secrets Management:** Supply production secrets and configuration via environment variables or secret managers (e.g., HashiCorp Vault, AWS Secrets Manager). Never hard-code credentials in code repositories.

---

## STAGE 11 — DEPLOYMENT & PRODUCTION READINESS

Stage 11 establishes a fully reproducible, containerized, and automated deployment architecture for the RASS-BUILDER platform across local workstations, Docker containers, and GitHub Actions CI/CD workflows.

```
                         [ Git Repository ]
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
 [ GitHub Actions CI/CD ]                     [ Container Runtime ]
 ├── Python 3.11 / 3.12 Matrix                ├── Multi-Stage Docker Build
 ├── pip install requirements-dev.txt         │   ├── Stage 1: Node 20 SPA Compilation
 ├── compileall bytecode check                │   └── Stage 2: Python 3.12-slim Runtime
 ├── python -m database.schema init           ├── Non-Root appuser Execution
 ├── pytest (121 Automated Tests)             ├── Docker Healthcheck (GET /health)
 └── npm run build validation                 └── Docker Compose Volume Orchestration
```

---

### A. Requirements

- **Operating System:** Linux (Ubuntu 22.04+ / Debian 12+), macOS (13+), or Windows 10/11.
- **Python:** Python 3.10, 3.11, or 3.12.
- **Node.js (for frontend compilation):** Node.js 20.x+ and npm 10.x+.
- **Containerization (optional):** Docker 24.0+ and Docker Compose 2.20+.
- **Hardware Minimums:** 2 CPU cores, 4 GB RAM, 2 GB free disk space.

---

### B. Installation

#### 1. Clone & Set Up Python Environment
```bash
# Clone repository
git clone https://github.com/organization/RASS-BUILDER.git
cd RASS-BUILDER

# Create and activate Python virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
```

#### 2. Install Python Dependencies
```bash
# Install runtime dependencies:
pip install -r requirements.txt

# Or install runtime + testing dependencies:
pip install -r requirements-dev.txt
```

#### 3. Install & Build Frontend SPA
```bash
cd frontend
npm install
npm run build
cd ..
```

---

### C. Environment Configuration

Copy the template configuration file:
```bash
cp .env.example .env
```

Key environment variables:
| Variable | Default | Production Recommendation | Description |
|---|---|---|---|
| `RASS_ENV` | `production` | `production` | Operational environment mode. |
| `RASS_LOG_LEVEL` | `INFO` | `INFO` or `WARNING` | Logging verbosity (never `DEBUG` in prod). |
| `RASS_DB_PATH` | `backend/data/rass_builder.db` | Mount to persistent storage | Relational SQLite database path. |
| `RASS_CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Set to your domain | Allowed client origins whitelist. |
| `RASS_MAX_UPLOAD_SIZE_MB` | `25` | `25`–`50` | Maximum file upload size limit in MB. |
| `RASS_RATE_LIMIT_ENABLED` | `1` | `1` | Active sliding-window rate limiting. |
| `RASS_REQUIRE_AUTH` | `0` | `1` (if strict) | Enforce authentication globally. |
| `RASS_MODEL_PATH` | *(empty)* | Optional path to `.pt` | Path to trained PyTorch weights. |

---

### D. Database Initialization

Database creation and table migrations are 100% deterministic and idempotent:
```bash
# Initialize database schema and performance indexes:
python backend/scripts/init_db.py

# Or run via Python module:
python -m database.schema
```

This safely creates `jobs`, `analysis_results`, `users`, `sessions`, `audit_logs`, and `schema_versions` tables without overwriting existing data.

---

### E. Model Setup

The Stage 5 PyTorch DNA Transformer foundation runs out of the box with certified unvalidated safeguards:
- **Default State:** Operates safely without a weights file, computing exact numerical sequence embeddings, attention representations, and GC/motif pattern checkpoints.
- **Custom Model Checkpoint:** If you have trained weights, provide the path via environment variable:
  ```bash
  export RASS_MODEL_PATH="/path/to/stage5_transformer.pt"
  ```
- Missing files produce a clear operational error (`Configured model checkpoint not found at: ...`) rather than crashing or inventing random predictions.

---

### F. Backend Startup

#### Production Mode (using Uvicorn ASGI Server):
```bash
# Start backend server on port 8000:
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
```

The backend automatically:
1. Validates configuration settings without leaking secrets.
2. Initializes or verifies the persistent SQLite database.
3. Automatically launches the asynchronous background worker thread.
4. Mounts compiled frontend SPA assets (`frontend/dist/`) if present.
5. Injects security headers, correlation IDs, and rate limiters.

---

### G. Worker Startup

RASS-BUILDER supports two worker deployment models:

#### Mode 1: Integrated Worker (Default & Recommended for Single-Server)
The background worker thread runs automatically inside the backend process. No separate process or command is needed.

#### Mode 2: Standalone Worker Daemon (Decoupled / Distributed Deployments)
For high-volume multi-process or containerized worker pools:
```bash
python backend/scripts/run_worker.py
```
The standalone worker recovers stale jobs on startup, polls the database for `QUEUED` jobs, executes the Stage 4 -> 5 -> 6 pipeline, records audit events, and handles `SIGINT`/`SIGTERM` gracefully.

---

### H. Frontend Usage

#### Unified Single-Port Serving (Production):
When `frontend/dist/` is built, the backend serves both API and Web UI:
- Open your browser at: `http://localhost:8000/` or `http://localhost:8000/app`

#### Independent Development Mode (with Hot Reload):
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` (or `http://localhost:5173`). Vite dev server proxies API calls to `http://localhost:8000`.

---

### I. Running Tests

Run the complete 121-test automated test suite across all Stages 4–11:
```bash
# Run complete test suite:
pytest -v

# Run Stage 11 deployment tests only:
pytest -v tests/test_stage11_deployment_readiness.py
```

---

### J. Docker Deployment

#### 1. Build and Run via Docker Compose:
```bash
# Build multi-stage image and start unified web service:
docker compose up -d --build

# View container logs:
docker compose logs -f

# Check container health status:
docker compose ps

# Stop containers:
docker compose down
```

#### 2. Build Single Docker Image Directly:
```bash
# Build image:
docker build -t rass-builder:latest .

# Run container with persistent volumes:
docker run -d \
  --name rass-builder-app \
  -p 8000:8000 \
  -v rass_data:/app/backend/data \
  -v rass_uploads:/app/uploads \
  rass-builder:latest
```

---

### K. CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically executes on every `push` and `pull_request`:
1. **Matrix Testing:** Runs automated pytest suite on Python 3.11 and Python 3.12.
2. **Bytecode Compilation:** Runs `compileall` to catch syntax or import regressions.
3. **Frontend Validation:** Runs `npm ci` and `npm run build` on Node.js 20.
4. **Security Hygiene:** Verifies no live `.env` files or database binaries are tracked by Git.

---

### L. Production Configuration Checklist

- [x] Set `RASS_ENV=production`
- [x] Configure explicit `RASS_CORS_ORIGINS` to match your domain
- [x] Mount `backend/data/` and `uploads/` to persistent storage volumes
- [x] Run container under non-root user `appuser` (UID 1000)
- [x] Ensure TLS/HTTPS termination at reverse proxy / load balancer
- [x] Verify rate limiting is enabled (`RASS_RATE_LIMIT_ENABLED=1`)

---

### M. Health & Readiness Probes

- **Process Liveness Probe:** `GET /health`
  ```bash
  curl -f http://localhost:8000/health
  # Response: {"status":"healthy","service":"rass-builder-api",...}
  ```
- **Deep Readiness Probe:** `GET /ready`
  ```bash
  curl -f http://localhost:8000/ready
  # Response: {"status":"ready","dependencies":{"database":"ok","worker":"ok","storage":"ok"}}
  ```

---

### N. Troubleshooting

1. **Port 8000 already in use:**
   - Change port via environment variable: `PORT=8080 python -m uvicorn main:app --port 8080 --app-dir backend`
2. **Database Locked (`sqlite3.OperationalError: database is locked`):**
   - SQLite WAL mode is pre-configured with a 10,000ms busy timeout. Ensure the database file resides on a local or block-storage filesystem (avoid NFS/SMB network shares).
3. **CORS Blocked in Browser:**
   - Add your frontend host URL to `RASS_CORS_ORIGINS` in `.env`.
4. **Worker Not Picking Up Jobs:**
   - Verify `GET /ready` returns `"worker": "ok"`. Check server logs for worker errors or run `python backend/scripts/run_worker.py` in standalone mode.





