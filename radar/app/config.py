from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 始终从 radar/ 目录读 .env，不依赖你从哪个目录启动
RADAR_DIR = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = (
    RADAR_DIR / ".env",
    RADAR_DIR / ".env.txt",  # Windows 记事本另存为时容易多出 .txt
    RADAR_DIR.parent / ".env",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in ENV_CANDIDATES if True),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = RADAR_DIR / "data"
    collect_interval_seconds: int = 900
    # 0 = 默认不自动写介绍，只在你点按钮时才调用大模型（省 token）
    enrich_top_n: int = 0
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

    @field_validator(
        "openai_api_key",
        "openai_base_url",
        "openai_model",
        "github_token",
        "dispatch_webhook_url",
        "dispatch_token",
        mode="before",
    )
    @classmethod
    def _strip_quotes(cls, value):
        if value is None:
            return ""
        text = str(value).strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"', "“", "”"}:
            text = text[1:-1].strip()
        return text

    @property
    def db_path(self) -> Path:
        path = self.data_dir
        if not path.is_absolute():
            path = RADAR_DIR / path
        return path / "frontier.db"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def env_file_found(self) -> str:
        for path in ENV_CANDIDATES:
            if path.is_file():
                return str(path)
        return ""


settings = Settings()
