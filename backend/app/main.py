from fastapi import FastAPI

app = FastAPI(title="Kisan Dost AI API")

@app.get("/")
def root():
    return {"status": "ok", "message": "Kisan Dost AI backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}