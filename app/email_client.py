import os
import base64
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import settings
import logging

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    if not settings.gmail_refresh_token:
        raise ValueError("Gmail refresh token is missing in .env")

    creds = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        scopes=SCOPES
    )
    return build('gmail', 'v1', credentials=creds)

def clean_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    return text

def parse_parts(service, message_id, parts):
    text_content = ""
    if not parts:
        return text_content
        
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            data = part.get('body', {}).get('data')
            if data:
                text_content += base64.urlsafe_b64decode(data).decode('utf-8')
        elif part.get('mimeType') == 'text/html':
            data = part.get('body', {}).get('data')
            if data:
                html_data = base64.urlsafe_b64decode(data).decode('utf-8')
                text_content += clean_html(html_data)
        elif 'parts' in part:
            text_content += parse_parts(service, message_id, part['parts'])
            
    return text_content

def fetch_new_emails() -> list[dict]:
    try:
        service = get_gmail_service()
        # Fetch up to 10 unread emails
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=10).execute()
        messages = results.get('messages', [])
        
        parsed_emails = []
        
        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            body = ""
            if 'parts' in payload:
                body = parse_parts(service, msg_id, payload['parts'])
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    content = base64.urlsafe_b64decode(data).decode('utf-8')
                    if payload.get('mimeType') == 'text/html':
                        body = clean_html(content)
                    else:
                        body = content
                        
            parsed_emails.append({
                'id': msg_id,
                'sender': sender,
                'subject': subject,
                'body': body
            })
            
        return parsed_emails
    except Exception as e:
        logging.error(f"Error fetching emails: {e}")
        return []
