from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.db_config import init_db
from app.routes import router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized successfully.")
    print("Starting FastAPI application...")
    yield

app = FastAPI(
    title="Helios Form API",
    description="API for managing dynamic forms and submissions",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)
