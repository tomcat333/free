from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Path("./data")
    collect_interval_seconds: int = 900
    enrich_top_n: int = 12
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    github_token: str = ""
    dispatch_webhook_url: str = ""
    dispatch_token: str = ""
    host: str = "0.0.0.0"
    port: int = 8787
    embed_worker: bool = False
    user_agent: str = "FrontierRadar/0.1 (+https://github.com/tomcat333/free)"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "frontier.db"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())


settings = Settings()
