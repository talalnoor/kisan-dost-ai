# API Contracts — Kisan Dost AI

**Base URL (dev):** `http://localhost:8000/api/v1`
**Base URL (prod):** set by `NEXT_PUBLIC_API_URL` env var, points to Railway deployment

## Conventions

- All requests requiring auth send header: `Authorization: Bearer <supabase_jwt>`
- All responses use this envelope:
```json
{ "success": true, "data": { }, "error": null }
```
On failure:
```json
{ "success": false, "data": null, "error": { "code": "STRING_CODE", "message": "human readable" } }
```
- All timestamps are ISO 8601 UTC strings.
- All IDs are UUID strings.

---

## 1. `POST /disease/analyze`

Analyzes a crop leaf image for disease or pest.

**Auth:** required
**Content-Type:** `multipart/form-data`

**Request fields:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `image` | file | yes | jpg/png, max 5MB |
| `crop_id` | string (uuid) | yes | must belong to the authenticated user |
| `scan_type` | string | no | `"disease"` (default) or `"pest"` |

**Success response (`200`) `data`:**
```json
{
  "scan_id": "8f14e...",
  "scan_type": "disease",
  "disease": "Tomato Early Blight",
  "confidence": 0.94,
  "severity": "moderate",
  "low_confidence": false,
  "symptoms": ["Dark concentric-ring spots on lower leaves", "Yellowing around lesions"],
  "causes": ["Fungal pathogen (Alternaria solani)", "Favored by warm, humid conditions"],
  "treatment": ["Apply copper-based or chlorothalonil fungicide", "Remove and destroy infected leaves"],
  "prevention": ["Crop rotation", "Avoid overhead watering", "Ensure adequate plant spacing"],
  "weather_risk": {
    "level": "high",
    "reason": "High humidity (84%) and rain probability increase fungal spread risk"
  },
  "created_at": "2026-08-21T10:30:00Z"
}
```

If `low_confidence: true`, `disease` will still contain the best guess, but the frontend MUST visibly show a "not certain — try a clearer photo" state rather than presenting it as a confirmed diagnosis.

**Error responses:**
| Status | `error.code` | When |
|---|---|---|
| 400 | `INVALID_IMAGE` | Wrong file type or corrupted image |
| 400 | `IMAGE_TOO_LARGE` | Exceeds 5MB |
| 422 | `MISSING_CROP_ID` | `crop_id` not provided or invalid |
| 404 | `CROP_NOT_FOUND` | `crop_id` doesn't belong to this user |
| 503 | `CV_PROVIDER_UNAVAILABLE` | Model API down/timeout — frontend shows retry message |
| 401 | `UNAUTHORIZED` | Missing/invalid token |

---

## 2. `POST /chat`

Sends a message to the farming assistant.

**Auth:** required

**Request body:**
```json
{
  "session_id": null,
  "message": "Why are my tomato leaves turning yellow?",
  "language": "en",
  "crop_id": "3ab21..."
}
```
- `session_id`: `null` to start a new conversation, or an existing session's UUID to continue it.
- `language`: `"en"` or `"ur"`.
- `crop_id`: optional — if provided, the assistant uses that crop's latest scan/context.

**Success response (`200`) `data`:**
```json
{
  "session_id": "9c22e...",
  "reply": "Yellowing on tomato leaves is often a sign of nitrogen deficiency or early blight...",
  "language": "en",
  "created_at": "2026-08-21T10:32:00Z"
}
```

**Error responses:**
| Status | `error.code` | When |
|---|---|---|
| 422 | `EMPTY_MESSAGE` | `message` is blank |
| 404 | `SESSION_NOT_FOUND` | `session_id` provided but doesn't exist/belong to user |
| 503 | `LLM_UNAVAILABLE` | Qwen API timeout — see fallback note below |
| 401 | `UNAUTHORIZED` | |

**Fallback behavior:** if the LLM call fails, the backend returns `success: true` with a templated reply built from structured data only (no error to the user) — this is a design choice, not a bug, so the chat never feels "broken" even if the LLM provider hiccups. Ashar should render this reply exactly like a normal one.

---

## 3. `GET /weather?lat={lat}&lon={lon}`

**Auth:** required

**Success response (`200`) `data`:**
```json
{
  "temperature": 32.5,
  "humidity": 84,
  "rain_probability": 0.72,
  "condition": "cloudy",
  "fetched_at": "2026-08-21T10:00:00Z"
}
```

**Error responses:**
| Status | `error.code` | When |
|---|---|---|
| 400 | `INVALID_COORDINATES` | Missing/malformed lat/lon |
| 503 | `WEATHER_PROVIDER_UNAVAILABLE` | Frontend should hide the weather widget gracefully, not block the page |

---

## 4. `GET /crops`

**Auth:** required

**Success response (`200`) `data`:**
```json
{
  "crops": [
    { "id": "3ab21...", "crop_type": "Tomato", "planted_date": "2026-06-01", "stage": "flowering" }
  ]
}
```

## 5. `POST /crops`

**Auth:** required

**Request body:**
```json
{ "crop_type": "Tomato", "planted_date": "2026-06-01", "stage": "seedling" }
```

**Success response (`201`) `data`:**
```json
{ "id": "3ab21...", "crop_type": "Tomato", "planted_date": "2026-06-01", "stage": "seedling", "created_at": "2026-08-21T09:00:00Z" }
```

**Error responses:** `422 VALIDATION_ERROR` for missing/invalid fields.

---

## 6. `GET /history?limit={n}&offset={n}`

Returns past disease/pest scans for the dashboard.

**Auth:** required
**Query params:** `limit` (default 20), `offset` (default 0)

**Success response (`200`) `data`:**
```json
{
  "scans": [
    {
      "scan_id": "8f14e...",
      "crop_id": "3ab21...",
      "scan_type": "disease",
      "disease": "Tomato Early Blight",
      "confidence": 0.94,
      "severity": "moderate",
      "created_at": "2026-08-21T10:30:00Z"
    }
  ],
  "total": 12
}
```

---

## 7. `GET /tasks` / `POST /tasks` (stretch goal — build after core is stable)

**`GET /tasks`** → `data: { "tasks": [ { "id", "task_type", "due_date", "status", "crop_id" } ] }`

**`POST /tasks`** body: `{ "crop_id", "task_type", "due_date" }` → returns created task.

---

## Frontend Development Note for Ashar

Until each endpoint is live, build against these exact JSON shapes using mock data / MSW / static fixtures. When the real backend is ready, swapping the mock for a real fetch call should require **zero changes to component code** — if it does, that means a component made an assumption not in this doc, and that's worth flagging to Talal rather than quietly patching around it.