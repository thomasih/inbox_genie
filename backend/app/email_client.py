import sys
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
import requests
from .embeddings import LocalEmbedder, IEmbedder
from .clustering import cluster_embeddings, pick_representative
from .naming import LocalLLMFolderNamer, IFolderNamer
from .db import SessionLocal
from .models_token import Token
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("inboxgenie.email_client")
logger.info("email_client.py loaded and logger initialized.")

router = APIRouter()

# Helper: Get access token for a user (for demo, just pick first user in cache)
def get_access_token(user_email):
    db: Session = SessionLocal()
    token = db.query(Token).filter(Token.user_email == user_email).first()
    db.close()
    if not token or not token.access_token:
        logger.error(f"No token found in DB for user {user_email}")
        raise Exception("No user authenticated.")
    logger.info(f"Access token fetched from DB for user {user_email}")
    return token.access_token

# Function to GET /me/messages?$top=50
def fetch_messages(user_email):
    access_token = get_access_token(user_email)
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch messages: status={resp.status_code}, text={resp.text}")
        raise Exception(f"Error fetching messages: status={resp.status_code}, text={resp.text}")
    logger.info(f"Fetched {len(resp.json().get('value', []))} messages from Graph API.")
    return resp.json().get("value", [])

# Function to PATCH /me/messages/{id} to update parentFolderId
def move_message(message_id, new_folder_id):
    access_token = get_access_token()
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {"parentFolderId": new_folder_id}
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code not in (200, 202):
        logger.error(f"Failed to move message {message_id}: {resp.text}")
        raise Exception(f"Error moving message: {resp.text}")
    logger.info(f"Message {message_id} moved to folder {new_folder_id}")
    return resp.json()

class RunCleanseRequest(BaseModel):
    user_email: str
    dry_run: bool = True

@router.post("/run-cleanse")
async def run_cleanse(request: RunCleanseRequest):
    try:
        user_email = request.user_email
        dry_run = request.dry_run
        logger.info("/run-cleanse endpoint called. dry_run=%s user_email=%s", dry_run, user_email)
        messages = fetch_messages(user_email)
        # Extract bodies, ids, and subjects for frontend display
        bodies = [m.get("body", {}).get("content", "") for m in messages]
        ids = [m.get("id") for m in messages]
        subjects = [m.get("subject", "") for m in messages]
        if not bodies:
            logger.warning("No email bodies found for clustering.")
            return JSONResponse({"error": "No email bodies found."}, status_code=404)
        # Instantiate embedder and namer
        embedder: IEmbedder = LocalEmbedder()
        namer: IFolderNamer = LocalLLMFolderNamer()
        # Embed
        embeddings = embedder.embed(bodies)
        # Cluster
        n_clusters = min(5, len(bodies))
        labels = cluster_embeddings(embeddings, n_clusters)
        # Pick representatives
        reps = pick_representative(bodies, labels, samples_per_cluster=3)
        # Name clusters
        folder_names = {str(k): namer.name_folder(samples) for k, samples in reps.items()}
        # Prepare cluster map for frontend (include id, subject, body)
        cluster_map = {str(k): [] for k in reps}
        for idx, label in enumerate(labels):
            cluster_map[str(label)].append({
                "id": ids[idx],
                "subject": subjects[idx],
                "body": bodies[idx]
            })
        logger.info(f"Clustering complete. Returning {len(folder_names)} folders.")
        return JSONResponse({
            "folders": folder_names,
            "cluster_map": cluster_map
        })
    except Exception as e:
        logger.exception("/run-cleanse error")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/store-token")
async def store_token(user_email: str, access_token: str, refresh_token: str = None, expires_at: str = None):
    db: Session = SessionLocal()
    token = db.query(Token).filter(Token.user_email == user_email).first()
    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
    else:
        token = Token(user_email=user_email, access_token=access_token, refresh_token=refresh_token, expires_at=expires_at)
        db.add(token)
    db.commit()
    db.close()
    logger.info(f"Token stored for user {user_email}")
    return {"status": "success"}
