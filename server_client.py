import tempfile
import requests
import os
from botutils import runtimeglobals
import importlib
from botutils import status
import time



class ServerClient:
    def __init__(self, server_url, secret_code):
        self.server_url = server_url
        self.secret_code = secret_code
        self.headers = {
            "X-Passphrase": self.secret_code
        }

    def fetch_status_messages(self):
            """Calls /status_messages to fetch and print current server status messages."""
            try:
                response = requests.get(
                    f"{self.server_url}/status_messages",
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    status_data = response.json()
                    status.status_messages = status_data
                    #print("✅ Status Messages:")
                    #for category, messages in status_data.items():
                        #print(f"  [{category}] -> {messages}")
                    return status_data
                else:
                    print("❌ Failed to fetch status messages:", response.status_code, response.text)
                    return None
            except requests.RequestException as e:
                print("❌ Exception while fetching status messages:", e)
                return None


    def check_bot_status(self):
        """Check if the bot instance is running on the server."""
        try:
            response = requests.get(
                f"{self.server_url}/bot_status",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("bot_running", False)
            else:
                print("❌ Failed to fetch bot status:", response.status_code, response.text)
                return False
        except requests.RequestException as e:
            print("❌ Exception while checking bot status:", e)
            return False

    def start_main_coroutine(self):
        """Start the main coroutine if not already running."""
        time.sleep(10)
        try:
            if self.check_bot_status():
                print("ℹ️ Bot instance already running — skipping start.")
                return True

            response = requests.post(
                f"{self.server_url}/start_main",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Server response:", response.json())
                return True
            else:
                print("❌ Server rejected request:", response.status_code, response.text)
                return False
        except requests.RequestException as e:
            print("❌ Exception calling start_main:", e)
            return False

    def reload_server(self):
        """Trigger server reload via the /reload_server endpoint."""
        try:
            response = requests.post(
                f"{self.server_url}/reload_server",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Server reload triggered:", response.json())
                return True
            else:
                print("❌ Reload failed:", response.status_code, response.text)
                return False
        except requests.RequestException as e:
            print("❌ Exception calling reload_server:", e)
            return False


    def send_runtimeglobals(self):
        try:
            # Build Python code string with current runtimeglobals
            lines = [
            "# Auto-generated runtimeglobals snapshot\n",
            "from collections import deque\n\n"
        ]
            for key in dir(runtimeglobals):
                if key.startswith("__"):
                    continue
                if key.startswith("ws"):
                    continue
                value = getattr(runtimeglobals, key)
                if callable(value):
                    continue

                # Represent strings with quotes, others as is
                if isinstance(value, str):
                    val_repr = f"'{value}'"
                else:
                    val_repr = repr(value)

                lines.append(f"{key} = {val_repr}\n")

            code = "".join(lines)

            # Write to a temporary .py file
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp_file:
                tmp_file.write(code)
                tmp_filepath = tmp_file.name

            # Send the generated file
            with open(tmp_filepath, "rb") as f:
                files = {"file": ("runtimeglobals.py", f, "text/x-python")}
                response = requests.post(
                    f"{self.server_url}/upload_runtime_file",
                    files=files,
                    headers=self.headers,
                    timeout=10
                )

            os.remove(tmp_filepath)  # cleanup

            if response.status_code == 200:
                print("✅ Live runtimeglobals file uploaded:", response.json())
                return True
            else:
                print("❌ Upload failed:", response.status_code, response.text)
                return False

        except Exception as e:
            print("❌ Exception while sending runtimeglobals:", e)
            return False