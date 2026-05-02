from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
import io


def get_drive_service(access_token):
    creds = Credentials(token=access_token)
    return build("drive", "v3", credentials=creds)


# 🔥 DOWNLOAD FILE CONTENT
def download_file(file_id, access_token):
    service = get_drive_service(access_token)

    request = service.files().get_media(fileId=file_id)

    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)

    return file_stream.read().decode("utf-8")