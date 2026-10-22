from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIMS_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://sims:sims@localhost:55433/sims"
    test_database_url: str = "postgresql+asyncpg://sims:sims@localhost:55433/sims_test"
    demo: bool = False  # the database holds synthetic demo data; the UI labels it as such


@lru_cache
def get_settings() -> Settings:
    return Settings()
