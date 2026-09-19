import requests
from app.config import settings
from app.models import AIResponse
import logging

def send_summary(ai_responses: list[AIResponse]):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logging.warning("Telegram configuration missing, skipping message send.")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    # Format the message
    message = "📬 **Email Summary**\n\n"
    
    high_importance = []
    actions = []
    others = []
    
    for r in ai_responses:
        if r.importance.lower() == 'high':
            high_importance.append(_format_summary_item(r))
        elif r.action_required:
            actions.append(_format_summary_item(r))
        else:
            others.append(_format_summary_item(r))
            
    if high_importance:
        message += "🔴 **Important**\n"
        for h in high_importance:
            message += f"• {h}\n"
        message += "\n"
        
    if actions:
        message += "✅ **Action Required**\n"
        for a in actions:
            message += f"• {a}\n"
        message += "\n"
        
    if others:
        message += "📦 **Updates**\n"
        for o in others:
            message += f"• {o}\n"

    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info("Telegram summary sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send Telegram summary: {e}")


def _format_summary_item(ai_response: AIResponse) -> str:
    if ai_response.email_url:
        return f"{ai_response.summary} ([Open email]({ai_response.email_url}))"
    return ai_response.summary
