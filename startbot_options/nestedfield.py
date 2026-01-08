from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from startbot_options.checkbox_dropdown_field import CheckboxDropdown
from startbot_options.labeled_textfield import LabeledTextInput


class Nested(BoxLayout):
    def __init__(self, parent_config, children_config_map, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10), size_hint_y=None, padding=dp(10), **kwargs)
        self.bind(minimum_height=self.setter('height'))

        # Background styling
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 0.9)
            self.bg_rect = RoundedRectangle(radius=[dp(12)], pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Parent dropdown
        self.parent_dropdown = CheckboxDropdown(**parent_config)
        self.parent_dropdown.bind(on_select=self._on_parent_select)
        self.add_widget(self.parent_dropdown)

        # Store children config
        self.children_config_map = children_config_map
        self.active_children = []

        # Delay binding until dropdown is populated
        Clock.schedule_once(lambda dt: self._on_parent_select(None), 0)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _clear_children(self):
        for widget in self.active_children:
            self.remove_widget(widget)
        self.active_children.clear()

    def _on_parent_select(self, instance):
        self._clear_children()

        selected = self.parent_dropdown.get_selected()
        if not selected:
            return

        if isinstance(selected, str):  # single select
            selected_items = [selected]
        elif isinstance(selected, list):
            selected_items = selected
        else:
            return

        for item in selected_items:
            configs = self.children_config_map.get(item, [])
            for config in configs:
                if config["type"] == "textinput":
                    widget = LabeledTextInput(**config["kwargs"])
                elif config["type"] == "checkbox":
                    widget = CheckboxDropdown(**config["kwargs"])
                else:
                    continue
                self.active_children.append(widget)
                self.add_widget(widget)

    def get_values(self):
        values = {}
    
        # Get parent selection
        selected_parent = self.parent_dropdown.get_selected()
        values["parent"] = selected_parent
    
        # Get child values (only currently visible/active)
        children_values = {}
        for w in self.active_children:
            if isinstance(w, LabeledTextInput):
                children_values[w.label] = w.get_value()
            elif isinstance(w, CheckboxDropdown):
                children_values[w.label_text] = w.get_selected()
    
        values["children"] = children_values
        return values
    