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
