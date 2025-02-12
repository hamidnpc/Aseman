import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# Load credentials from environment variable
CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS")
CREDENTIALS_DICT = json.loads(CREDENTIALS_JSON)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authenticate_drive():
    creds = Credentials.from_service_account_info(CREDENTIALS_DICT, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def upload_to_drive(file_path, file_name):
    service = authenticate_drive()
    file_metadata = {"name": file_name, "mimeType": "application/octet-stream"}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    return f"File uploaded successfully! Google Drive ID: {uploaded_file['id']}"
