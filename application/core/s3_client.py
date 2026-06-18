# application/core/s3_client.py
import os

# 🔥 ЖЕЛЕЗОБЕТОННЫЙ ФИКС ДЛЯ СВЕЖИХ ВЕРСИЙ BOTO3/AIOBOTOCORE
# Выключаем принудительный расчет чексумм, ломающий HTTP-заголовки на сторонних S3
os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "when_required"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "when_required"

import uuid
from typing import Optional
import aioboto3
from dotenv import load_dotenv

load_dotenv()

class S3Storage:
    def __init__(self):
        self.access_key = os.getenv("S3_ACCESS_KEY_ID")
        self.secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.public_url = os.getenv("S3_PUBLIC_URL", "").rstrip("/")

        # Инициализируем сессию
        self.session = aioboto3.Session()

    async def upload_file(self, file_bytes: bytes, original_filename: str, folder: str = "categories") -> Optional[str]:
        """
        Загружает байты файла в Tebi.io и возвращает прямую публичную ссылку.
        """
        # Безопасно вытаскиваем расширение
        extension = original_filename.split(".")[-1] if "." in original_filename else "jpg"
        unique_filename = f"{folder}/{uuid.uuid4()}.{extension}"

        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3_client:
            try:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=unique_filename,
                    Body=file_bytes,
                    ContentType=f"image/{extension}",
                    ACL="public-read"  # Делаем файл публичным при загрузке
                )
                return f"{self.public_url}/{unique_filename}"
            except Exception as e:
                print(f"❌ Ошибка загрузки в Tebi.io: {e}")
                return None

# Синглтон для импорта в роуты или сервисы приложений
s3_storage = S3Storage()