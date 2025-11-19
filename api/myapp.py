from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
import uvicorn
import os
import json
import logging
from typing import Literal, Optional
from urllib import request, error
import pandas as pd
from io import BytesIO
from openai import OpenAI
import base64
import requests

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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

class ChatRequest(BaseModel):
    message: str
    model: Optional[Literal["dall-e-2", "dall-e-3", "gpt-4o-mini"]] = "gpt-4o-mini"

app = FastAPI()
df = None

@app.post("/api/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    global df
    logger.info(f"File upload request received: {file.filename}")
    try:
        # Check if the file is a CSV
        if file.filename and file.filename.endswith('.csv'):
            # Read the file content
            contents = await file.read()
            logger.info(f"Reading CSV file: {file.filename}, size: {len(contents)} bytes")
            # Load into pandas DataFrame
            df = pd.read_csv(BytesIO(contents))
            logger.info(f"CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            # Keep only the last 20 rows
            return {
                "filename": file.filename,
                "message": "CSV file loaded successfully",
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict(orient='records')
            }
        else:
            logger.warning(f"File is not a CSV: {file.filename}")
            return {"filename": file.filename, "message": "File is not a CSV file"}
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
        return {"filename": file.filename, "error": str(e)}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    global df
    logger.info(f"Chat request received - model: {req.model}, message length: {len(req.message)}")
    try:
        if client is None:
            logger.error("OpenAI API key not configured")
            return {"error": "OpenAI API key not configured"}
        
        # Build the user message
        user_content = req.message
        if df is not None:
            if req.model == "dall-e-2":
                # note very limited prompt window for dall-e-2 so only use last 20 rows
                logger.info("Adding DataFrame data to prompt (last 20 rows for dall-e-2)")
                user_content += f"\n\nThe user has also uploaded a document. Here is the content:\n{df.tail(20).to_string()}"
            else:
                logger.info("Adding DataFrame data to prompt (full dataset)")
                user_content += f"\n\nThe user has also uploaded a document. Here is the content:\n{df.to_string()}"
        else:
            logger.info("No DataFrame data available to include in prompt")
            
        
        # Handle chat models vs image models
        if req.model == "gpt-4o-mini":
            # Chat completion
            logger.info("Calling OpenAI chat completion API")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a supportive mental coach who helps overwhelmed people feel calmer."},
                    {"role": "user", "content": user_content},
                ]
            )
            logger.info(f"Chat completion successful, response length: {len(response.choices[0].message.content)}")
            return {"reply": response.choices[0].message.content}
        else:
            # Image generation
            logger.info(f"Generating image with model: {req.model}")
            
            if req.model == "dall-e-2":
                try:
                    logger.info("Calling DALL-E 2 image generation API")
                    result = client.images.generate(
                        model="dall-e-2",
                        prompt=user_content + "create a chart of the user content data in a .png format",
                        size="512x512",
                        response_format="b64_json"
                    )
                    # Decode base64 string to bytes
                    image_base64 = result.data[0].b64_json
                    image_bytes = base64.b64decode(image_base64)
                    logger.info(f"DALL-E 2 image generated successfully, size: {len(image_bytes)} bytes")
                except Exception as e:
                    logger.error(f"Failed to generate DALL-E 2 image: {str(e)}", exc_info=True)
                    return {"error": f"Failed to generate image: {str(e)}"}
            else:
                # Use URL response and download (for dall-e-3)
                logger.info("Calling DALL-E 3 image generation API")
                result = client.images.generate(
                    model="dall-e-3",
                    prompt=user_content + "create a chart of the data in a .png format",
                    size="512x512"
                )
                # Download image from URL
                image_url = result.data[0].url
                logger.info(f"Downloading image from URL: {image_url}")
                img_response = requests.get(image_url)
                image_bytes = img_response.content
                logger.info(f"DALL-E 3 image downloaded successfully, size: {len(image_bytes)} bytes")
            
            # Return image as PNG response
            return Response(content=image_bytes, media_type="image/png")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return {"error": str(e)}

@app.get("/api/ping")
async def ping():
    logger.info("Ping endpoint called")
    return {"message": "pong"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)