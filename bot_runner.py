# bot_runner.py
import asyncio
import threading
from kivy.clock import Clock
from kivy.utils import platform
from botutils.analysis_runner import start_pure_websocket_session
from botutils import runtimeglobals
from bitrunner_ping import ServerPinger
from server_client import ServerClient
from kivy.metrics import dp
import sys
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


def show_server_unreachable_popup(on_confirm, on_cancel):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

    # Message label
    message_label = Label(
        text="Server unreachable.\nContinue in local mode?",
        halign="center",
        valign="middle"
    )
    message_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

    # Buttons row (Yes / No side by side)
    btn_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=10)
    
    yes_btn = Button(
        text="Yes",
        background_color=(0.2, 0.6, 0.2, 1)
    )
    yes_btn.bind(on_release=lambda *args: (popup.dismiss(), on_confirm()))

    no_btn = Button(
        text="No",
        background_color=(0.6, 0.2, 0.2, 1)
    )
    no_btn.bind(on_release=lambda *args: (popup.dismiss(), on_cancel()))

    btn_layout.add_widget(yes_btn)
    btn_layout.add_widget(no_btn)

    # Assemble layout
    layout.add_widget(message_label)
    layout.add_widget(btn_layout)

    # Create popup
    popup = Popup(
        title="Connection Failed",
        content=layout,
        size_hint=(None, None),
        size=(dp(280), dp(180)),
        auto_dismiss=False
    )
    popup.open()


class BotRunner:
    def __init__(self, loop, stop_event):
        self.loop = loop
        self.stop_event = stop_event
        self.tasks = []  # Track tasks

    def run(self):
        print(f"[RUN] Loop ID: {id(self.loop)} | Thread: {threading.current_thread().name}")
        asyncio.set_event_loop(self.loop)

        async def heartbeat():
            while True:
                await asyncio.sleep(1)

        async def monitor_stop():
            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)
            print("[STOP] Stop event received. Shutting down loop.")
            # Cancel all tasks before stopping the loop
            for task in self.tasks:
                task.cancel()
            self.loop.stop()

        async def loop_fetch(client, interval=2):
            while True:
                client.fetch_status_messages()
                await asyncio.sleep(interval)


        async def startup():
            try:
                if runtimeglobals.run_mode == "Local":
                    await start_pure_websocket_session(self.stop_event)
                elif runtimeglobals.run_mode == "Server":
                    try:
                        # TODO: Add actual connection logic later
                        print("[SERVER MODE] Attempting to connect to server...")
                        pinger = ServerPinger(runtimeglobals.server_url,runtimeglobals.secret_code)
                        #result = pinger.ping()
                        try:
                            result = pinger.ping()
                            print(result)
                            if result:  # Could be True or something valid
                                print("✅ Server reachable.")
                                server_available = True
                            else:
                                print("❌ Ping returned falsy result.")
                                server_available = False
                        except Exception as e:
                            print(f"❌ Exception while pinging server: {e}")
                            server_available = False
                        
                        if result:
                            server_available = True
                        if server_available:
                            print("server connected")
                            client = ServerClient(runtimeglobals.server_url, runtimeglobals.secret_code)
                            sys.modules["client"] = client
                            client.send_runtimeglobals()
                            client.start_main_coroutine()
                            asyncio.create_task(loop_fetch(client))

                        else:
                            print("[SERVER MODE] Server unavailable. Prompting user...")
                            def run_local_mode():
                                    print("[INFO] Starting local mode...")
                                    asyncio.run_coroutine_threadsafe(start_pure_websocket_session(self.stop_event), self.loop)
                            def do_nothing():
                                print("[INFO] User cancelled. Doing nothing.")
                            Clock.schedule_once(lambda dt: show_server_unreachable_popup(run_local_mode, do_nothing))
                            
                    except Exception as e:
                        print(f"[SERVER MODE] Exception occurred: {e}. Falling back to local.")
                        await start_pure_websocket_session(self.stop_event)
                else:
                    print(f"[WARNING] Unknown run mode: {runtimeglobals.run_mode}. Defaulting to local.")
                    await start_pure_websocket_session(self.stop_event)
            except Exception as e:
                print(f"❌ Exception in startup: {e}")

        # Create and track tasks
        task_startup = self.loop.create_task(startup())
        task_heartbeat = self.loop.create_task(heartbeat())
        task_monitor = self.loop.create_task(monitor_stop())

        self.tasks.extend([task_startup, task_heartbeat, task_monitor])  # Add tasks to the list

        self.loop.run_forever()



"""
import asyncio
import threading
from kivy.clock import Clock
from kivy.utils import platform
from botutils.analysis_runner import start_pure_websocket_session
from botutils import runtimeglobals

class BotRunner:
    def __init__(self, loop, stop_event):
        self.loop = loop
        self.stop_event = stop_event
        self.tasks = []  # Track tasks

    def run(self):
        print(f"[RUN] Loop ID: {id(self.loop)} | Thread: {threading.current_thread().name}")
        asyncio.set_event_loop(self.loop)

        async def heartbeat():
            while True:
                await asyncio.sleep(1)

        async def monitor_stop():
            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)
            print("[STOP] Stop event received. Shutting down loop.")
            # Cancel all tasks before stopping the loop
            for task in self.tasks:
                task.cancel()
            self.loop.stop()

        async def startup():
            try:
                await start_pure_websocket_session(self.stop_event)
            except Exception as e:
                print(f"❌ Exception in start_pure_websocket_session: {e}")

        # Create and track tasks
        task_startup = self.loop.create_task(startup())
        task_heartbeat = self.loop.create_task(heartbeat())
        task_monitor = self.loop.create_task(monitor_stop())

        self.tasks.extend([task_startup, task_heartbeat, task_monitor])  # Add tasks to the list

        self.loop.run_forever()
        
        """
