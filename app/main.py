import logging

from app.database import (
    init_db,
    is_email_processed,
    mark_email_processed,
)
from app.email_client import fetch_new_emails
from app.huggingface import analyze_email
from app.telegram import (
    send_summary,
    start_telegram_listener,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def process_emails():
    """
    Fetch and process new emails.

    Returns:
        list: AI responses generated for newly processed emails.
    """

    logging.info("Starting Email AI Assistant run...")

    init_db()

    emails = fetch_new_emails()

    if not emails:
        logging.info("No new emails found.")
        return []

    summary_items = []

    for email in emails:

        if is_email_processed(email["id"]):
            logging.info(
                f"Skipping already processed email: "
                f"{email['subject']}"
            )
            continue

        logging.info(
            f"Processing email: {email['subject']}"
        )

        # Analyze email with AI
        ai_response = analyze_email(
            email["body"],
            email["subject"],
        )

        ai_response.email_url = email.get("url")

        # Don't mark email as processed if AI failed
        if ai_response.summary in [
            "Failed to analyze email",
            "HF Token Missing",
        ]:
            logging.warning(
                f"Skipping marking {email['subject']} "
                "as processed due to HF error."
            )
            continue

        # Save processed email
        mark_email_processed(
            email["id"],
            email["sender"],
            email["subject"],
            ai_response.summary,
            ai_response.importance,
            ai_response.action_required,
        )

        summary_items.append(ai_response)

    # Send Telegram summary
    if summary_items:
        send_summary(summary_items)
    else:
        logging.info(
            "No new emails were processed."
        )

    logging.info(
        "Email processing completed successfully."
    )

    return summary_items


if __name__ == "__main__":

    # Initialize database
    init_db()

    # Run email processing once when the application starts
    process_emails()

    # Start Telegram listener in the main thread
    start_telegram_listener()