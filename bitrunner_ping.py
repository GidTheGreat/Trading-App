# bitrunner_ping.py

import requests
from botutils import runtimeglobals

class ServerPinger:
    def __init__(self, server_url, secret_code):
        self.server_url = server_url
        self.secret_code = secret_code

    def ping(self):
        try:
            headers = {"X-Passphrase": self.secret_code}
            response = requests.get(f"{self.server_url}/ping", headers=headers, timeout=5)
            if response.status_code == 200:
                print("✅ Server is live:", response.json())
                return True
            else:
                print("❌ Unauthorized or bad response:", response.status_code, response.text)
                return False
        except requests.RequestException as e:
            print("❌ Server unreachable:", e)
            return False




"""
class ServerPinger:
    def __init__(self, server_ip, port=5000):
        self.base_url = f"http://{server_ip}:{port}"

    def ping(self):
        try:
            response = requests.get(f"{self.base_url}/ping?passphrase=my_secret_code", timeout=3)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Bad response"}
        except Exception as e:
            return {"error": str(e)}
            
"""            
            