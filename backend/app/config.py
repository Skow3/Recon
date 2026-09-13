from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

# Base directory for the backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    PROJECT_NAME: str = "RECON"
    TAGLINE: str = "Reconcile reality before taking action."
    DEBUG: bool = True
    
    # AI Settings
    OPENAI_API_KEY: str = Field(default="", validation_alias=AliasChoices("OPENAI_API_KEY"))
    OPENAI_MODEL: str = Field(default="gpt-5-nano", validation_alias=AliasChoices("OPENAI_MODEL"))
    
    # Stripe Settings (TEST MODE ONLY)
    STRIPE_SECRET_KEY: str = Field(default="", validation_alias=AliasChoices("STRIPE_SECRET_KEY", "STRIPESECRET_KEY"))
    
    # Slack Settings
    SLACK_BOT_TOKEN: str = Field(default="", validation_alias=AliasChoices("SLACK_BOT_TOKEN"))
    SLACK_CHANNEL: str = Field(default="billing", validation_alias=AliasChoices("SLACK_CHANNEL"))
    
    # Gmail Settings
    GMAIL_CREDENTIALS_PATH: str = Field(default="./credentials.json", validation_alias=AliasChoices("GMAIL_CREDENTIALS_PATH"))
    GMAIL_TOKEN_PATH: str = Field(default="./token.json", validation_alias=AliasChoices("GMAIL_TOKEN_PATH"))
    
    # Mode Settings
    MOCK_MODE: bool = Field(default=True, validation_alias=AliasChoices("MOCK_MODE"))
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./recon.db", validation_alias=AliasChoices("DATABASE_URL"))

    @property
    def is_stripe_test_mode(self) -> bool:
        if self.MOCK_MODE:
            return True
        key = self.STRIPE_SECRET_KEY.strip()
        return key.startswith("sk_test_")

settings = Settings()
