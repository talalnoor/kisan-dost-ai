# Database Schema — Kisan Dost AI

Supabase Postgres, region `ap-south-1` (Mumbai). All tables have Row Level Security enabled — a user can only ever read/write their own data, enforced at the database level.

**Important — GRANT permissions:** RLS policies alone are not enough. After creating any new table, also run a table-level GRANT, e.g.:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON public.<table_name> TO authenticated;
```
(adjust the verb list to match what the table's RLS policies actually allow). Without this, every query fails with `permission denied for table ...` even though RLS is configured correctly — this bit us once during `crops` testing.

## `profiles`
Extends `auth.users` with app-specific fields. 1:1 with the auth user.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | References `auth.users(id)`, cascade delete |
| `full_name` | text | |
| `preferred_language` | text | `'en'` or `'ur'`, default `'en'` |
| `region` | text | |
| `created_at` | timestamptz | default `now()` |

**RLS:** select/update/insert — own row only (`auth.uid() = id`).

---

## `crops`
A farmer's registered crops.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | default `gen_random_uuid()` |
| `user_id` | uuid, FK → `auth.users` | cascade delete |
| `crop_type` | text | not null |
| `planted_date` | date | |
| `stage` | text | e.g. seedling, flowering, harvest |
| `created_at` | timestamptz | default `now()` |

**RLS:** full CRUD, own rows only. **Index:** `user_id`.

---

## `disease_scans`
Every disease/pest analysis result. Shared table for both scan types (`scan_type` column) rather than a separate `pest_scans` table.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `user_id` | uuid, FK → `auth.users` | cascade delete |
| `crop_id` | uuid, FK → `crops` | `on delete set null` — history survives crop deletion |
| `scan_type` | text | `'disease'` or `'pest'`, default `'disease'` |
| `disease_label` | text | machine key, e.g. `tomato_early_blight` |
| `disease_display_name` | text | human-readable, e.g. "Tomato Early Blight" |
| `confidence` | numeric(4,3) | 0.000–1.000 |
| `severity` | text | e.g. mild/moderate/severe |
| `low_confidence` | boolean | default false |
| `symptoms` | jsonb | array of strings |
| `causes` | jsonb | array of strings |
| `treatment` | jsonb | array of strings |
| `prevention` | jsonb | array of strings |
| `weather_snapshot` | jsonb | weather context at scan time |
| `image_url` | text | Supabase Storage path |
| `created_at` | timestamptz | default `now()` |

**RLS:** select/insert only, own rows — scans are permanent history, not editable. **Indexes:** `user_id`, `crop_id`, `created_at desc`.

---

## `chat_sessions`
One assistant conversation.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `user_id` | uuid, FK → `auth.users` | cascade delete |
| `crop_id` | uuid, FK → `crops`, nullable | `on delete set null` |
| `created_at` | timestamptz | |

**RLS:** select/insert, own rows only.

---

## `chat_messages`
Individual turns within a session. No direct `user_id` — ownership is inherited through `chat_sessions`.

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `session_id` | uuid, FK → `chat_sessions` | cascade delete |
| `role` | text | `'user'` or `'assistant'` |
| `content` | text | not null |
| `language` | text | `'en'` or `'ur'`, default `'en'` |
| `created_at` | timestamptz | |

**RLS:** select/insert, via subquery checking the parent session's `user_id` matches `auth.uid()`. **Index:** `session_id`.

---

## `farming_tasks`
Calendar/task items (stretch feature).

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `user_id` | uuid, FK → `auth.users` | cascade delete |
| `crop_id` | uuid, FK → `crops`, nullable | `on delete set null` |
| `task_type` | text | not null |
| `due_date` | date | |
| `status` | text | `'pending'` / `'completed'` / `'skipped'`, default `'pending'` |
| `created_at` | timestamptz | |

**RLS:** full CRUD, own rows only. **Index:** `user_id`.

---

## Deliberately not created
- Separate `pest_scans` table — merged into `disease_scans` via `scan_type`.
- `farms` table — single-farm-per-user assumed for MVP.
- `weather_records` table — weather is fetched live and snapshotted into `disease_scans.weather_snapshot`, no standalone history table needed.
- `recommendations` table — generated on the fly by the recommendation engine, not persisted separately.