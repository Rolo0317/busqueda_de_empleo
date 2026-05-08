from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    browser: str = Field(default="edge", alias="BROWSER")
    magneto_search_keywords: str = Field(alias="MAGNETO_SEARCH_KEYWORDS")
    target_locations: str = Field(default="Colombia,Bogota,Medellin,Remoto LATAM,Remoto Worldwide", alias="TARGET_LOCATIONS")
    priority_skills: str = Field(default="React,Next.js,Node.js,TypeScript,JavaScript,APIs,MongoDB,SQL,AWS,Docker,IA,Automatizacion", alias="PRIORITY_SKILLS")
    magneto_city: str = Field(alias="MAGNETO_CITY")
    max_offers: int = Field(alias="MAX_OFFERS")
    wait_seconds: int = Field(alias="WAIT_SECONDS")
    login_wait_seconds: int = Field(default=180, alias="LOGIN_WAIT_SECONDS")
    loop_interval_seconds: int = Field(default=300, alias="LOOP_INTERVAL_SECONDS")
    min_match_score: int = Field(default=70, alias="MIN_MATCH_SCORE")
    min_salary: int = Field(default=2_500_000, alias="MIN_SALARY")
    run_continuously: bool = Field(default=True, alias="RUN_CONTINUOUSLY")
    cv_path: Path = Field(alias="CV_PATH")
    candidate_profile_path: Path = Field(default=Path("candidate_profile.json"), alias="CANDIDATE_PROFILE_PATH")
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("DB_HOST", "hotst", "HOST"))
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(default="root", validation_alias=AliasChoices("DB_USER", "sql_user", "SQL_USER"))
    db_password: str = Field(default="", validation_alias=AliasChoices("DB_PASSWORD", "Sql_password", "SQL_PASSWORD"))
    db_name: str = Field(default="job_bot", alias="DB_NAME")
    chrome_user_data_dir: Path = Field(alias="CHROME_USER_DATA_DIR")
    chrome_profile_directory: str = Field(alias="CHROME_PROFILE_DIRECTORY")
    edge_user_data_dir: Path = Field(alias="EDGE_USER_DATA_DIR")
    edge_profile_directory: str = Field(alias="EDGE_PROFILE_DIRECTORY")
    edge_binary_path: Path = Field(alias="EDGE_BINARY_PATH")
    edge_bot_user_data_dir: Path = Field(alias="EDGE_BOT_USER_DATA_DIR")
    allow_bot_profile_fallback: bool = Field(default=False, alias="ALLOW_BOT_PROFILE_FALLBACK")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def search_keywords(self) -> list[str]:
        return [keyword.strip() for keyword in self.magneto_search_keywords.split(",") if keyword.strip()]

    @property
    def locations(self) -> list[str]:
        return [location.strip() for location in self.target_locations.split(",") if location.strip()]

    @property
    def skills(self) -> list[str]:
        return [skill.strip() for skill in self.priority_skills.split(",") if skill.strip()]


def load_settings() -> Settings:
    base_path = Path(__file__).resolve().parent
    env_files = (
        base_path.parent / ".env",
        base_path.parent / "magneto_job_system" / ".env",
        base_path / ".env",
    )
    existing_env_files = tuple(str(path) for path in env_files if path.exists())
    return Settings(_env_file=existing_env_files or None)
