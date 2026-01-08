import traceback
from kivy.uix.label import Label
from kivy.app import App
from kivy.utils import platform

def log_crash(error_text):
    try:
        from kivy.app import App
        path = App.get_running_app().user_data_dir
    except:
        import os
        path = os.getcwd()  # fallback for very early errors

    try:
        from telegram import send_telegram_message
        with open(f"{path}/kivlog.txt", "w") as f:
            f.write(error_text)
            send_telegram_message(error_text)
    except Exception as e:
        print("Could not write crash log:", e)

try:
    # -------------------------
    # 🔽 ALL YOUR APP CODE HERE
    # -------------------------

    import kivycompatibility
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from logoscreen import LogoScreen
    #from mainlayoutscreen import MainLayoutScreen
    from startbot_options.setupbot import SetupScreen


    class UIApp(App):
        def build(self):
            sm = ScreenManager()

            logo_screen = LogoScreen(name='logo')
            #main_screen = MainLayoutScreen(name='main')
            setup_screen = SetupScreen(name='setup')

            sm.add_widget(logo_screen)
            #sm.add_widget(main_screen)
            sm.add_widget(setup_screen)

            sm.current = 'logo'  # Show logo screen first
            return sm


    UIApp().run()

except Exception:
    # -------------------------
    # 🔥 Catch anything above
    # -------------------------
    error_text = traceback.format_exc()
    print("Crash detected:\n", error_text)
    log_crash(error_text)

    class CrashApp(App):
        def build(self):
            return Label(text=f"❌ Crash:\n{error_text[:500]}", font_size=12)

    CrashApp().run()
