import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database.db import init_db, SessionLocal
from .api.cases import router as cases_router
from .api.evaluation import router as evaluation_router
from .api.workspaces import router as workspaces_router, ensure_default_workspaces
from .api.workflows import router as workflows_router
from .api.apps import router as apps_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and migrations
    init_db()
    # Pre-seed default workspaces and flagship workflows
    db = SessionLocal()
    try:
        ensure_default_workspaces(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-app AI workspace and orchestration platform across Gmail, Stripe, Slack, and developer apps.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(cases_router)
app.include_router(evaluation_router)
app.include_router(workspaces_router)
app.include_router(workflows_router)
app.include_router(apps_router)

@app.get("/api/health")
def health_check():
    # Detect component connection status
    gmail_connected = False
    if settings.MOCK_MODE:
        gmail_connected = True
    elif os.path.exists(settings.GMAIL_TOKEN_PATH) or os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
        gmail_connected = True

    stripe_status = "TEST MODE" if settings.is_stripe_test_mode else "INVALID_OR_NOT_TEST"

    slack_connected = False
    if settings.MOCK_MODE:
        slack_connected = True
    elif settings.SLACK_BOT_TOKEN and not settings.SLACK_BOT_TOKEN.startswith("xoxb-placeholder"):
        slack_connected = True

    openai_connected = bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_"))

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "mode": "MOCK MODE" if settings.MOCK_MODE else "LIVE MODE",
        "is_mock": settings.MOCK_MODE,
        "integrations": {
            "gmail": "CONNECTED" if gmail_connected else "AVAILABLE (MOCK)",
            "stripe": stripe_status,
            "slack": "CONNECTED" if slack_connected else "AVAILABLE (MOCK)",
            "openai": "CONNECTED" if openai_connected else "FALLBACK RECONCILER"
        },
        "version": "1.0.0"
    }

# Mount built frontend dist directory if present
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
