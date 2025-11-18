from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import uvicorn
import os
import json
from urllib import request, error
import pandas as pd
from io import BytesIO

# Load .env locally if available; Vercel uses project env vars
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        # Check if the file is a CSV
        if file.filename and file.filename.endswith('.csv'):
            # Read the file content
            contents = await file.read()
            # Load into pandas DataFrame
            df = pd.read_csv(BytesIO(contents))
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

@app.get("/")
async def ping():
    return {"message": "pong"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)