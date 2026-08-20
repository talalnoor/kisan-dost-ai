# Kisan Dost AI — System Architecture (Phase 1)

**Status:** Draft for team-lead approval
**Author:** Muhammad Talal Noor (Team Lead)
**Last updated:** Aug 21, 2026

---

## A. Executive Overview

Kisan Dost AI is an AI-powered farming assistant for Pakistani farmers. Core value: point a phone at a diseased leaf, get a trustworthy diagnosis with weather-aware treatment advice, in Urdu or English, backed by a real conversational assistant — not a single-page demo.

Given the compressed timeline (days, not weeks), this architecture is deliberately narrow: **one confident end-to-end flow**, built on infrastructure that removes work rather than adding "impressive" complexity. Every "should have" / "bonus" feature is scoped so it can be dropped without breaking the demo.

Non-negotiable architectural rule from the brief, and one I agree with: **the LLM never classifies the disease image directly.** It explains and converses. A dedicated CV model classifies. This is both more credible to judges and more reliable — LLMs guessing diseases from images hallucinate confidently, which is exactly what you don't want live on stage.

---

## B. Product Architecture (conceptual layers)

```
Farmer-facing experience  →  Application intelligence  →  AI/external services  →  Data
```

Four layers, each replaceable independently:

1. **Experience layer** (Next.js): what the farmer sees and touches.
2. **Intelligence layer** (FastAPI services): orchestrates AI calls, applies business rules, decides what's confident enough to show.
3. **Provider layer**: swappable CV model, LLM, weather API, speech services — accessed only through interfaces, never called directly from route handlers.
4. **Data layer**: Supabase Postgres + Auth.

The point of layer 3 being isolated: if DashScope rate-limits you mid-demo, you swap to a fallback provider by changing one config value, not by touching business logic.

---

## C. System Architecture Diagram

```
                         ┌─────────────────────────┐
                         │      Next.js Frontend    │
                         │  (Vercel)                │
                         └────────────┬─────────────┘
                                      │ HTTPS / REST (JSON, versioned /api/v1)
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI Backend     │
                         │  (Railway)                │
                         │                            │
                         │  ┌──────────────────────┐ │
                         │  │ Application Services │ │
                         │  │ - auth (delegates)    │ │
                         │  │ - disease analysis    │ │
                         │  │ - pest analysis (opt) │ │
                         │  │ - farming assistant   │ │
                         │  │ - weather intelligence│ │
                         │  │ - recommendation eng. │ │
                         │  │ - voice (opt)          │ │
                         │  │ - farming calendar     │ │
                         │  └──────────┬────────────┘ │
                         │             │               │
                         │  ┌──────────▼────────────┐ │
                         │  │ Provider Interfaces    │ │
                         │  │ (ports, not concrete)  │ │
                         │  └──────────┬────────────┘ │
                         └─────────────┼───────────────┘
                                       │
              ┌────────────┬──────────┼───────────┬─────────────┐
              ▼            ▼          ▼            ▼             ▼
        CV Model API   Qwen LLM   Weather API   STT/TTS      Supabase
        (HF Inference) (DashScope) (OpenWeather) (optional)  (Postgres+Auth)
```

---

## D. Frontend Architecture (Ashar's domain — for context, not prescription)

- Next.js (App Router) + TypeScript + Tailwind.
- Talks to the backend **only** through the versioned API contract in section K — never assumes response shape.
- State: server data via fetch/React Query-style pattern; no need for heavy global state management at MVP scale.
- Auth: Supabase client SDK handles session/token; frontend attaches the Supabase JWT to backend requests.
- Mock-data-first: Ashar can build every screen against the finalized JSON contracts before the backend is done — this is the whole point of finalizing contracts in Phase 1.

I won't dictate component structure — that's Ashar's call within his folder. My interest as team lead is only the boundary: the API contract.

---

## E. Backend Architecture (mine)

**Pattern: modular monolith**, organized by domain, not by technical layer:

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, router mounting
│   ├── core/
│   │   ├── config.py           # env/settings
│   │   ├── security.py         # Supabase JWT verification
│   │   └── exceptions.py       # shared error handling
│   ├── api/v1/
│   │   ├── disease.py
│   │   ├── pest.py
│   │   ├── chat.py
│   │   ├── weather.py
│   │   ├── crops.py
│   │   ├── history.py
│   │   └── tasks.py
│   ├── services/                # business logic, one per domain
│   │   ├── disease_service.py
│   │   ├── weather_service.py
│   │   ├── recommendation_service.py
│   │   ├── chat_service.py
│   │   └── voice_service.py
│   ├── providers/               # concrete implementations of provider interfaces
│   │   ├── cv/
│   │   │   ├── base.py          # abstract interface
│   │   │   └── hf_plant_model.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   └── qwen_provider.py
│   │   ├── weather/
│   │   │   ├── base.py
│   │   │   └── openweather_provider.py
│   │   └── speech/ (optional, later)
│   ├── models/                   # Pydantic schemas (request/response contracts)
│   ├── db/                       # Supabase client, queries
│   └── knowledge/                # structured disease/pest facts (not LLM-generated)
└── tests/
```

**Why services vs. providers are separate:** a service (`disease_service.py`) contains the *logic* — "if confidence < 0.6, ask for a clearer photo instead of guessing." A provider (`hf_plant_model.py`) is just "call this API, return this shape." Swapping providers should never require touching service logic. This is the one piece of "unnecessary-sounding" abstraction I'm keeping, because it directly serves the brief's requirement that CV/LLM/weather/speech all be replaceable — and it costs almost nothing to build correctly from day one vs. retrofitting under deadline pressure.

**Rejected for MVP:** microservices, message queues, Redis, Kubernetes. No justification for the added ops burden in a few-day hackathon. If we need caching for weather data later, an in-process cache (or a Postgres table with a TTL check) is enough.

---

## F. AI Architecture

```
Leaf Image
   ↓
CV Model (pretrained plant-disease classifier via HF Inference API)
   ↓
{ disease_label, confidence }
   ↓
Structured Knowledge Lookup (knowledge/diseases.json — symptoms, causes, treatment, prevention)
   ↓
+ Weather Context (from weather_service)
+ Crop Context (from crops table)
   ↓
Recommendation Engine (rule-based: confidence thresholds, risk scoring)
   ↓
Qwen LLM — turns structured result into a natural, conversational English/Urdu explanation
   ↓
Response to Frontend
```

Key discipline: **the knowledge (symptoms/causes/treatment) lives in your own structured data, not in LLM output.** The LLM's job is phrasing and conversation, not being the source of agricultural facts. This is both more accurate and lets you demo the "why" behind a recommendation without worrying about the LLM inventing a treatment.

**Confidence handling (important, not in your original brief but necessary):** if CV confidence is below a threshold (e.g. 0.5), the system should say so honestly ("uncertain — try a clearer photo of the affected leaf") rather than presenting a low-confidence guess as fact. This is a two-line rule in `disease_service.py` and meaningfully raises the product's credibility with judges who will absolutely try to break it with a bad photo.

**Provider choice — CV model:** Use a pretrained HuggingFace plant-disease model (PlantVillage-trained, e.g. models under `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification` or similar — Zain should evaluate 2–3 candidates and pick by class coverage + accuracy) via the free HF Inference API. No training pipeline, no GPU management, deployable in an afternoon.

**Provider choice — LLM:** Qwen (`qwen-plus`) via DashScope's OpenAI-compatible endpoint, free tier, no card required. Fallback interface ready for Groq if needed.

---

## G. Database Architecture

Minimal, justified set for MVP — I'm deliberately not creating every table from your draft list yet.

| Table | Purpose | Key fields | Notes |
|---|---|---|---|
| `profiles` | Extends Supabase `auth.users` with app-specific fields | `id (FK auth.users)`, `full_name`, `preferred_language`, `region` | 1:1 with auth user |
| `crops` | Farmer's registered crops | `id`, `user_id`, `crop_type`, `planted_date`, `stage` | user-owned, RLS on `user_id` |
| `disease_scans` | Each disease analysis result | `id`, `user_id`, `crop_id`, `image_url`, `disease_label`, `confidence`, `severity`, `weather_snapshot (jsonb)`, `created_at` | history + dashboard source |
| `chat_sessions` | One assistant conversation | `id`, `user_id`, `crop_id (nullable)`, `created_at` | groups messages |
| `chat_messages` | Individual turns | `id`, `session_id`, `role`, `content`, `language`, `created_at` | |
| `farming_tasks` | Calendar/task items | `id`, `user_id`, `crop_id`, `task_type`, `due_date`, `status` | should-have, not must-have |

**Deliberately deferred:** `farms` (multi-farm support — not needed for single-crop demo flow), `pest_scans` (can reuse `disease_scans` with a `scan_type` column instead of a parallel table — less schema duplication), `weather_records` (weather is fetched live and snapshotted into `disease_scans.weather_snapshot`, no need for a standalone historical table at MVP scale), `recommendations` (generated on the fly, not persisted separately, unless you specifically want to show "recommendation history" — flag if so).

All tables get Row Level Security: `user_id = auth.uid()`.

---

## H. Authentication Architecture

Supabase Auth, email/password (fastest to demo, no SMS/OTP flakiness on stage). Frontend obtains a JWT from Supabase directly. Backend verifies that JWT on every request (using Supabase's JWT secret / JWKS) — backend never re-implements auth logic, only verification middleware in `core/security.py`.

---

## I. API Architecture

All endpoints versioned under `/api/v1`. Every response follows a consistent envelope so the frontend never has to guess:

```json
{ "success": true, "data": { ... }, "error": null }
```

### `POST /api/v1/disease/analyze`
- **Auth:** required
- **Request:** multipart form — `image` (file), `crop_id` (string)
- **Response `data`:**
```json
{
  "scan_id": "uuid",
  "disease": "Tomato Early Blight",
  "confidence": 0.94,
  "severity": "moderate",
  "symptoms": ["..."],
  "causes": ["..."],
  "treatment": ["..."],
  "prevention": ["..."],
  "weather_risk": { "level": "high", "reason": "high humidity increases fungal spread" },
  "low_confidence": false
}
```
- **Errors:** `400` invalid/unsupported image, `422` missing crop_id, `503` CV provider unavailable (with fallback message, not a raw 500)

### `POST /api/v1/chat`
- **Auth:** required
- **Request:** `{ "session_id": "uuid | null", "message": "string", "language": "en | ur", "crop_id": "uuid | null" }`
- **Response `data`:** `{ "session_id": "uuid", "reply": "string", "language": "en | ur" }`

### `GET /api/v1/weather?lat=&lon=`
- **Auth:** required
- **Response `data`:** `{ "temperature": 32, "humidity": 84, "rain_probability": 0.72, "condition": "cloudy" }`
- **Errors:** `503` weather provider down — **must not block disease analysis**, see Section R

### `GET /api/v1/crops` / `POST /api/v1/crops`
- Standard CRUD scoped to `user_id`.

### `GET /api/v1/history`
- **Response `data`:** paginated list of past `disease_scans` for dashboard.

### `GET|POST /api/v1/tasks`
- Should-have, same pattern as crops.

Pest detection reuses `/api/v1/disease/analyze` with a `scan_type` field rather than a separate endpoint family — less surface area to build and test under time pressure. Revisit if pest model behaves too differently.

---

## J. Weather Architecture

Provider: **OpenWeatherMap** (free tier, no card, well-documented, handles Pakistan coverage fine). Called server-side only (API key never touches frontend). `weather_service.py` converts raw weather → `{ level: low/medium/high, reason }` risk classification consumed by the recommendation engine — this mapping is a small rule table (e.g. humidity > 80% + condition = rain → high fungal risk), not an LLM call. Keeps it fast and deterministic.

---

## K. Voice Architecture (should-have — build only if core flow is solid with time to spare)

```
Audio → STT (e.g. Whisper via Groq, fast + free-tier friendly) → existing /api/v1/chat pipeline → TTS → audio back
```

No separate AI system — voice is a thin wrapper around the same chat service. If time runs out, this is the first thing cut; text chat already covers the "ask in English or Urdu" requirement.

---

## L. Repository / Folder Architecture

```
kisan-dost-ai/
├── frontend/
├── backend/
├── docs/
│   ├── architecture/system-architecture.md   ← this document
│   ├── api/api-contracts.md
│   ├── database/database-schema.md
│   ├── ai/ai-pipeline.md
│   ├── team/team-responsibilities.md
│   └── development/
│       ├── development-guide.md
│       └── git-workflow.md
├── README.md
├── .gitignore
└── .env.example
```

Dropped `ai/` as a top-level folder and `tests/` as top-level — CV model evaluation notes belong in `docs/ai/`, and tests belong inside `backend/tests/` and `frontend/__tests__/` respectively (co-located tests are easier to keep in sync than a parallel top-level tree). Flag if you disagree — easy to add back.

---

## M. Team Responsibility Architecture

| Owner | Folder | Cannot touch without lead approval |
|---|---|---|
| Talal | `backend/`, `docs/`, deployment, integration | — |
| Ashar | `frontend/` | `backend/`, API contracts |
| Zain | `backend/app/knowledge/`, `backend/app/providers/cv/`, model evaluation docs | `backend/app/api/`, `backend/app/services/` (logic), `frontend/` |

Zain owns the CV model choice and the disease knowledge base content — not the service logic that calls it. This matters: if Zain swaps models, only `providers/cv/hf_plant_model.py` should change.

---

## N. Git/GitHub Workflow

Single repo `kisan-dost-ai`, `main` as stable branch, feature branches per the pattern in your brief. I'll walk you through the actual commands step by step once you approve this document — not dumping them all now, per your own instruction to go one step at a time.

---

## O. Development Roadmap (revised for "a few days")

Given the timeline, phases 10 (voice) and 11 (pest) are **optional tail phases**, only attempted after 1–9 are demo-stable:

1. Architecture (this doc) — **today**
2. Repo foundation — same day
3. Backend foundation + Supabase schema/auth
4. Frontend foundation (parallel with 3, using mock data against the contract in Section I)
5. Disease AI pipeline (CV provider + knowledge + recommendation logic)
6. Weather intelligence
7. Farming assistant (chat, Qwen integration)
8. Dashboard/history
9. End-to-end integration + demo rehearsal
10. *(only if time remains)* Voice
11. *(only if time remains)* Pest detection, calendar

---

## P. MVP Prioritization (tightened)

**Must have (this is the whole demo):** disease detection with real CV model, result UI with confidence/severity, chat assistant in English+Urdu, weather-aware risk on the disease result, auth, history/dashboard, clean responsive UI, reliable happy-path.

**Cut to "if time permits":** voice, pest detection, farming calendar, fertilizer recommendation as a separate feature (fold basic fertilizer guidance into the disease treatment output instead of building it as a distinct system).

---

## Q. Security Considerations

- Supabase RLS on every user-owned table (`user_id = auth.uid()`).
- Image upload: validate MIME type + size limit (e.g. 5MB) before sending to CV provider — prevents abuse and wasted API calls.
- CORS restricted to your Vercel domain + localhost during dev.
- All provider API keys server-side only, never in frontend bundle.
- No custom password handling — Supabase owns that entirely.

---

## R. Failure / Fallback Strategy

| Failure | Behavior |
|---|---|
| Weather API down | Disease analysis still returns — `weather_risk: null` with a note, not a hard failure |
| CV model timeout/down | Return a clear "analysis service is temporarily unavailable, please retry" — never fabricate a fake diagnosis |
| LLM timeout | Fall back to a templated, structured-data-only response (no explanation prose, but treatment/symptoms still shown) |
| Low CV confidence | Say so explicitly, suggest a clearer photo — don't present as certain |
| Auth failure | Standard 401, frontend redirects to login |
| Voice failure | Falls back to text chat silently |

---

## S. Deployment Architecture

**Frontend → Vercel.** Not really a debate — it's built for Next.js.

**Backend → Railway over Render.** Reasoning specific to your situation: Railway's free/hobby tier has historically had simpler environment-variable management and faster cold-start behavior for FastAPI + background workers than Render's free tier, which sleeps aggressively and adds real latency to a live demo (a judge waiting 30+ seconds for the first request to wake up is a bad look). Railway also makes it trivial to add a Postgres addon later if you ever need something beyond Supabase. Both are fine engineering choices in general — this is a demo-day latency call, not a "Render is worse" claim.

**Database/Auth → Supabase**, managed, no deployment work needed.

---

## T. Hackathon Demo Strategy

Follow the flow in your brief almost exactly (login → select crop → upload leaf → disease + confidence + severity → weather risk → treatment → switch to Urdu → follow-up question → save → dashboard). One addition: **rehearse the low-confidence path too.** Judges poking at edge cases is common; showing the system say "I'm not confident, please try a clearer photo" instead of hallucinating is a stronger credibility signal than a string of perfect results.

---

## Open Questions for You (answer before Phase 2)

1. Fertilizer guidance folded into disease treatment output, or does the team want it as a visibly separate feature/screen?
2. OK to defer `pest_scans` as a shared table with `disease_scans` (via `scan_type`) rather than a parallel schema?
3. Confirm: Qwen (DashScope) as primary LLM, OpenWeatherMap as weather provider, HF-hosted pretrained model as CV provider — proceed on this basis?

Once you confirm, next step is Phase 2 — repository foundation, one Git command at a time.