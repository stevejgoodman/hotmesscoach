"""Business logic service layer for the application."""

import os
import json
import re
import logging
import base64
from typing import Optional, Literal, Dict, Any
from io import BytesIO
import pandas as pd
import requests
from openai import OpenAI
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import dotenv
dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class AppService:
    """Service layer encapsulating all business logic."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the service with OpenAI client."""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.df: Optional[pd.DataFrame] = None
    
    def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process uploaded CSV file.
        
        Args:
            file_content: The file content as bytes
            filename: The name of the uploaded file
            
        Returns:
            Dictionary with upload result information
        """
        logger.info(f"Processing file upload: {filename}")
        try:
            # Check if the file is a CSV
            if filename and filename.endswith('.csv'):
                # Load into pandas DataFrame
                self.df = pd.read_csv(BytesIO(file_content))
                self.df = self.df.tail(20)
                logger.info(f"CSV loaded successfully: {len(self.df)} rows, {len(self.df.columns)} columns")
                return {
                    "filename": filename,
                    "message": "CSV file loaded successfully",
                    "rows": len(self.df),
                    "columns": list(self.df.columns),
                    "data": self.df.to_dict(orient='records')
                }
            else:
                logger.warning(f"File is not a CSV: {filename}")
                return {"filename": filename, "message": "File is not a CSV file"}
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}", exc_info=True)
            return {"filename": filename, "error": str(e)}
    
    def ping(self) -> Dict[str, str]:
        """
        Ping endpoint - returns basic status.
        
        Returns:
            Dictionary with ping response
        """
        logger.info("Ping called")
        return {"message": "pong"}
    
    def chat(
        self, 
        message: str, 
        model: Optional[Literal["gpt-4o", "gpt-4o-mini"]] = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Handle chat request with OpenAI.
        
        Args:
            message: User's message
            model: Model to use for chat
            
        Returns:
            Dictionary with reply or error, or Response object for images
        """
        logger.info(f"Chat request - model: {model}, message length: {len(message)}")
        try:
            if self.client is None:
                logger.error("OpenAI API key not configured")
                return {"error": "OpenAI API key not configured"}
            
            # Build the user message
            user_content = message
            if self.df is not None:
                logger.info("Adding DataFrame data to prompt (full dataset)")
                user_content += f"\n\nThe user has also uploaded a document. Here is the content:\n{self.df.to_string()}"
            else:
                logger.info("No DataFrame data available to include in prompt")
        
            logger.info("Calling OpenAI chat completion API")
            response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a supportive mental coach who helps overwhelmed people feel calmer."},
                        {"role": "user", "content": user_content},
                    ]
                )
            logger.info(f"Chat completion successful, response length: {len(response.choices[0].message.content)}")
            return {"reply": response.choices[0].message.content}
            

        except Exception as e:
            logger.error(f"Error in chat: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def extract_and_execute_chart_code(
        self, 
        reply: str
    ) -> Dict[str, Any]:
        """
        Extract Python code from chat reply and execute it to generate charts.
        
        Args:
            reply: The chat reply containing Python code
            
        Returns:
            Dictionary with image bytes or error
        """
        logger.info("Extracting and executing chart code")
        try:
            # Extract Python code from triple backticks
            # Match ```python ... ``` or ``` ... ```
            code_pattern = r'```(?:python)?\s*\n(.*?)\n```'
            matches = re.findall(code_pattern, reply, re.DOTALL)
            
            if not matches:
                logger.warning("No Python code block found in reply")
                return {
                    "error": "No Python code block found in reply (looking for ```python ... ```)"
                }
            
            # Use the first code block found
            python_code = matches[0].strip()
            logger.info(f"Extracted Python code ({len(python_code)} characters)")
            
            # Create a namespace for code execution
            exec_namespace = {
                'plt': plt,
                'matplotlib': matplotlib,
                'pd': pd,
                'np': __import__('numpy'),
                'os': os,
                'df': self.df,  # Make DataFrame available to the code
            }
            
            # Execute the code
            try:
                exec(python_code, exec_namespace)
                logger.info("Python code executed successfully")
                
                # Check if any matplotlib figures exist and save them to BytesIO
                if plt.get_fignums():
                    # Save plot to BytesIO buffer instead of file
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                    plt.close('all')  # Close all figures
                    buffer.seek(0)
                    image_bytes = buffer.getvalue()
                    buffer.close()
                    logger.info(f"Chart generated successfully, size: {len(image_bytes)} bytes")
                    return {
                        "image_bytes": image_bytes,
                        "media_type": "image/png"
                    }
                else:
                    logger.info("No matplotlib figures found to save")
                    return {
                        "error": "No matplotlib figures found to save"
                    }
                    
            except Exception as e:
                logger.error(f"Error executing code: {e}", exc_info=True)
                return {
                    "error": f"Error executing code: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error in extract_and_execute_chart_code: {str(e)}", exc_info=True)
            return {
                "error": str(e)
            }
    
    def chat_with_chart(
        self, 
        message: str, 
        model: Optional[Literal["gpt-4o", "gpt-4o-mini"]] = "gpt-4o-mini"
    ) -> Dict[str, Any]:
        """
        Handle chat request that should generate a chart.
        
        Args:
            message: User's message
            model: Model to use for chat
            
        Returns:
            Dictionary with image_bytes and media_type, or error
        """
        logger.info(f"Chat with chart request - model: {model}")
        
        # Build prompt for chart generation
        if self.df is not None:
            prompt = f"""{message}   
Can you show the trend by creating a chart with python code from the 'hot_mess_score' column. 
Only return the python code and nothing else. here is the data: {self.df.to_string()}"""
        else:
            prompt = f"""{message}   
Can you show the trend by creating a chart with python code. 
Only return the python code and nothing else."""
        
        # Get chat response
        chat_result = self.chat(prompt, model)
        
        if "error" in chat_result:
            return chat_result
        
        reply = chat_result.get("reply", "")
        if not reply:
            return {"error": "No reply received from chat"}
        
        # Extract and execute chart code - returns image_bytes
        chart_result = self.extract_and_execute_chart_code(reply)
        return chart_result

