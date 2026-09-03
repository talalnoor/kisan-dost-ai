# Kisan Dost AI 🌾

AI-powered farming assistant for Pakistani farmers — built for the Alibaba Cloud AI Hackathon (Bano Qabil / Alkhidmat Foundation Pakistan).

**Live backend:** https://kisan-dost-ai-production.up.railway.app
**API docs (Swagger):** https://kisan-dost-ai-production.up.railway.app/docs
**Live frontend:** https://kisan-dost-ai-rho.vercel.app

## What it does

Farmers upload a photo of a diseased crop leaf and get an instant diagnosis — disease name, confidence, severity, symptoms, causes, treatment, and prevention — combined with live weather data to assess disease-spread risk. A bilingual (English/Urdu) AI farming assistant answers follow-up questions about crops, fertilizers, irrigation, and more.

## Team

| Name | Role |
|---|---|
| Muhammad Talal Noor | Team Lead — Backend, AI orchestration, architecture, deployment |
| Ashar Rizwan | Frontend Engineer |
| Zain ul Abidin | AI Data & Integration Engineer |

## Tech stack

- **Backend:** FastAPI (Python), deployed on Railway
- **Database & Auth:** Supabase (PostgreSQL, Row Level Security)
- **LLM:** Qwen via Alibaba Cloud Model Studio (DashScope)
- **Weather:** OpenWeatherMap
- **Frontend:** Next.js, TypeScript, Tailwind CSS (deployed on Vercel)

## Working features

- ✅ Authentication (signup, login, JWT verification)
- ✅ Crop management (CRUD)
- ✅ Real AI disease detection (HuggingFace ViT model, 38 disease/healthy classes across tomato, potato, corn, apple, grape, etc.) with confidence handling and graceful fallback
- ✅ Weather-integrated disease risk assessment
- ✅ Scan history
- ✅ Farming task tracking
- ✅ Bilingual AI farming assistant (Qwen LLM) — safety-checked to avoid giving unverified exact fertilizer dosages
- ✅ Live weather data
- ✅ Full frontend: login, signup, dashboard (with live stats), scan/diagnose, chat — deployed and live

## Local setup (frontend)

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to the live backend or localhost:8000
npm run dev
```

Runs at `http://localhost:3000`.

## Documentation

Full architecture, API contracts, database schema, and team responsibilities are in [`/docs`](./docs). Read these before making any architectural changes.

## Local setup (backend)

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys
uvicorn app.main:app --reload
```

API will be running at `http://127.0.0.1:8000`, docs at `http://127.0.0.1:8000/docs`.

## License

Built for the Alibaba Cloud AI Hackathon 2026.