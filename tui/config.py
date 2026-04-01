from pydantic_settings import BaseSettings, SettingsConfigDict


class TUISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TUI_",
        extra="ignore",
    )

    api_base_url: str = "http://localhost:8000"
    embedded_mode: bool = False
    default_user: str = ""
    default_password: str = ""


settings = TUISettings()
