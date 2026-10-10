import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    magneto_search_keywords: str = Field(alias="MAGNETO_SEARCH_KEYWORDS")
    platforms: str = Field(default="magneto", alias="PLATFORMS")
    supervised_apply: bool = Field(default=True, alias="SUPERVISED_APPLY")
    exhaustive_mode: bool = Field(default=False, alias="EXHAUSTIVE_MODE")
    target_locations: str = Field(default="Colombia,Bogota,Medellin,Remoto LATAM,Remoto Worldwide", alias="TARGET_LOCATIONS")
    priority_skills: str = Field(default="React,Next.js,Node.js,TypeScript,JavaScript,APIs,MongoDB,SQL,AWS,Docker,IA,Automatizacion", alias="PRIORITY_SKILLS")
    magneto_city: str = Field(alias="MAGNETO_CITY")
    # Tope de postulaciones enviadas por corrida; 0 es sin tope.
    max_offers: int = Field(default=0, alias="MAX_OFFERS")
    wait_seconds: int = Field(alias="WAIT_SECONDS")
    loop_interval_seconds: int = Field(default=300, alias="LOOP_INTERVAL_SECONDS")
    # Pausa tras cada respuesta del cuestionario, para revisarla en vivo; 0 la desactiva.
    question_review_seconds: int = Field(default=0, ge=0, alias="QUESTION_REVIEW_SECONDS")
    min_match_score: int = Field(default=70, alias="MIN_MATCH_SCORE")
    min_salary: int = Field(default=2_500_000, alias="MIN_SALARY")
    run_continuously: bool = Field(default=True, alias="RUN_CONTINUOUSLY")
    # Ritmo del bot continuo: tope de postulaciones por dia (0 sin tope) y
    # franja horaria local en la que postula [inicio, fin).
    max_postulaciones_dia: int = Field(default=40, ge=0, alias="MAX_POSTULACIONES_DIA")
    hora_inicio_postulacion: int = Field(default=7, ge=0, le=23, alias="HORA_INICIO_POSTULACION")
    hora_fin_postulacion: int = Field(default=21, ge=1, le=24, alias="HORA_FIN_POSTULACION")
    cv_path: Path = Field(alias="CV_PATH")
    candidate_profile_path: Path = Field(default=Path("job_bot/candidate_profile.json"), alias="CANDIDATE_PROFILE_PATH")
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("DB_HOST", "hotst", "HOST"))
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_user: str = Field(default="root", validation_alias=AliasChoices("DB_USER", "sql_user", "SQL_USER"))
    db_password: str = Field(default="", validation_alias=AliasChoices("DB_PASSWORD", "Sql_password", "SQL_PASSWORD"))
    db_name: str = Field(default="job_bot", alias="DB_NAME")
    # Donde se guardan vacantes y postulaciones: "supabase" (lo que lee el panel
    # web) o "mysql" (la base local de antes).
    db_backend: str = Field(default="mysql", alias="DB_BACKEND")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_publishable_key: str = Field(default="", alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_email: str = Field(default="", alias="SUPABASE_EMAIL")
    supabase_password: str = Field(default="", alias="SUPABASE_PASSWORD")
    # Login automatico de Magneto (codigo de 6 digitos al correo). Sin
    # MAGNETO_EMAIL el bot no intenta entrar solo; sin la clave de aplicacion
    # de Gmail, pide el codigo a la persona y la espera.
    magneto_email: str = Field(default="", alias="MAGNETO_EMAIL")
    correo_codigos_clave_app: str = Field(default="", alias="CORREO_CODIGOS_CLAVE_APP")
    minutos_espera_login_manual: int = Field(default=10, ge=1, alias="MINUTOS_ESPERA_LOGIN_MANUAL")
    ats_ai_provider: str = Field(default="auto", alias="ATS_AI_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    edge_debugger_address: str = Field(default="", alias="EDGE_DEBUGGER_ADDRESS")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def enabled_platforms(self) -> list[str]:
        return [p.strip() for p in self.platforms.split(",") if p.strip()]

    @property
    def search_keywords(self) -> list[str]:
        return [keyword.strip() for keyword in self.magneto_search_keywords.split(",") if keyword.strip()]

    @property
    def locations(self) -> list[str]:
        return [location.strip() for location in self.target_locations.split(",") if location.strip()]

    @property
    def skills(self) -> list[str]:
        return [skill.strip() for skill in self.priority_skills.split(",") if skill.strip()]


class PerfilNoEncontrado(RuntimeError):
    """Falta el perfil del candidato: sin el, el bot responderia en blanco."""


def cargar_perfil(settings: Settings) -> dict:
    ruta = settings.candidate_profile_path
    if not ruta.exists():
        raise PerfilNoEncontrado(
            f"No existe el perfil del candidato en {ruta}. Copia "
            "job_bot/candidate_profile.example.json como job_bot/candidate_profile.json "
            "y rellenalo con tus datos."
        )
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError as error:
        raise PerfilNoEncontrado(f"El perfil {ruta} no es un JSON valido: {error}") from error


def load_settings() -> Settings:
    root_path = Path(__file__).resolve().parent.parent
    settings = Settings()
    if not settings.candidate_profile_path.is_absolute():
        settings.candidate_profile_path = root_path / settings.candidate_profile_path
    return settings
