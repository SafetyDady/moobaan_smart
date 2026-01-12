from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "moobaan_smart_backend"
    ENV: str = "local"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/moobaan_smart"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production-use-openssl-rand-hex-32"
    
    class Config:
        env_file = ".env"


settings = Settings()