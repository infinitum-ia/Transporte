"""
Application Settings

Configuration management using Pydantic Settings (12-Factor App pattern)
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application
    APP_NAME: str = "Transformas Medical Transport Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL"""
        if self.REDIS_URL:
            return self.REDIS_URL
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # OpenAI
    OPENAI_API_KEY: str = "sk-test-key"  # Default for testing
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 1000

    # Agent Configuration
    AGENT_NAME: str = "María"
    COMPANY_NAME: str = "Transformas"
    EPS_NAME: str = "Cosalud"
    # Agent backend: "mock" (no LLM) or "llm" (OpenAI via LangChain)
    AGENT_MODE: str = "mock"
    MAX_CONVERSATION_TURNS: int = 50
    SESSION_TTL_SECONDS: int = 3600

    # Outbound Calls (Excel Integration)
    EXCEL_PATH: Optional[str] = None  # Path to Excel/CSV file for outbound calls
    EXCEL_BACKUP_FOLDER: Optional[str] = None  # Path to backup folder

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


# Singleton instance
settings = Settings()
