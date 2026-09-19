import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    
    hf_token: str = ""
    hf_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    calendar_id: str = "primary"
    min_ai_confidence: float = 0.85
    max_email_length: int = 10000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
