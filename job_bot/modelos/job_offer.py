from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class JobOffer(BaseModel):
    platform: str = Field(default="Magneto")
    title: str
    company: str = "No especificada"
    url: HttpUrl
    published_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    city: str = "No especificada"
    salary: str = "No especificado"
    description: str = ""
