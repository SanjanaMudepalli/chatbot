from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

from app.services.document_loader import extract_text
from app.utils.text_chunker import chunk_text
from app.services.embeddings import generate_embeddings
from app.services.vector_store import create_vector_store, get_all_files
from app.services.rag_agent import generate_answer

router = APIRouter()


# 📌 Upload + Index
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        text = await extract_text(file)
        chunks = chunk_text(text)
        embeddings = generate_embeddings(chunks)

        create_vector_store(embeddings, chunks, file.filename)

        return {
            "message": "Document indexed successfully",
            "chunks": len(chunks),
            "filename": file.filename
        }

    except Exception as e:
        return {"error": str(e)}


# 📌 Request model
class ChatRequest(BaseModel):
    question: str
    files: list[str] | None = None   # ✅ optional filtering


# 📌 Ask question
@router.post("/ask")
def ask_question(data: ChatRequest):
    try:
        response = generate_answer(
            question=data.question,
            selected_files=data.files
        )
        return response

    except Exception as e:
        return {
            "answer": "Error processing request.",
            "error": str(e),
            "sources": []
        }


# 📌 List uploaded files
@router.get("/files")
def list_files():
    return {
        "files": get_all_files()
    }