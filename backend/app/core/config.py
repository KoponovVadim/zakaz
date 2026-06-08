from functools import cached_property

from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://zakaz:zakaz@postgres:5432/zakaz"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    fernet_key: str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    connector_version: str = "1.0.0"
    backend_cors_origins: str = "http://localhost,http://127.0.0.1"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin12345"

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]

    @cached_property
    def effective_fernet_key(self) -> str:
        if self.fernet_key:
            return self.fernet_key
        return Fernet.generate_key().decode()


settings = Settings()
