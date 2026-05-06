import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:5002/v1/chat/completions"
# Replace with a valid Distributor ID or API Key from your DB
# For testing, we might need to insert a dummy one or use an existing one.
# I will try to use a dummy ID '1' or similar if I know one exists, 
# or I will assume the Authorization header simulates a Bearer token that matches a distributor ID.
API_KEY = "1" # Assuming ID 1 exists for testing purposes

def test_chat_completion():
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hola, ¿qué productos vendes?"}
        ],
        "user": "test_user_openai_compat"
    }
    
    try:
        print(f"Sending request to {BASE_URL}...")
        response = requests.post(BASE_URL, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2))
            
            # Validation
            assert "id" in data
            assert data["object"] == "chat.completion"
            assert len(data["choices"]) > 0
            message = data["choices"][0]["message"]
            assert message["role"] == "assistant"
            print("\n✅ Verification PASSED: Endpoint returned valid OpenAI format.")
        else:
            print(f"Error Response: {response.text}")
            print("\n❌ Verification FAILED.")
            
    except Exception as e:
        print(f"Exception: {e}")
        print("\n❌ Verification FAILED (Exception).")

if __name__ == "__main__":
    test_chat_completion()
