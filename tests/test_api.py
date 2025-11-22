import os
import sys
import pathlib
# Add parent directory to path to import from api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.services import AppService

# Initialize service instance for testing
app_service = AppService()

def test_upload_file(file_path: str):
    """Test file upload functionality."""
   
    with open(file_path, 'rb') as f:
        file_content = f.read()
        result = app_service.upload_file(file_content, pathlib.Path(file_path).name)
        
        if "error" in result:
            print(f"✗ Error: {result.get('error')}")
            return False
        
        print(f"✓ File uploaded successfully")
        print(f"  Rows: {result.get('rows')}, Columns: {result.get('columns')}")
        return True

def test_ping():
    """Test ping endpoint."""
    result = app_service.ping()
    print(f"✓ Ping response: {result.get('message')}")

def test_chat(message: str):
    """Test chat functionality."""
    result = app_service.chat(message, 'gpt-4o-mini')
    
    if "error" in result:
        print(f"✗ Error: {result.get('error')}")
        return False
    
    reply = result.get('reply', '')
    print(f"✓ Chat response received ({len(reply)} characters)")
    print(f"Reply: {reply[:200]}...")
    return True

def test_chat_with_chart(message: str):
    """Test chat with chart generation."""
    result = app_service.chat_with_chart(message, 'gpt-4o-mini')
    
    if "error" in result:
        print(f"✗ Error: {result.get('error')}")
        return False
    
    if "image_bytes" in result:
        image_bytes = result.get('image_bytes')
        media_type = result.get('media_type', 'image/png')
        print(f"✓ Chart generated successfully")
        print(f"  Image size: {len(image_bytes)} bytes")
        print(f"  Media type: {media_type}")
        
        # Optionally save to file for testing purposes
        output_path = 'tests/generated_plot.png'
        os.makedirs('tests', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
        print(f"  Saved to: {output_path} (for testing)")
        return True
    else:
        print(f"✗ Chart generation failed: No image bytes in response")
        return False

def router_test(query: str):
    """Route test query to appropriate test function."""
    if 'chart' in query.lower() or 'plot' in query.lower():
        return test_chat_with_chart(query)
    else:
        return test_chat(query)

if __name__ == "__main__":
    test_upload_file('data/two_month_hot_mess_data.csv')
    #test_ping()
    #test_chat()
    #test_chat_with_chart()
    router_test('I feel like a hot mess today...can you help?')
    router_test('I feel like a hot mess today...can you chart  the past trend of my hot mess score?')