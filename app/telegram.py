import logging
import re

import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.database import (
    get_todays_emails,
    search_emails,
)
from app.models import AIResponse
from app.huggingface import answer_email_question


logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Outbound: Send email summary to Telegram
# -------------------------------------------------------------------

def send_summary(ai_responses: list[AIResponse]):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning(
            "Telegram configuration missing, skipping message send."
        )
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{settings.telegram_bot_token}/sendMessage"
    )

    message = "📬 **Email Summary**\n\n"

    high_importance = []
    actions = []
    others = []

    for response in ai_responses:
        if response.importance.lower() == "high":
            high_importance.append(
                _format_summary_item(response)
            )
        elif response.action_required:
            actions.append(
                _format_summary_item(response)
            )
        else:
            others.append(
                _format_summary_item(response)
            )

    if high_importance:
        message += "🔴 **Important**\n"

        for item in high_importance:
            message += f"• {item}\n"

        message += "\n"

    if actions:
        message += "✅ **Action Required**\n"

        for item in actions:
            message += f"• {item}\n"

        message += "\n"

    if others:
        message += "📦 **Updates**\n"

        for item in others:
            message += f"• {item}\n"

    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        logger.info(
            "Telegram summary sent successfully."
        )

    except Exception as error:
        logger.error(
            f"Failed to send Telegram summary: {error}"
        )


def _format_summary_item(
    ai_response: AIResponse,
) -> str:

    if ai_response.email_url:
        return (
            f"{ai_response.summary} "
            f"([Open email]({ai_response.email_url}))"
        )

    return ai_response.summary


# -------------------------------------------------------------------
# Telegram Commands
# -------------------------------------------------------------------

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /start."""

    await update.message.reply_text(
        "👋 Hi! I'm your Email AI Assistant.\n\n"
        "I can help you manage and understand your emails.\n\n"
        "Use /help to see what I can do."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /help."""

    await update.message.reply_text(
        "🤖 Email AI Assistant\n\n"
        "Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show available commands\n"
        "/status - Check assistant status\n"
        "/emails - Check for new emails\n"
        "/summary - Get today's email summary\n\n"
        "You can also ask questions such as:\n"
        "\"When is the AI webinar?\""
    )


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /status."""

    await update.message.reply_text(
        "🟢 Email AI Assistant is running.\n\n"
        "Telegram listener: ✅\n"
        "Email processing: ✅\n"
        "AI analysis: ✅"
    )


async def emails_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /emails and trigger email processing."""

    await update.message.reply_text(
        "📬 Checking for new emails..."
    )

    try:
        # Import here to avoid circular imports.
        from app.main import process_emails

        results = process_emails()

        if results:
            await update.message.reply_text(
                f"✅ Processed {len(results)} new email(s)."
            )
        else:
            await update.message.reply_text(
                "📭 No new emails found."
            )

    except Exception:
        logger.exception(
            "Failed to process emails from Telegram command."
        )

        await update.message.reply_text(
            "❌ Failed to process emails.\n\n"
            "Check the Raspberry Pi logs for details."
        )


async def summary_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle /summary and show today's processed emails."""

    try:
        emails = get_todays_emails()

        if not emails:
            await update.message.reply_text(
                "📭 No emails processed today."
            )
            return

        message = "📊 **Today's Email Summary**\n\n"

        important = []
        actions = []
        updates = []

        for email in emails:

            item = f"• {email['summary']}"

            if email["importance"].lower() == "high":
                important.append(item)

            elif email["action_required"]:
                actions.append(item)

            else:
                updates.append(item)

        if important:
            message += "🔴 **Important**\n"

            for item in important:
                message += f"{item}\n"

            message += "\n"

        if actions:
            message += "✅ **Action Required**\n"

            for item in actions:
                message += f"{item}\n"

            message += "\n"

        if updates:
            message += "📦 **Updates**\n"

            for item in updates:
                message += f"{item}\n"

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    except Exception:
        logger.exception(
            "Failed to generate today's email summary."
        )

        await update.message.reply_text(
            "❌ Failed to generate today's summary."
        )


# -------------------------------------------------------------------
# Natural-language search
# -------------------------------------------------------------------

def extract_search_query(text: str) -> str:
    """
    Extract the useful topic from a natural-language question.

    Example:
        "When is the Generative AI Mastermind?"
        -> "the Generative AI Mastermind"
    """

    query = text.strip()

    patterns = [
        r"^\s*when\s+is\s+(.+?)\??\s*$",
        r"^\s*when\s+will\s+(.+?)\??\s*$",
        r"^\s*what\s+time\s+is\s+(.+?)\??\s*$",
        r"^\s*what\s+time\s+will\s+(.+?)\??\s*$",
        r"^\s*when\s+does\s+(.+?)\s+(?:start|begin)\??\s*$",
        r"^\s*date\s+of\s+(.+?)\??\s*$",
        r"^\s*schedule\s+for\s+(.+?)\??\s*$",
    ]

    for pattern in patterns:
        match = re.match(
            pattern,
            query,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1).strip(
                " \t\n?.!,"
            )

    return ""


async def handle_natural_language(
    update: Update,
    text: str,
):
    """Handle natural-language email questions."""

    search_query = extract_search_query(text)

    if not search_query:
        return False

    logger.info(
        "Natural-language email search: %s",
        search_query,
    )

    try:
        results = search_emails(
            search_query,
            limit=10,
        )

        if not results:
            await update.message.reply_text(
                "🔎 I couldn't find an email matching:\n\n"
                f"**{search_query}**",
                parse_mode="Markdown",
            )

            return True

        answer = answer_email_question(
            question=text,
            emails=results,
        )

        await update.message.reply_text(answer)

        return True

    except Exception:
        logger.exception(
            "Failed to search emails."
        )

        await update.message.reply_text(
            "❌ I couldn't search your emails right now."
        )

        return True


# -------------------------------------------------------------------
# Normal Telegram Messages
# -------------------------------------------------------------------

async def handle_incoming_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Handle normal incoming Telegram messages."""

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    user = update.effective_user

    logger.info(
        "Telegram message received from %s: %s",
        user.username if user else "unknown",
        text,
    )

    # Try natural-language email search first.
    handled = await handle_natural_language(
        update,
        text,
    )

    if handled:
        return

    # Keep existing behavior for normal messages.
    await update.message.reply_text(
        f"📬 Got it!\n\nYou said: {text}"
    )


# -------------------------------------------------------------------
# Telegram Listener
# -------------------------------------------------------------------

def start_telegram_listener():
    """Start Telegram long polling."""

    if not settings.telegram_bot_token:
        raise ValueError(
            "Telegram bot token is missing in .env"
        )

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    application.add_handler(
        CommandHandler("emails", emails_command)
    )

    application.add_handler(
        CommandHandler("summary", summary_command)
    )

    # Normal text messages
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_incoming_message,
        )
    )

    logger.info(
        "Telegram listener started "
        "(long polling, 30s timeout)."
    )

    application.run_polling(
        poll_interval=0,
        timeout=30,
        drop_pending_updates=False,
    )