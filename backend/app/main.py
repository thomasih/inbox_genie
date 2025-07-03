from fastapi import FastAPI
from .auth import router as auth_router
from .email_client import router as email_router, fetch_messages
from fastapi.responses import JSONResponse
from fastapi.requests import Request as FastAPIRequest
from fastapi.responses import JSONResponse as FastAPIJSONResponse
import logging

app = FastAPI(title="InboxZen API")

# Configure logger
logger = logging.getLogger("inboxgenie.main")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

# Use /api as the global prefix for all routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(email_router, prefix="/api/email", tags=["email"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/pipeline/run")
async def pipeline_run():
    try:
        logger.info("/api/pipeline/run endpoint called.")
        messages = fetch_messages()
        logger.info(f"Fetched {len(messages)} messages in pipeline run.")
        return JSONResponse({"messages": messages})
    except Exception as e:
        logger.exception("Error in /api/pipeline/run endpoint")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    logger.critical(f"Uncaught exception: {exc}", exc_info=True)
    return FastAPIJSONResponse(status_code=500, content={"error": str(exc)})
