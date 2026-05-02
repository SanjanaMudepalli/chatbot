import os
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 🔥 RAG imports
from app.services.google_drive import download_file
from app.utils.text_chunker import chunk_text
from app.services.embeddings import generate_embeddings
from app.services.vector_store import create_vector_store

load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# 🔥 TEMP STORAGE
flow_dict = {}


# =========================
# 🔐 LOGIN
# =========================
@router.get("/login")
def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, state = flow.authorization_url(prompt="consent")
    flow_dict[state] = flow

    return RedirectResponse(auth_url)


# =========================
# 🔁 CALLBACK
# =========================
@router.get("/callback")
def callback(request: Request):
    try:
        state = request.query_params.get("state")

        if state not in flow_dict:
            return {"error": "Invalid state"}

        flow = flow_dict[state]

        flow.fetch_token(authorization_response=str(request.url))

        credentials = flow.credentials
        access_token = credentials.token

        return {
            "message": "Login successful",
            "access_token": access_token
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {"error": str(e)}


# =========================
# 📁 DRIVE SERVICE
# =========================
def get_drive_service(access_token):
    creds = Credentials(token=access_token)
    return build("drive", "v3", credentials=creds)


# =========================
# 📂 LIST FILES IN FOLDER
# =========================
@router.get("/files")
def list_files(
    folder_id: str = Query(...),
    access_token: str = Query(...)
):
    try:
        service = get_drive_service(access_token)

        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType)"
        ).execute()

        return {"files": results.get("files", [])}

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {"error": str(e)}


# =========================
# 🔥 INDEX ENTIRE FOLDER
# =========================
@router.post("/index-folder")
def index_folder(
    folder_id: str = Query(...),
    access_token: str = Query(...)
):
    try:
        service = get_drive_service(access_token)

        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType)"
        ).execute()

        files = results.get("files", [])

        total_chunks = 0

        for file in files:
            file_id = file["id"]
            filename = file["name"]

            print(f"📄 Processing: {filename}")

            # 🔥 Download file
            content = download_file(file_id, access_token)

            # 🔥 Chunk text
            chunks = chunk_text(content)

            # 🔥 Generate embeddings
            embeddings = generate_embeddings(chunks)

            # 🔥 Store in vector DB
            create_vector_store(embeddings, chunks, filename)

            total_chunks += len(chunks)

        return {
            "message": "Folder indexed successfully",
            "files_processed": len(files),
            "total_chunks": total_chunks
        }

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return {"error": str(e)}