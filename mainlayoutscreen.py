from kivy.uix.screenmanager import Screen
from mainlayout import MainLayout



class MainLayoutScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(MainLayout())

