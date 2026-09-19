import time
import logging
from app.config import settings
from app.database import init_db, is_email_processed, mark_email_processed
from app.email_client import fetch_new_emails
from app.huggingface import analyze_email
from app.telegram import send_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_emails():
    logging.info("Starting Email AI Assistant run...")
    
    # 1. Initialize DB
    init_db()
    
    # 2. Fetch Emails
    emails = fetch_new_emails()
    
    if not emails:
        logging.info("No new emails found.")
        return

    summary_items = []
    
    for email in emails:
        if is_email_processed(email['id']):
            continue
            
        logging.info(f"Processing email: {email['subject']}")
        
        # 3. Analyze with Hugging Face
        ai_response = analyze_email(email['body'], email['subject'])
        
        # Check if HF failed
        if ai_response.summary in ["Failed to analyze email", "HF Token Missing"]:
            logging.warning(f"Skipping marking {email['subject']} as processed due to HF error.")
            continue
        
        # 4. Mark processed
        mark_email_processed(
            email['id'], 
            email['sender'], 
            email['subject'], 
            ai_response.summary, 
            ai_response.importance, 
            ai_response.action_required
        )
        
        # 5. Add to telegram summary queue
        summary_items.append(ai_response)
        
    # 6. Send Telegram Summary
    if summary_items:
        send_summary(summary_items)
        
    logging.info("Run completed successfully.")

if __name__ == "__main__":
    process_emails()
