"""
Entry point of the backend. Creates the FastAPI app, sets up CORS and plugs in every router.

Run it:
    on this laptop only : uvicorn app.main:app --reload
    for the phones      : uvicorn app.main:app --host 0.0.0.0 --port 8000   (no --reload, one worker)

Owner: Yehia. Nobody else needs to edit this file: every router is already included below.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (importing it registers the 4 tables on Base)
from app.database import Base, engine
from app.routers import auth, groups, messages, metrics, stream, users, ws

# Create any missing tables on startup (never changes or drops existing ones).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Real Time Chat API")

# ---------------------------------------------------------------------------
# CORS
# The React app is served from port 5173 and calls this API on port 8000. A different port
# counts as a different "origin", so the phone's browser blocks the calls unless we allow it.
# The regex allows port 5173 on localhost and on any private Wi-Fi / hotspot address
# (192.168.x.x, 10.x.x.x, 172.16-31.x.x), so nothing has to change when the laptop's IP changes.
# (CORS does not apply to WebSockets, so /ws is not affected by this.)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1"
        r"|192\.168\.\d{1,3}\.\d{1,3}"
        r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):5173"
    ),
    allow_methods=["*"],
    allow_headers=["*"],  # needed for the Authorization: Bearer header
)


@app.get("/", status_code=200)
def root():
    return {"message": "I LOVE YEHIA"}


# ---------------------------------------------------------------------------
# Routers (one per file in app/routers/). Owners are listed in each file.
# ---------------------------------------------------------------------------
app.include_router(auth.router)      # /auth/register, /auth/login
app.include_router(users.router)     # /users ...             (Eyad)
app.include_router(groups.router)    # /groups ...            (Gelan)
app.include_router(messages.router)  # /messages, /sync ...   (Maryam)
app.include_router(metrics.router)   # /metrics               (Eyad)
app.include_router(ws.router)        # /ws      protocol 1    (Yehia)
app.include_router(stream.router)    # /stream  protocol 2    (Yehia)
