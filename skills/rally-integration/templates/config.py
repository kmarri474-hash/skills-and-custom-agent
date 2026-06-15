# Rally service config (Pydantic Settings example).
# Adapt to your framework — the env var names and the two derived properties are what matter.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Rally Integration ---
    RALLY_BASE_URL: str = "https://rally1.rallydev.com/slm/webservice/v2.0"
    RALLY_AUTH_URL: str = "https://rally1.rallydev.com/login/oauth2/token"

    # OAuth2 client-credentials path
    RALLY_CLIENT_ID: str = ""
    RALLY_CLIENT_SECRET: str = ""

    # Static API key / bearer token (alternative to client_id/secret; takes precedence)
    RALLY_API_KEY: str = ""

    # Project scoping: NAME is auto-resolved to a ref; REF (raw URL) overrides NAME.
    RALLY_PROJECT_NAME: str = ""
    RALLY_PROJECT_REF: str = ""

    # Corporate TLS inspection sometimes requires disabling verification.
    RALLY_SSL_VERIFY: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def rally_enabled(self) -> bool:
        return bool(self.RALLY_BASE_URL and (self.RALLY_CLIENT_ID or self.RALLY_API_KEY))

    @property
    def rally_bearer_token(self) -> str:
        """Static token if configured; empty string means 'use OAuth2 flow'."""
        return self.RALLY_API_KEY


settings = Settings()
