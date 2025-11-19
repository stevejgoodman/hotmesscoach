from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
import uvicorn
import os
import json
from typing import Literal, Optional
from urllib import request, error
import pandas as pd
from io import BytesIO
from openai import OpenAI
import base64
import requests
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
    try:
        # Check if the file is a CSV
        if file.filename and file.filename.endswith('.csv'):
            # Read the file content
            contents = await file.read()
            # Load into pandas DataFrame
            df = pd.read_csv(BytesIO(contents))
            # Keep only the last 20 rows
            return {
                "filename": file.filename,
                "message": "CSV file loaded successfully",
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict(orient='records')
            }
        else:
            return {"filename": file.filename, "message": "File is not a CSV file"}
    except Exception as e:
        return {"filename": file.filename, "error": str(e)}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    global df
    try:
        if client is None:
            return {"error": "OpenAI API key not configured"}
        
        # Build the user message
        user_content = req.message
        if df is not None:
            if req.model == "dall-e-2":
                # note very limited prompt window for dall-e-2 so only use last 20 rows
                user_content += f"\n\nThe user has also uploaded a document. Here is the content:\n{df.tail(20).to_string()}"
            else:
                user_content += f"\n\nThe user has also uploaded a document. Here is the content:\n{df.to_string()}"
            
        
        # Handle chat models vs image models
        if req.model == "gpt-4o-mini":
            # Chat completion
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a supportive mental coach who helps overwhelmed people feel calmer."},
                    {"role": "user", "content": user_content},
                ]
            )
            return {"reply": response.choices[0].message.content}
        else:
            # Image generation
            # Try to get base64 response (works for dall-e-2)
            
            if req.model == "dall-e-2":
                try:
                    result = client.images.generate(
                        model="dall-e-2",
                        prompt=user_content + "create a chart of the user content data in a .png format",
                        size="512x512",
                        response_format="b64_json"
                    )
                    # Decode base64 string to bytes
                    image_base64 = result.data[0].b64_json
                    image_bytes = base64.b64decode(image_base64)
                except Exception as e:
                    return {"error": f"Failed to generate image: {str(e)}"}
            else:
                # Use URL response and download (for dall-e-3)
                result = client.images.generate(
                    model="dall-e-3",
                    prompt=user_content + "create a chart of the data in a .png format",
                    size="512x512"
                )
                # Download image from URL
                image_url = result.data[0].url
                img_response = requests.get(image_url)
                image_bytes = img_response.content
            
            # Return image as PNG response
            return Response(content=image_bytes, media_type="image/png")

    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ping")
async def ping():
    return {"message": "pong"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)