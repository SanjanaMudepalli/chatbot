from pypdf import PdfReader
from fastapi import UploadFile, HTTPException
import io

async def extract_text(file: UploadFile):
    filename = file.filename.lower()
    contents = await file.read()

    try:
        if filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(contents))
            text = ""

            for page in pdf.pages:
                text += page.extract_text() or ""

            return text

        elif filename.endswith(".txt") or filename.endswith(".md"):
            return contents.decode("utf-8")

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to process document"
        )