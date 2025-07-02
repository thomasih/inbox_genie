from fastapi import FastAPI
from .auth import router as auth_router
from .email_client import router as email_router, fetch_messages
from fastapi.responses import JSONResponse

app = FastAPI(title="InboxZen API")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(email_router, prefix="/email", tags=["email"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/pipeline/run")
async def pipeline_run():
    try:
        messages = fetch_messages()
        return JSONResponse({"messages": messages})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
