from fastapi import FastAPI
from .auth import router as auth_router
from .email_client import router as email_router

app = FastAPI(title="InboxZen API")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(email_router, prefix="/email", tags=["email"])

@app.get("/health")
async def health():
    return {"status": "ok"}
