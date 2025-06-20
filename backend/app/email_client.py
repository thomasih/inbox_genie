from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import requests
from .auth import token_cache, token_cache_lock
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
async def run_cleanse():
    try:
        messages = fetch_messages()
        return JSONResponse({"messages": messages})
    except Exception as e:
        logging.error(f"/run-cleanse error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
