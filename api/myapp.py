from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
import uvicorn
import os
import logging
from typing import Literal, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env locally if available; Vercel uses project env vars
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Handle imports for both module and script execution
import sys
from pathlib import Path

# When running as a script, add project root to path and use absolute imports
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from api.services.app_service import AppService
else:
    # When imported as a module, use relative imports
    from .services import AppService

class ChatRequest(BaseModel):
    message: str
    model: Optional[Literal["gpt4o", "gpt-4o-mini"]] = "gpt-4o-mini"

app = FastAPI()

# Initialize service instance
app_service = AppService()

@app.post("/api/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    """Upload and process CSV file."""
    logger.info(f"File upload request received: {file.filename}")
    contents = await file.read()
    return app_service.upload_file(contents, file.filename or "unknown")

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Handle chat request."""
    logger.info(f"Chat request received - model: {req.model}, message length: {len(req.message)}")
    result = app_service.chat(req.message, req.model)
    
    # Handle image responses
    if "image_bytes" in result:
        return Response(content=result["image_bytes"], media_type=result.get("media_type", "image/png"))
    
    return result

@app.get("/api/ping")
async def ping():
    """Ping endpoint."""
    logger.info("Ping endpoint called")
    return app_service.ping()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)