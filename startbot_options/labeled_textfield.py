from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock


class LabeledTextInput(BoxLayout):
    label = StringProperty("")
    input_type = ObjectProperty(str)
    min_value = ObjectProperty(None)
    max_value = ObjectProperty(None)
    default = StringProperty("")
    special = BooleanProperty(False)
    hidden = BooleanProperty(False)
    password = StringProperty("7564")

    def __init__(self, label="", input_type=str, min_value=None, max_value=None,
                 default="", special=False, hidden=False, password="7564", **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.label = label
        self.input_type = input_type
        self.min_value = min_value
        self.max_value = max_value
        self.default = default
        self.special = special
        self.hidden = hidden
        self.password = password

        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(40)

        self.label_widget = Label(
            text=self.label,
            size_hint_x=None,
            width=dp(100),
            halign="left",
            valign="middle",
        )
        self.label_widget.bind(size=self._update_label)

        hint_parts = [f"{input_type.__name__}"]
        if min_value is not None:
            hint_parts.append(f"≥{min_value}")
        if max_value is not None:
            hint_parts.append(f"≤{max_value}")

        # Main text input
        self.text_input = TextInput(
            multiline=False,
            size_hint_x=1,
            text=str(self.default),
            hint_text=" | ".join(hint_parts),
            padding=[dp(5), dp(5)],
            disabled=special,
            password=hidden
        )
        self.text_input.bind(text=self.on_text_change)

        if self.special:
            self.text_input.bind(on_touch_down=self.on_special_click)

        self.add_widget(self.label_widget)
        self.add_widget(self.text_input)

        # Toggle button for hidden fields
        if self.hidden:
            self.toggle_button = Button(
                text="🔒",
                size_hint_x=None,
                width=dp(40),
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=dp(18)
            )
            self.toggle_button.bind(on_release=self.show_toggle_password_prompt)
            self.add_widget(self.toggle_button)

        with self.text_input.canvas.after:
            self._error_color = Color(1, 0, 0, 0)
            self._error_rect = Rectangle(pos=self.text_input.pos, size=self.text_input.size)
        self.text_input.bind(pos=self._update_error_rect, size=self._update_error_rect)

    def _update_label(self, instance, size):
        instance.text_size = size

    def _update_error_rect(self, *args):
        self._error_rect.pos = self.text_input.pos
        self._error_rect.size = self.text_input.size

    def on_text_change(self, instance, value):
        if not value.strip():
            self._error_color.a = 0
            return

        try:
            val = self.input_type(value.strip())
            if isinstance(val, (int, float)):
                if (self.min_value is not None and val < self.min_value) or \
                   (self.max_value is not None and val > self.max_value):
                    raise ValueError
            self._error_color.a = 0
        except:
            self._error_color.a = 0.8

    def get_value(self):
        raw_text = self.text_input.text.strip()
        try:
            value = self.input_type(raw_text)
            if isinstance(value, (int, float)):
                if self.min_value is not None and value < self.min_value:
                    raise ValueError(f"Below min: {self.min_value}")
                if self.max_value is not None and value > self.max_value:
                    raise ValueError(f"Above max: {self.max_value}")
            return value
        except:
            self._error_color.a = 0.8
            return None

    def on_special_click(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.text_input.disabled:
            self.show_password_prompt()

    def show_password_prompt(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        password_input = TextInput(password=True, hint_text="Enter password", multiline=False)

        def try_unlock(instance):
            if password_input.text == self.password:
                self.text_input.disabled = False
                self.popup.dismiss()
                Clock.schedule_once(lambda dt: setattr(self.text_input, 'disabled', True), 10)
            else:
                password_input.text = ""
                password_input.hint_text = "Wrong password!"

        unlock_btn = Button(text="Unlock", size_hint_y=None, height=dp(40), background_color=(0.2, 0.6, 0.2, 1))
        unlock_btn.bind(on_release=try_unlock)

        cancel_btn = Button(text="X", size_hint=(None, None), size=(dp(30), dp(30)))
        cancel_btn.bind(on_release=lambda x: self.popup.dismiss())

        top_row = BoxLayout(size_hint_y=None, height=dp(30))
        top_row.add_widget(cancel_btn)

        layout.add_widget(top_row)
        layout.add_widget(password_input)
        layout.add_widget(unlock_btn)

        self.popup = Popup(title="Unlock Input", content=layout, size_hint=(None, None), size=(dp(250), dp(200)))
        self.popup.open()

    def show_toggle_password_prompt(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        password_input = TextInput(password=True, hint_text="Enter password", multiline=False)

        def try_toggle(instance):
            if password_input.text == self.password:
                self.text_input.password = not self.text_input.password
                self.toggle_button.text = "🔓" if not self.text_input.password else "🔒"
                self.popup.dismiss()
            else:
                password_input.text = ""
                password_input.hint_text = "Wrong password!"

        toggle_btn = Button(text="Toggle", size_hint_y=None, height=dp(40), background_color=(0.2, 0.6, 0.2, 1))
        toggle_btn.bind(on_release=try_toggle)

        cancel_btn = Button(text="X", size_hint=(None, None), size=(dp(30), dp(30)))
        cancel_btn.bind(on_release=lambda x: self.popup.dismiss())

        top_row = BoxLayout(size_hint_y=None, height=dp(30))
        top_row.add_widget(cancel_btn)

        layout.add_widget(top_row)
        layout.add_widget(password_input)
        layout.add_widget(toggle_btn)

        self.popup = Popup(title="Toggle Password", content=layout, size_hint=(None, None), size=(dp(250), dp(200)))
        self.popup.open()

        
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock  

class LabeledTextInput(BoxLayout):
    label = StringProperty("")
    input_type = ObjectProperty(str)
    min_value = ObjectProperty(None)
    max_value = ObjectProperty(None)
    default = StringProperty("")
    special = BooleanProperty(False)
    hidden = BooleanProperty(False)
    password = StringProperty("7564")

    def __init__(self, label="", input_type=str, min_value=None, max_value=None,
                 default="", special=False, hidden=False, password="7564", **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.label = label
        self.input_type = input_type
        self.min_value = min_value
        self.max_value = max_value
        self.default = default
        self.special = special
        self.hidden = hidden
        self.password = password

        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(40)

        self.label_widget = Label(
            text=self.label,
            size_hint_x=None,
            width=dp(100),
            halign="left",
            valign="middle",
        )
        self.label_widget.bind(size=self._update_label)

        hint_parts = [f"{input_type.__name__}"]
        if min_value is not None:
            hint_parts.append(f"≥{min_value}")
        if max_value is not None:
            hint_parts.append(f"≤{max_value}")

        # Main text input
        self.text_input = TextInput(
            multiline=False,
            size_hint_x=1,
            text=str(self.default),
            hint_text=" | ".join(hint_parts),
            padding=[dp(5), dp(5)],
            disabled=special,
            password=hidden
        )
        self.text_input.bind(text=self.on_text_change)

        # If special, bind unlock trigger
        if self.special:
            self.text_input.bind(on_touch_down=self.on_special_click)

        self.add_widget(self.label_widget)
        self.add_widget(self.text_input)

        # Toggle button for hidden fields
        if self.hidden:
            self.toggle_button = Button(
                text="[LCK]",
                size_hint_x=None,
                width=dp(40),
                background_normal='',
                background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=dp(18)
            )
            self.toggle_button.bind(on_release=self.show_toggle_password_prompt)
            self.add_widget(self.toggle_button)

        with self.text_input.canvas.after:
            self._error_color = Color(1, 0, 0, 0)
            self._error_rect = Rectangle(pos=self.text_input.pos, size=self.text_input.size)
        self.text_input.bind(pos=self._update_error_rect, size=self._update_error_rect)

    def _update_label(self, instance, size):
        instance.text_size = size

    def _update_error_rect(self, *args):
        self._error_rect.pos = self.text_input.pos
        self._error_rect.size = self.text_input.size

    def on_text_change(self, instance, value):
        if not value.strip():
            self._error_color.a = 0
            return

        try:
            val = self.input_type(value.strip())
            if isinstance(val, (int, float)):
                if (self.min_value is not None and val < self.min_value) or \
                   (self.max_value is not None and val > self.max_value):
                    raise ValueError
            self._error_color.a = 0
        except:
            self._error_color.a = 0.8

    def get_value(self):
        raw_text = self.text_input.text.strip()
        try:
            value = self.input_type(raw_text)
            if isinstance(value, (int, float)):
                if self.min_value is not None and value < self.min_value:
                    raise ValueError(f"Below min: {self.min_value}")
                if self.max_value is not None and value > self.max_value:
                    raise ValueError(f"Above max: {self.max_value}")
            return value
        except:
            self._error_color.a = 0.8
            return None

    def on_special_click(self, instance, touch):
        if instance.collide_point(*touch.pos) and self.text_input.disabled:
            self.show_password_prompt()

    def show_password_prompt(self):
        layout = FloatLayout()

        password_input = TextInput(
            password=True, multiline=False,
            size_hint=(0.6, None), height=dp(40),
            pos_hint={"center_x": 0.5, "center_y": 0.6}
        )

        submit_btn = Button(
            text="Unlock", size_hint=(0.4, None), height=dp(40),
            pos_hint={"center_x": 0.5, "center_y": 0.4}
        )

        close_btn = Button(
            text="X", size_hint=(None, None), size=(dp(30), dp(30)),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal='', background_color=(1, 0, 0, 1),
            font_size=dp(18)
        )

        popup = Popup(
            title="Enter Password",
            content=layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )

        def on_submit(instance):
            if password_input.text == self.password:
                self.text_input.disabled = False
                popup.dismiss()
                Clock.schedule_once(lambda dt: setattr(self.text_input, 'disabled', True), 10)
            else:
                password_input.text = ""
                password_input.hint_text = "Wrong password"

        submit_btn.bind(on_release=on_submit)
        close_btn.bind(on_release=popup.dismiss)

        layout.add_widget(password_input)
        layout.add_widget(submit_btn)
        layout.add_widget(close_btn)
        popup.open()

    def show_toggle_password_prompt(self, instance):
        layout = FloatLayout()

        password_input = TextInput(
            password=True, multiline=False,
            size_hint=(0.6, None), height=dp(40),
            pos_hint={"center_x": 0.5, "center_y": 0.6}
        )

        submit_btn = Button(
            text="Toggle", size_hint=(0.4, None), height=dp(40),
            pos_hint={"center_x": 0.5, "center_y": 0.4}
        )

        close_btn = Button(
            text="X", size_hint=(None, None), size=(dp(30), dp(30)),
            pos_hint={"right": 0.98, "top": 0.98},
            background_normal='', background_color=(1, 0, 0, 1),
            font_size=dp(18)
        )

        popup = Popup(
            title="Unlock Visibility",
            content=layout,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )

        def on_submit(instance):
            if password_input.text == self.password:
                self.text_input.password = not self.text_input.password
                self.toggle_button.text = "🔓" if not self.text_input.password else "🔒"
                popup.dismiss()
            else:
                password_input.text = ""
                password_input.hint_text = "Wrong password"

        submit_btn.bind(on_release=on_submit)
        close_btn.bind(on_release=popup.dismiss)

        layout.add_widget(password_input)
        layout.add_widget(submit_btn)
        layout.add_widget(close_btn)
        popup.open()
    
"""
    
    
    