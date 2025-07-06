from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import msal
import os
from dotenv import load_dotenv
import logging
from .db import SessionLocal
from .models_token import Token
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = "/api/auth/callback"
SCOPE = ["User.Read", "Mail.ReadWrite"]

missing_vars = []
if not CLIENT_ID:
    missing_vars.append("AZURE_CLIENT_ID")
if not CLIENT_SECRET:
    missing_vars.append("AZURE_CLIENT_SECRET")
if not TENANT_ID:
    missing_vars.append("AZURE_TENANT_ID")
if missing_vars:
    raise RuntimeError(f"Missing required environment variables for auth: {', '.join(missing_vars)}. Check your .env file or environment.")

logger = logging.getLogger("inboxgenie.auth")
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

@router.get("/login")
async def login(request: Request):
    logger.info("Login requested from %s", request.client.host)
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
    try:
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
            import requests
            headers = {"Authorization": f"Bearer {result['access_token']}"}
            user_resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            user_email = user_resp.json().get("mail") or user_resp.json().get("userPrincipalName")
            # Store tokens in DB
            db: Session = SessionLocal()
            token = db.query(Token).filter(Token.user_email == user_email).first()
            if token:
                token.access_token = result["access_token"]
                token.refresh_token = result.get("refresh_token")
                token.expires_at = None  # You can parse expires_in if needed
            else:
                token = Token(user_email=user_email, access_token=result["access_token"], refresh_token=result.get("refresh_token"), expires_at=None)
                db.add(token)
            db.commit()
            db.close()
            logger.info(f"User {user_email} authenticated and token stored in DB.")
            return JSONResponse({"email": user_email, "access_token": result["access_token"]})
        else:
            logger.error(f"Auth callback error: {result.get('error_description', 'Unknown error')}")
            return JSONResponse({"error": result.get("error_description", "Unknown error")}, status_code=400)
    except Exception as e:
        logger.exception("Exception in auth callback")
        return JSONResponse({"error": str(e)}, status_code=500)

def store_token(session: Session, user_email: str, access_token: str, refresh_token: str, expires_at):
    token = session.query(Token).filter(Token.user_email == user_email).first()
    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
    else:
        token = Token(user_email=user_email, access_token=access_token, refresh_token=refresh_token, expires_at=expires_at)
        session.add(token)
    session.commit()

def get_token(session: Session, user_email: str):
    return session.query(Token).filter(Token.user_email == user_email).first()
