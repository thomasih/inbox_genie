from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import msal
import os
from dotenv import load_dotenv
import threading

router = APIRouter()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/auth/callback"
SCOPE = ["User.Read", "Mail.ReadWrite"]

# In-memory token cache (thread-safe)
token_cache = {}
token_cache_lock = threading.Lock()

@router.get("/login")
async def login(request: Request):
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    redirect_uri = str(request.base_url)[:-1] + REDIRECT_PATH
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=redirect_uri,
        response_mode="query"
    )
    return RedirectResponse(auth_url)

@router.get("/callback")
async def callback(request: Request, code: str):
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    redirect_uri = f"http://localhost:8000{REDIRECT_PATH}"
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=redirect_uri
    )
    if "access_token" in result:
        # Get user info
        import requests
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        user_resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        user_email = user_resp.json().get("mail") or user_resp.json().get("userPrincipalName")
        # Store tokens in memory (keyed by user email)
        with token_cache_lock:
            token_cache[user_email] = result
        return JSONResponse({"email": user_email, "access_token": result["access_token"]})
    else:
        return JSONResponse({"error": result.get("error_description", "Unknown error")}, status_code=400)
