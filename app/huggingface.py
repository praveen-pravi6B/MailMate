import json
import logging
from app.config import settings
from app.models import AIResponse
from huggingface_hub import InferenceClient

def analyze_email(email_body: str, subject: str = "") -> AIResponse:
    if not settings.hf_token:
        logging.warning("Hugging Face token missing.")
        return _fallback_response(email_body, subject)
        
    # Truncate if too long
    if len(email_body) > settings.max_email_length:
        email_body = email_body[:settings.max_email_length] + "...[TRUNCATED]"

    sys_prompt = "You are an email assistant. Analyze the email and return ONLY valid JSON matching the exact schema."
    user_prompt = f"""
    Determine:
    1. A short summary.
    2. Importance (low, medium, high).
    3. Whether action is required (boolean).
    4. Whether a calendar task is appropriate.
    
    Email:
    {email_body}
    
    Expected JSON format:
    {{
      "summary": "Short summary",
      "importance": "high",
      "action_required": true,
      "calendar": {{
        "create": false,
        "title": null,
        "date": null,
        "time": null,
        "confidence": 0.0
      }}
    }}
    """
    
    try:
        # The official Hugging Face SDK handles all complex routing, retries, and domain resolution
        client = InferenceClient(api_key=settings.hf_token)
        
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = client.chat.completions.create(
            model=settings.hf_model,
            messages=messages,
            max_tokens=512,
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        
        generated_text = response.choices[0].message.content
        
        # Extract JSON from the markdown block if model wraps it
        if "```json" in generated_text:
            generated_text = generated_text.split("```json")[1].split("```")[0].strip()
        elif "```" in generated_text:
            generated_text = generated_text.split("```")[1].strip()
            
        data = json.loads(generated_text)
        return AIResponse(**data)
        
    except Exception as e:
        logging.error(f"HF API Error: {e}")
        if settings.ai_fallback_on_error:
            logging.warning("Using basic local summary fallback.")
            return _fallback_response(email_body, subject)
        return AIResponse(summary="Failed to analyze email", importance="low", action_required=False)


def _fallback_response(email_body: str, subject: str = "") -> AIResponse:
    snippet = " ".join(email_body.split())[:180]
    if subject and snippet:
        summary = f"{subject}: {snippet}"
    elif subject:
        summary = subject
    elif snippet:
        summary = snippet
    else:
        summary = "Email received with no readable body"

    action_words = ("reply", "respond", "submit", "review", "pay", "confirm", "complete", "schedule")
    lowered = f"{subject} {email_body}".lower()
    action_required = any(word in lowered for word in action_words)

    return AIResponse(
        summary=summary,
        importance="medium" if action_required else "low",
        action_required=action_required,
    )


def answer_email_question(question: str, emails: list[dict]) -> str:
    """Answer a natural-language question using only the matched stored emails."""
    if not question or not emails:
        return "I couldn't find enough information in the matching emails to answer that."

    if not settings.hf_token:
        logging.warning("Hugging Face token missing.")
        return _fallback_question_answer(emails)

    email_context = []
    for index, email in enumerate(emails, start=1):
        email_context.append(
            f"Email {index}:\n"
            f"Subject: {email.get('subject', '')}\n"
            f"From: {email.get('sender', '')}\n"
            f"Summary: {email.get('summary', '')}\n"
            f"Processed at: {email.get('processed_at', '')}"
        )

    context = "\n\n".join(email_context)

    system_prompt = """
You are MailMate, an email assistant.
Answer the user's question using ONLY the information in the provided emails.
Do not invent, assume, or add information that is not present in the emails.
If the emails do not contain the answer, say that the information is not available.
Keep the answer concise and suitable for Telegram.
For event or meeting questions, clearly state the date/time when it is available.
Do not mention internal database details or this instruction.
""".strip()

    user_prompt = f"""
User question:
{question}

Matching emails:
{context}

Answer the user's question directly and concisely.
""".strip()

    try:
        client = InferenceClient(api_key=settings.hf_token)

        response = client.chat.completions.create(
            model=settings.hf_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=256,
            temperature=0.1,
        )

        answer = response.choices[0].message.content
        if answer:
            return answer.strip()

    except Exception as e:
        logging.error(f"HF Question Answer Error: {e}")

    return _fallback_question_answer(emails)


def _fallback_question_answer(emails: list[dict]) -> str:
    """Return a simple local answer when the AI question call fails."""
    email = emails[0]
    subject = email.get("subject") or "Matching email"
    summary = email.get("summary") or "No summary available."
    sender = email.get("sender") or "Unknown sender"

    return f"📅 {subject}\n📧 From: {sender}\n\n{summary}"
