import requests
import os
import json
import re
from PIL import Image
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt


def  test_upload_file():
    url = 'http://127.0.0.1:8000/api/uploadfile'
    with open('data/two_month_hot_mess_data.csv', 'rb') as f:
        file = {'file': f}
        resp = requests.post(url=url, files=file) 
        print(resp.json())

def test_ping():
    url = 'http://127.0.0.1:8000/api/ping'
    resp = requests.get(url=url)
    print(resp.json()['rows'], resp.json()['columns'])
def test_chat():
    url = 'http://127.0.0.1:8000/api/chat'
    # Test with image model
    data = {
        'message': 'I feel like a hot mess today...can you show the trend by creating python code f the "hot_mess_score" column. only return the python code and nothing else',
        'model': 'gpt-4o-mini' 
    }
    resp = requests.post(url=url, json=data)
    
    # Check response status
    print(f"Response status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"✗ Error: {resp.status_code}")
        try:
            print(resp.json())
        except:
            print(resp.text)
        return
    
    # Check if response is an image (PNG)
    content_type = resp.headers.get('content-type', '')
    if 'image/png' in content_type:
        # Get image bytes
        image_bytes = resp.content
        print(f"✓ Received PNG image ({len(image_bytes)} bytes)")
        
        # Verify it's a valid PNG by trying to open it with PIL
        try:
            img = Image.open(BytesIO(image_bytes))
            print(f"✓ Image is valid PNG")
            print(f"  Size: {img.size[0]}x{img.size[1]} pixels")
            print(f"  Format: {img.format}")
            print(f"  Mode: {img.mode}")
            
            # Save to file for inspection
            output_path = 'tests/generated_image.png'
            os.makedirs('tests', exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"  ✓ Saved to: {output_path}")
            
        except Exception as e:
            print(f"✗ Invalid image: {e}")
    else:
        # Handle JSON response (for chat models or errors)
        print(f"Response content-type: {content_type}")
        try:
            response_data = resp.json()
            reply = response_data.get('reply', '')
            print(f"Reply received: {len(reply)} characters")
            
            # Extract Python code from triple backticks
            # Match ```python ... ``` or ``` ... ```
            code_pattern = r'```(?:python)?\s*\n(.*?)\n```'
            matches = re.findall(code_pattern, reply, re.DOTALL)
            
            if matches:
                # Use the first code block found
                python_code = matches[0].strip()
                print(f"✓ Extracted Python code ({len(python_code)} characters)")
                print(f"Code preview:\n{python_code[:200]}...")
                
                # Create a namespace for code execution
                exec_namespace = {
                    'plt': plt,
                    'matplotlib': matplotlib,
                    'pd': __import__('pandas'),
                    'np': __import__('numpy'),
                    'os': os,
                }
                
                # Execute the code
                try:
                    exec(python_code, exec_namespace)
                    print("✓ Python code executed successfully")
                    
                    # Check if any matplotlib figures exist and save them
                    if plt.get_fignums():
                        output_path = 'tests/generated_plot.png'
                        os.makedirs('tests', exist_ok=True)
                        plt.savefig(output_path, dpi=150, bbox_inches='tight')
                        plt.close('all')  # Close all figures
                        print(f"  ✓ Plot saved to: {output_path}")
                    else:
                        print("  ℹ No matplotlib figures found to save")
                        
                except Exception as e:
                    print(f"✗ Error executing code: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("✗ No Python code block found in reply (looking for ```python ... ```)")
                print(f"Reply content:\n{reply[:500]}")
                
        except json.JSONDecodeError:
            print(f"✗ JSON decode error. Response text: {resp.text[:200]}")
        except Exception as e:
            print(f"✗ Error processing response: {e}")
            print(f"Response text: {resp.text[:200]}")



if __name__ == "__main__":
    test_upload_file()
    #test_ping()
    test_chat()