from fastapi import UploadFile, HTTPException
from PIL import Image
from pypdf import PdfReader
import io


class FileService:

    async def extract_content(self, file: UploadFile) -> str:

        filename = file.filename.lower()

        # ---------------- TEXT FILE ----------------
        if filename.endswith(".txt"):
            content = await file.read()

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Empty text file"
                )

            return content.decode("utf-8", errors="ignore")

        # ---------------- PDF FILE ----------------
        elif filename.endswith(".pdf"):
            pdf_bytes = await file.read()

            reader = PdfReader(io.BytesIO(pdf_bytes))

            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No readable text found in PDF"
                )

            return text

        # ---------------- IMAGE FILE ----------------
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image_bytes = await file.read()

            try:
                image = Image.open(io.BytesIO(image_bytes))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )

            return (
                f"Image uploaded successfully.\n"
                f"Size: {image.size}\n"
                f"Mode: {image.mode}"
            )

        # ---------------- UNSUPPORTED ----------------
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )
