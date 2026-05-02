from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🔹 Import your routes
from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router

app = FastAPI()

# 🔹 Enable CORS (needed for React later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Register routes
app.include_router(chat_router)          # /upload, /ask, /files
app.include_router(auth_router, prefix="/auth")   # /auth/login, /auth/callback


# 🔹 Root test endpoint
@app.get("/")
def root():
    return {"message": "RAG Agent with Google Drive OAuth is running 🚀"}