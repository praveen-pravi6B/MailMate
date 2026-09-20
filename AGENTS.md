# AGENTS.md

This repository contains the Email AI Assistant, a Python service that checks Gmail for unread messages, uses Hugging Face to summarize them, and sends a Telegram notification for actionable items.

## Project overview
- Runtime: Python 3
- Main entry point: `python -m app.main`
- Configuration: environment variables in `.env` loaded by `app.config.Settings`
- Dependencies: see `requirements.txt`
- Service scheduling: `email-assistant.service` and `email-assistant.timer`

## Working conventions
- Keep changes focused and minimal.
- Prefer preserving the existing architecture and naming patterns in `app/`.
- Do not commit secrets. Keep Gmail, Hugging Face, and Telegram credentials in `.env` and never in tracked files.
- If behavior changes, update the relevant docs in `README.md`.

## Local setup
1. Create and activate the virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the example config and fill in real values:
   ```bash
   cp config/settings.example.env .env
   ```
3. Run the app:
   ```bash
   python -m app.main
   ```

## Validation
Before considering a change complete, run the most relevant check:
```bash
python -m compileall app
```
If a focused pytest check exists for the changed behavior, run it too.

## Important files
- `app/main.py`: main orchestration flow
- `app/email_client.py`: Gmail fetching logic
- `app/huggingface.py`: AI analysis and fallback behavior
- `app/telegram.py`: Telegram notification sender
- `app/config.py`: environment-driven settings
- `config/settings.example.env`: template for required configuration

## Notes
- The app expects `.env` values for `gmail_client_id`, `gmail_client_secret`, `gmail_refresh_token`, `hf_token`, and `telegram_bot_token`/`telegram_chat_id`.
- If Hugging Face fails, the app logs the error and may continue with local fallback summaries depending on configuration.
- The service is designed to run as a scheduled systemd job on Raspberry Pi / Linux hosts.
