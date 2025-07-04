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
    # Request bodyPreview (plain text), subject, id, and from (sender info)
    url = "https://graph.microsoft.com/v1.0/me/messages?$top=50&$select=id,subject,bodyPreview,body,from"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch messages: status={resp.status_code}, text={resp.text}")
        raise Exception(f"Error fetching messages: status={resp.status_code}, text={resp.text}")
    logger.info(f"Fetched {len(resp.json().get('value', []))} messages from Graph API.")
    return resp.json().get("value", [])

class RunCleanseRequest(BaseModel):
    user_email: str
    dry_run: bool = True

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
        logger.info("/emails/raw endpoint called. user_email=%s", user_email)
        messages = fetch_messages(user_email)
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
