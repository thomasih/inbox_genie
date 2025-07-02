from fastapi import FastAPI
from .auth import router as auth_router
from .email_client import router as email_router, fetch_messages
from fastapi.responses import JSONResponse

app = FastAPI(title="InboxZen API")

# Use /api as the global prefix for all routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(email_router, prefix="/api/email", tags=["email"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/pipeline/run")
async def pipeline_run():
    try:
        messages = fetch_messages()
        return JSONResponse({"messages": messages})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
