import requests
import json

# Configuration
BASE_URL = "http://localhost:5000/api"
USER_EMAIL = "jonnathan.ypg@gmail.com"
USER_PASS = "admin123" # Use your actual password if different

def debug_whatsapp_init():
    print(f"--- EnpiAI Local API Debug ---")
    
    # 1. Login to get JWT
    print(f"\n1. Attempting login for {USER_EMAIL}...")
    login_url = f"{BASE_URL}/auth/login"
    login_data = {"email": USER_EMAIL, "password": USER_PASS}
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed ({response.status_code}): {response.text}")
            return
        
        token = response.json().get('access_token')
        print("✅ Login successful. Token acquired.")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test Status (GET)
        print("\n2. Testing WhatsApp Status (GET)...")
        status_url = f"{BASE_URL}/channels/whatsapp/status"
        res_status = requests.get(status_url, headers=headers)
        print(f"   Response Code: {res_status.status_code}")
        print(f"   Body: {res_status.text}")
        
        # 3. Test Init (POST)
        print("\n3. Testing WhatsApp Init (POST)...")
        init_url = f"{BASE_URL}/channels/whatsapp/init"
        res_init = requests.post(init_url, headers=headers)
        print(f"   Response Code: {res_init.status_code}")
        print(f"   Body: {res_init.text}")
        
        if res_init.status_code == 404:
            print("\n🚨 DEBUG FINDING: The 404 is reproducible locally on port 5000!")
            print("This means the issue is INSIDE Flask logic, not Nginx.")
        elif res_init.status_code == 200:
            print("\n✨ DEBUG FINDING: It works locally! The issue is likely Nginx or the Frontend request format.")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    debug_whatsapp_init()
