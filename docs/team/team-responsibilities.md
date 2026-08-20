# Team Responsibilities — Kisan Dost AI

## Team

| Name | Role | Owns |
|---|---|---|
| Muhammad Talal Noor | Team Lead / AI + Backend Lead | `backend/`, `docs/`, deployment, integration, technical review |
| Ashar Rizwan | Frontend Engineer | `frontend/` |
| Zain ul Abidin | AI Data & Integration Engineer | `ai/`, disease/pest model research, knowledge base content |

## Talal — Team Lead / Backend

- System architecture and final technical decisions
- FastAPI backend, API design
- AI orchestration (CV → knowledge → recommendation → LLM pipeline)
- LLM integration (Qwen/DashScope)
- Weather integration
- Recommendation engine logic
- Supabase integration (DB + Auth)
- Backend deployment (Railway)
- GitHub coordination, PR review, merging to `main`
- Final system reliability and integration testing

## Ashar — Frontend

- Next.js + TypeScript + Tailwind
- All UI: dashboard, disease result screen, chat UI, weather UI, voice UI (stretch), calendar UI (stretch)
- Responsive, mobile-first design
- Frontend integration against the agreed API contract (`docs/api/api-contracts.md`)
- Should build against mock data matching the contract while backend is in progress — no blocking on Talal

## Zain — AI Data & Integration

- Research and select the CV model (disease + pest) — evaluate 2-3 pretrained options, document accuracy/coverage tradeoffs in `docs/ai/ai-pipeline.md`
- Build and maintain the structured agricultural knowledge base (`backend/app/knowledge/`) — symptoms, causes, treatment, prevention per disease
- Write and refine LLM prompts/context for the farming assistant
- Test AI outputs for accuracy before they ship
- Implement `backend/app/providers/cv/` (the concrete CV provider — logic in `services/` stays Talal's)

## Working Rules

1. Stay inside your owned folder. Need to touch someone else's area? Message them first — don't just push it.
2. `docs/` and `tests/` are shared — anyone can update these, but architecture-level changes to `docs/architecture/` need Talal's sign-off since it's the team's source of truth.
3. All Claude/AI-assistant sessions (yours included) should be told: "Read `/docs` before making architectural decisions — do not redesign independently."
4. Every feature branch → Pull Request → Talal reviews → merge to `main`. No direct pushes to `main`.