import requests
import sys

def test_api_paths(base_url):
    print(f"--- EnpiAI API Path Diagnostic ---")
    print(f"Target Base URL: {base_url}")
    
    paths_to_test = [
        "/health",
        "/api/auth/login", # Should be 405 (Method Not Allowed) if path is correct, 404 if prefix stripped
        "/auth/login",     # Should be 404 if prefix is NOT stripped
    ]
    
    for path in paths_to_test:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            # We use POST for login test to see if it hits the route
            method = "POST" if "login" in path else "GET"
            response = requests.request(method, url, timeout=5)
            print(f"\nTesting {method} {url}")
            print(f"  Status Code: {response.status_code}")
            
            if path == "/health" and response.status_code == 200:
                print("  ✅ Health check successful.")
            elif path == "/api/auth/login":
                if response.status_code == 405:
                    print("  ✅ SUCCESS: The /api prefix is being preserved correctly.")
                elif response.status_code == 404:
                    print("  ❌ ERROR: The /api/ prefix is likely being STRIPPED by Nginx.")
            elif path == "/auth/login":
                if response.status_code == 404:
                    print("  ✅ Correct: This path should not exist without /api.")
                elif response.status_code == 405:
                    print("  ❌ ERROR: Nginx is stripping /api! Flask is receiving /auth/login.")
                    
        except Exception as e:
            print(f"  ❌ Connection Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vps_api.py <base_url>")
        print("Example: python test_vps_api.py https://enpi.click")
        sys.exit(1)
    
    test_api_paths(sys.argv[1])
