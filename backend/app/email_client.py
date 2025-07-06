import sys
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests
from .db import SessionLocal
from .models_token import Token
from sqlalchemy.orm import Session
import logging
from pydantic import BaseModel
from bs4 import BeautifulSoup
import re
from .llm_categorizer import LLMEmailCategorizer
from datetime import datetime
from .models import EmailActionLog
import uuid
from sqlalchemy import update as sqlalchemy_update

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

# Function to GET /me/mailFolders/inbox/messages?$top=50
# Only fetch emails from the Inbox
def fetch_messages(user_email, num_emails=50):
    access_token = get_access_token(user_email)
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top={num_emails}&$select=id,subject,bodyPreview,body,from"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch messages: status={resp.status_code}, text={resp.text}")
        raise Exception(f"Error fetching messages: status={resp.status_code}, text={resp.text}")
    logger.info(f"Fetched {len(resp.json().get('value', []))} messages from Graph API (Inbox only).")
    return resp.json().get("value", [])

class RunCleanseRequest(BaseModel):
    user_email: str
    dry_run: bool = True
    num_emails: int = 50

# Aggressive plain-text cleaner for email snippets
def clean_snippet(text):
    import re
    # Remove invisible/zero-width chars, soft hyphens, etc
    text = re.sub(r"[\u200B-\u200D\uFEFF\u00AD]", "", text)
    # Remove all markdown tables (lines with pipes or table headers)
    text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|.*$", "", text, flags=re.MULTILINE)
    # Remove any line with 2+ pipes (likely table row)
    text = re.sub(r"^.*\|.*\|.*$", "", text, flags=re.MULTILINE)
    # Remove markdown table headers (---|---)
    text = re.sub(r"^\s*-{2,}\s*\|.*$", "", text, flags=re.MULTILINE)
    # Remove markdown images and links (including alt text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown formatting: headers, bold, italics, blockquotes, code, hr
    text = re.sub(r"^#+\\s*", "", text, flags=re.MULTILINE)  # headers
    text = re.sub(r"[*_~`]+", "", text)  # bold/italic/strike/code
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)  # blockquotes
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)  # hr
    # Remove repeated dashes, underscores, asterisks
    text = re.sub(r"[-_*]{3,}", "", text)
    # Remove lines that are just numbers, symbols, or whitespace
    text = re.sub(r"^\s*[-–—•\d\s]+\s*$", "", text, flags=re.MULTILINE)
    # Remove common footer/unsubscribe/legal lines
    text = re.sub(r"(?i)unsubscribe|privacy policy|view online|copyright|all rights reserved|follow us|contact us|terms of use|update your details|sent to|click here|edit your profile|faq|help centre|visit help centre|our help centre", "", text)
    # Remove leftover empty lines and normalize whitespace
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    # Split into paragraphs (by double newlines or single newlines)
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\n", text) if len(p.strip()) > 30]
    for p in paragraphs:
        # Skip if looks like a legal/footer line
        if not re.search(r"unsubscribe|privacy|copyright|all rights reserved|click here|edit your profile|faq|help centre", p, re.I):
            # Return first 300 chars of first good paragraph
            return p[:300]
    # Fallback: first non-empty line
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 30:
            return line[:300]
    return '[No preview available]'

def extract_main_text_from_html(html):
    """
    Aggressively extract only the main, human-readable content from HTML emails.
    Removes tables, images, nav, footer, header, and common boilerplate.
    Returns a single plain-text string.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Remove all tables, nav, footer, header, aside, form, script, style, img, svg, and their content
    for tag in soup.find_all(['table', 'nav', 'footer', 'header', 'aside', 'form', 'script', 'style', 'img', 'svg']):
        tag.decompose()
    # Remove elements with class or id indicating ads, banners, social, copyright, etc
    for tag in soup.find_all(attrs={"class": re.compile(r"(footer|header|nav|social|banner|ads|copyright|unsubscribe|promo|legal|disclaimer)", re.I)}):
        tag.decompose()
    for tag in soup.find_all(attrs={"id": re.compile(r"(footer|header|nav|social|banner|ads|copyright|unsubscribe|promo|legal|disclaimer)", re.I)}):
        tag.decompose()
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, type(soup.Comment))):
        comment.extract()
    # Get all visible text from <p>, <div>, <span>, and direct text in <body>
    body = soup.body if soup.body else soup
    texts = []
    for tag in body.find_all(['p', 'div', 'span'], recursive=True):
        t = tag.get_text(separator=' ', strip=True)
        if t and len(t) > 30:
            texts.append(t)
    # If nothing found, fallback to all visible text in body
    if not texts:
        texts = [body.get_text(separator=' ', strip=True)]
    # Remove lines that are just numbers, symbols, or whitespace
    cleaned = []
    for t in texts:
        t = re.sub(r"^\s*[-–—•\d\s]+\s*$", "", t, flags=re.MULTILINE)
        if len(t.strip()) > 30:
            cleaned.append(t.strip())
    # Join and return the first 500 chars
    result = ' '.join(cleaned)
    result = re.sub(r'\s+', ' ', result).strip()
    return result[:500] if result else ''

def extract_main_text(body):
    """
    Given a message body dict, extract the main, human-readable content for clustering/snippet.
    """
    content = body.get("content", "")
    ctype = body.get("contentType", "")
    if ctype == "text":
        return content.strip()
    elif ctype == "html":
        return extract_main_text_from_html(content)
    return ""

@router.post("/emails/raw")
async def get_raw_emails(request: RunCleanseRequest):
    try:
        user_email = request.user_email
        num_emails = getattr(request, 'num_emails', 50)
        logger.info("/emails/raw endpoint called. user_email=%s num_emails=%d", user_email, num_emails)
        messages = fetch_messages(user_email, num_emails=num_emails)
        emails = []
        for m in messages:
            email_id = m.get("id")
            subject = m.get("subject", "")
            body = m.get("body", {})
            sender = m.get("from", {})
            sender_email = sender.get("emailAddress", {}).get("address", "")
            sender_name = sender.get("emailAddress", {}).get("name", "")
            sender_obj = {"name": sender_name, "email": sender_email}
            main_text = extract_main_text(body)
            if not main_text or len(main_text) < 30:
                main_text = m.get("bodyPreview", "")
            main_text = BeautifulSoup(main_text, 'html.parser').get_text(separator=' ', strip=True)
            main_text = ' '.join(main_text.split())
            snippet = clean_snippet(main_text)
            emails.append({
                "id": email_id,
                "subject": subject,
                "snippet": snippet,
                "sender": sender_obj
            })
        logger.info(f"Returning {len(emails)} emails (raw, no LLM or grouping).")
        return JSONResponse({"emails": emails})
    except Exception as e:
        logger.exception("/emails/raw error")
        return JSONResponse({"error": str(e)}, status_code=500)

# Move an email to a folder using Microsoft Graph API
def move_email(user_email, email_id, dest_folder_id):
    access_token = get_access_token(user_email)
    url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}/move"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"destinationId": dest_folder_id}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code != 201:
        logger.error(f"Failed to move email {email_id} to {dest_folder_id}: {resp.status_code} {resp.text}")
        raise Exception(f"Error moving email: {resp.status_code} {resp.text}")
    logger.info(f"Moved email {email_id} to folder {dest_folder_id}")
    return resp.json()

# Get all mail folders (name -> id), recursively
# If multiple folders have the same name, the first found is used

def get_folder_map(user_email):
    access_token = get_access_token(user_email)
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://graph.microsoft.com/v1.0/me/mailFolders?$top=100"
    folder_name_to_id = {}
    queue = [url]
    while queue:
        current_url = queue.pop(0)
        resp = requests.get(current_url, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch folders: {resp.status_code} {resp.text}")
            raise Exception(f"Error fetching folders: {resp.status_code} {resp.text}")
        folders = resp.json().get("value", [])
        for f in folders:
            name = f.get("displayName")
            fid = f.get("id")
            if name and fid and name not in folder_name_to_id:
                folder_name_to_id[name] = fid
            # If folder has child folders, queue them for fetching
            if f.get("childFolderCount", 0) > 0:
                child_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{fid}/childFolders?$top=100"
                queue.append(child_url)
    return folder_name_to_id

def create_folder_if_missing(user_email, folder_name, folder_name_to_id):
    if folder_name in folder_name_to_id:
        return folder_name_to_id[folder_name]
    access_token = get_access_token(user_email)
    url = "https://graph.microsoft.com/v1.0/me/mailFolders"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"displayName": folder_name}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code in (200, 201):
        folder_id = resp.json().get("id")
        folder_name_to_id[folder_name] = folder_id
        logger.info(f"Created folder '{folder_name}' for user {user_email}")
        return folder_id
    elif resp.status_code == 409:
        # Folder already exists, refresh folder map and return the ID
        logger.warning(f"Folder '{folder_name}' already exists. Refreshing folder map.")
        folder_name_to_id.clear()
        folder_name_to_id.update(get_folder_map(user_email))
        if folder_name in folder_name_to_id:
            return folder_name_to_id[folder_name]
        else:
            logger.error(f"Folder '{folder_name}' exists but could not find its ID after refresh.")
            raise Exception(f"Folder '{folder_name}' exists but could not find its ID after refresh.")
    else:
        logger.error(f"Failed to create folder '{folder_name}': {resp.status_code} {resp.text}")
        raise Exception(f"Error creating folder: {resp.status_code} {resp.text}")

@router.post("/emails/categorize")
async def categorize_emails(request: RunCleanseRequest):
    try:
        user_email = request.user_email
        num_emails = getattr(request, 'num_emails', 50)
        logger.info("/emails/categorize endpoint called. user_email=%s num_emails=%d", user_email, num_emails)
        messages = fetch_messages(user_email, num_emails=num_emails)
        emails = []
        for m in messages:
            email_id = m.get("id")
            subject = m.get("subject", "")
            body = m.get("body", {})
            sender = m.get("from", {})
            sender_email = sender.get("emailAddress", {}).get("address", "")
            sender_name = sender.get("emailAddress", {}).get("name", "")
            sender_obj = {"name": sender_name, "email": sender_email}
            main_text = extract_main_text(body)
            if not main_text or len(main_text) < 30:
                main_text = m.get("bodyPreview", "")
            main_text = BeautifulSoup(main_text, 'html.parser').get_text(separator=' ', strip=True)
            main_text = ' '.join(main_text.split())
            snippet = clean_snippet(main_text)
            emails.append({
                "id": email_id,
                "subject": subject,
                "snippet": snippet,
                "sender": sender_obj
            })
        logger.info(f"Fetched {len(emails)} emails for categorization.")
        categorizer = LLMEmailCategorizer()
        folder_map = categorizer.categorize_emails(emails)
        if "error" in folder_map:
            return JSONResponse({"error": folder_map["error"]}, status_code=500)
        folder_name_to_id = get_folder_map(user_email)
        moved_count = 0
        batch_id = str(uuid.uuid4())
        db: Session = SessionLocal()
        try:
            for folder, email_list in folder_map.items():
                dest_folder_id = create_folder_if_missing(user_email, folder, folder_name_to_id)
                for email_id in email_list:
                    access_token = get_access_token(user_email)
                    msg_url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}?$select=parentFolderId"
                    msg_resp = requests.get(msg_url, headers={"Authorization": f"Bearer {access_token}"})
                    if msg_resp.status_code != 200:
                        logger.warning(f"Could not get parent folder for email {email_id}, skipping undo tracking.")
                        continue
                    orig_folder_id = msg_resp.json().get("parentFolderId")
                    try:
                        move_resp = move_email(user_email, email_id, dest_folder_id)
                        new_id = move_resp.get("id", email_id)
                        log_entry = EmailActionLog(
                            user_email=user_email,
                            email_id=new_id,  # Store new ID for undo
                            from_folder=orig_folder_id,
                            to_folder=dest_folder_id,
                            batch_id=batch_id
                        )
                        db.add(log_entry)
                        moved_count += 1
                    except Exception as e:
                        logger.warning(f"Move failed for email {email_id}: {e}")
            db.commit()
        finally:
            db.close()
        logger.info(f"Moved {moved_count} emails into {len(folder_map)} categories for user {user_email}.")
        return JSONResponse({
            "message": f"Sorted {moved_count} emails into {len(folder_map)} categories! Please check your inbox."
        })
    except Exception as e:
        logger.exception("/emails/categorize error")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/emails/undo")
async def undo_last_sort(request: RunCleanseRequest):
    user_email = request.user_email
    db: Session = SessionLocal()
    try:
        latest_batch = db.query(EmailActionLog.batch_id).filter(
            EmailActionLog.user_email == user_email,
            EmailActionLog.undone == False
        ).order_by(EmailActionLog.timestamp.desc()).first()
        if not latest_batch:
            return JSONResponse({"message": "Nothing to undo."})
        batch_id = latest_batch[0]
        actions = db.query(EmailActionLog).filter(
            EmailActionLog.user_email == user_email,
            EmailActionLog.batch_id == batch_id,
            EmailActionLog.undone == False
        ).all()
        undo_count = 0
        # Collect all destination folders from this batch
        dest_folder_ids = set(a.to_folder for a in actions)
        # Always move emails back to Inbox (since we only ever fetch from Inbox)
        folder_name_to_id = get_folder_map(user_email)
        inbox_id = folder_name_to_id.get("Inbox")
        if not inbox_id:
            logger.error("Inbox folder not found for user %s", user_email)
            return JSONResponse({"error": "Inbox folder not found."}, status_code=500)
        for action in actions:
            try:
                move_resp = move_email(user_email, action.email_id, inbox_id)
                new_id = move_resp.get("id", action.email_id)
                # Update the log entry with the new ID for future undos
                action.email_id = new_id
                action.undone = True
                undo_count += 1
            except Exception as e:
                logger.warning(f"Undo move failed for email {action.email_id}: {e}")
        db.commit()

        # After undo, delete any empty folders created by the app
        access_token = get_access_token(user_email)
        headers = {"Authorization": f"Bearer {access_token}"}
        for folder_id in dest_folder_ids:
            # Check if folder is empty
            url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages?$top=1"
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                messages = resp.json().get("value", [])
                if not messages:
                    # Folder is empty, delete it (soft delete)
                    del_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}"
                    del_resp = requests.delete(del_url, headers=headers)
                    if del_resp.status_code in (204, 202):
                        logger.info(f"Deleted empty folder {folder_id} after undo.")
                        # Now, try to permanently delete from Deleted Items
                        # 1. List child folders of Deleted Items
                        deleted_items_url = "https://graph.microsoft.com/v1.0/me/mailFolders('deleteditems')/childFolders?$top=100"
                        child_resp = requests.get(deleted_items_url, headers=headers)
                        if child_resp.status_code == 200:
                            child_folders = child_resp.json().get("value", [])
                            for f in child_folders:
                                if f.get("id") == folder_id:
                                    # 2. Hard delete (purge) the folder
                                    purge_url = f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}"
                                    purge_resp = requests.delete(purge_url, headers=headers)
                                    if purge_resp.status_code in (204, 202):
                                        logger.info(f"Permanently deleted folder {folder_id} from Deleted Items.")
                                    else:
                                        logger.warning(f"Failed to permanently delete folder {folder_id}: {purge_resp.status_code} {purge_resp.text}")
                        else:
                            logger.warning(f"Failed to list Deleted Items child folders: {child_resp.status_code} {child_resp.text}")
                    else:
                        logger.warning(f"Failed to delete folder {folder_id}: {del_resp.status_code} {del_resp.text}")
            else:
                logger.warning(f"Failed to check messages in folder {folder_id}: {resp.status_code} {resp.text}")

        return JSONResponse({"message": f"Undo complete. Restored {undo_count} emails to Inbox."})
    finally:
        db.close()

class StoreTokenRequest(BaseModel):
    user_email: str
    access_token: str
    refresh_token: str = None
    expires_at: str = None

@router.post("/store-token")
async def store_token(request: StoreTokenRequest):
    db: Session = SessionLocal()
    token = db.query(Token).filter(Token.user_email == request.user_email).first()
    if token:
        token.access_token = request.access_token
        token.refresh_token = request.refresh_token
        token.expires_at = request.expires_at
    else:
        token = Token(user_email=request.user_email, access_token=request.access_token, refresh_token=request.refresh_token, expires_at=request.expires_at)
        db.add(token)
    db.commit()
    db.close()
    logger.info(f"Token stored for user {request.user_email}")
    return {"status": "success"}

def condense_email(email):
    email_id = email.get("id")
    subject = email.get("subject", "")
    sender = email.get("from", {})
    sender_email = sender.get("emailAddress", {}).get("address", "")
    sender_name = sender.get("emailAddress", {}).get("name", "")
    sender_obj = {"name": sender_name, "email": sender_email}
    snippet = email.get("bodyPreview", "")
    return {
        "id": email_id,
        "subject": subject,
        "snippet": snippet,
        "sender": sender_obj
    }

def fetch_emails(user_email, raise_on_error=False):
    # Simulate error for test
    if raise_on_error:
        raise Exception("Simulated fetch error")
    return [
        {
            "id": "id1",
            "subject": "Test Subject",
            "from": {"emailAddress": {"name": "Test Sender", "address": "test@example.com"}},
            "bodyPreview": "Test body preview"
        }
    ]
