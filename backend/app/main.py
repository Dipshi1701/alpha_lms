from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import Base, engine
from app.response import error_response, success_response
from app.seed import seed_database
from app.routes import auth, courses, users
from app.routes import scorm as scorm_routes

# Create all database tables (runs once on startup; safe to re-run)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=config.APP_NAME, debug=config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(scorm_routes.router, prefix="/api/scorm", tags=["scorm"])

# Serve uploaded SCORM files at /scorm-content/{course_id}/...
config.SCORM_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/scorm-content", StaticFiles(directory=str(config.SCORM_STORAGE_PATH)), name="scorm-content")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return error_response(
        message="Request failed",
        status_code=exc.status_code,
        error={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return error_response(
        message="Validation failed",
        status_code=422,
        error={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    # Keep error details generic to avoid leaking internals in production APIs.
    return error_response(
        message="Internal server error",
        status_code=500,
        error={"detail": str(exc) if config.DEBUG else "Unexpected error"},
    )


@app.on_event("startup")
def on_startup():
    seed_database()


@app.get("/health")
def health():
    return success_response(message="Health check successful", data={"status": "ok"})
