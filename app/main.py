from fastapi import FastAPI, UploadFile, File, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import os
from datetime import datetime

app = FastAPI(
    title="Media Service",
    description="Handles media uploads and metadata storage",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
    app.database = app.mongodb_client[settings.MONGO_DB]

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

@app.post("/upload", tags=["Media"])
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    filepath = os.path.join("uploads", filename)

    os.makedirs("uploads", exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    collection = app.database["media"]
    media_doc = {
        "filename": filename,
        "content_type": file.content_type,
        "path": filepath,
        "uploaded_at": datetime.utcnow()
    }
    await collection.insert_one(media_doc)

    print(f"EVENT: media.uploaded -> {filename}")

    return {"message": "File uploaded successfully", "filename": filename}
