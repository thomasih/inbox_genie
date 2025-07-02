from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
import requests
from .auth import token_cache, token_cache_lock
from .embeddings import LocalEmbedder, IEmbedder
from .clustering import cluster_embeddings, pick_representative
from .naming import LocalLLMFolderNamer, IFolderNamer
import logging

router = APIRouter()

# Helper: Get access token for a user (for demo, just pick first user in cache)
def get_access_token():
    with token_cache_lock:
        if not token_cache:
            raise Exception("No user authenticated.")
        # Pick first user (for demo)
        user_email, token_data = next(iter(token_cache.items()))
        access_token = token_data["access_token"]
        return access_token

# Function to GET /me/messages?$top=50
def fetch_messages():
    access_token = get_access_token()
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=50"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logging.error(f"Failed to fetch messages: status={resp.status_code}, text={resp.text}")
        raise Exception(f"Error fetching messages: status={resp.status_code}, text={resp.text}")
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
        logging.error(f"Failed to move message {message_id}: {resp.text}")
        raise Exception(f"Error moving message: {resp.text}")
    return resp.json()

@router.post("/run-cleanse")
async def run_cleanse(dry_run: bool = Query(True)):
    try:
        messages = fetch_messages()
        # Extract bodies, ids, and subjects for frontend display
        bodies = [m.get("body", {}).get("content", "") for m in messages]
        ids = [m.get("id") for m in messages]
        subjects = [m.get("subject", "") for m in messages]
        if not bodies:
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
        # If not dry_run, here is where you would move emails/create folders
        # (skipped for now)
        return JSONResponse({
            "folders": folder_names,
            "cluster_map": cluster_map
        })
    except Exception as e:
        logging.error(f"/run-cleanse error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
