from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import analyze

app = FastAPI(title="DepViz")


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://127.0.0.1:8000", "http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes
app.include_router(analyze.router, prefix="/api")

@app.get("/")
def root():
    return {"msg": "DepViz backend running 🚀"}
