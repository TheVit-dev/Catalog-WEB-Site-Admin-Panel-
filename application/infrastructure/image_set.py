import os
import uuid
from aioboto3 import Session
from botocore.config import Config
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "WHEN_REQUIRED"
os.environ["AWS_RESPONSE_CHECKSUM_VALIDATION"] = "WHEN_REQUIRED"

S3_ACESS_KEY = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "https://s3.tebi.io")

s3_config = Config(
    request_checksum_calculation="WHEN_REQUIRED",
    response_checksum_validation="WHEN_REQUIRED"
)

async def upload_image_to_s3(file_bytes: bytes, original_filename: str) ->str:

    ext = os.path.splitext(original_filename)[1] or ".jpg"
    unique_filename =  f"{uuid.uuid4()}{ext}"

    session = Session()

    async with session.client(  

        service_name="s3",
        aws_access_key_id= S3_ACESS_KEY,
        aws_secret_access_key= S3_SECRET_KEY,
        endpoint_url= S3_ENDPOINT_URL

    ) as s3:
        
        file_size = len(file_bytes)

        await s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=unique_filename,
            Body=file_bytes,
            ACL="public-read",
            ContentType=f"image/{ext.replace('.', '')}",
            ContentLength=file_size  
        )

        
    file_url = f"https://s3.tebi.io/{S3_BUCKET_NAME}/{unique_filename}"
    return file_url