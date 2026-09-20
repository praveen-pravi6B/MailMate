# Copilot instructions for Email AI Assistant

## Repository context
This project is a Python-based email automation service for Gmail and Telegram. It periodically checks for unread Gmail messages, sends them to Hugging Face for analysis, and posts a digest to Telegram.

## Goals
- Preserve the existing Raspberry Pi / Linux-friendly runtime behavior.
- Keep logic simple, explicit, and easy to debug.
- Prefer configuration via environment variables and `.env` over hardcoded secrets.

## Workflow
- Use the existing project structure under `app/`.
- Keep imports, config access, and logging patterns consistent with the current code.
- Prefer surgical fixes over broad refactors.
- If a change affects runtime behavior, validate it with a focused Python compile check or targeted unit test.

## Required checks
Run this before finishing work:
```bash
python -m compileall app
```

## Security and data handling
- Never add secrets to repository files.
- Keep OAuth credentials and API tokens in `.env` only.
- Do not log full email bodies or sensitive user data unless explicitly required for a debugging task.

## Key files
- `app/main.py`
- `app/config.py`
- `app/email_client.py`
- `app/huggingface.py`
- `app/telegram.py`
- `README.md`
