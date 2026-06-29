from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlparse

class Settings(BaseSettings):
    # Твои переменные
    DATABASE_URL: str
    REDIS_URL: str
    admin_id: str
    bot_token: str
    api_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_endpoint_url: str
    s3_bucket_name: str
    s3_public_url: str

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

    @property
    def redis_config(self):
        """Парсинг URL для Redis"""
        url = urlparse(self.REDIS_URL)
        return {
            "host": url.hostname,
            "port": url.port or 6379,
            "db": int(url.path.lstrip('/')) if url.path else 0
        }

settings = Settings()



CACHE_KEY_CATALOG = "catalog:structure"
CACHE_KEY_PRODUCTS = "product:structure"