from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.event import EventDispatcher
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock


class StyledDropDown(DropDown):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            self.bg_rect = RoundedRectangle(radius=[10], size=self.size, pos=self.pos)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos



class CheckboxDropdown(BoxLayout):
    def __init__(self, label="Select:", options=None, default_selected=None,
                 multiselect=True, preview_selected=True, special=False, **kwargs):

        self.register_event_type('on_select')
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10), **kwargs)

        self.label_text = label
        self.options = options or []
        self.default_selected = default_selected or []
        self.multiselect = multiselect
        self.preview_selected = preview_selected
        self.special = special
        self.locked = special
        self.unlock_timer = None
        self.selected_options = {}

        # Label on the left
        self.label_widget = Label(
            text=self.label_text,
            size_hint_x=None,
            width=dp(100),
            halign="left",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        self.label_widget.bind(size=self._update_label_text_size)
        self.add_widget(self.label_widget)

        # Dropdown & scrollable content
        self.dropdown = StyledDropDown(auto_width=False, size_hint=(None, None))
        self.dropdown.width = dp(200)

        scroll_view = ScrollView(size_hint=(1, None), height=dp(3 * 40))
        self.option_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(5))
        self.option_layout.bind(minimum_height=self.option_layout.setter('height'))
        scroll_view.add_widget(self.option_layout)
        self.dropdown.add_widget(scroll_view)

        # "Select All" row
        if self.multiselect:
            self.select_all_checkbox = CheckBox(size_hint=(None, None), size=(dp(25), dp(25)))
            self.select_all_checkbox.bind(active=self._on_select_all_toggle)

            select_all_label = Label(
                text="Select All",
                size_hint_x=1,
                halign="left",
                valign="middle",
                color=(1, 1, 1, 1)
            )
            select_all_label.bind(size=self._update_label_text_size)

            select_all_row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                padding=[dp(10), 0],
                spacing=dp(10)
            )
            select_all_row.add_widget(self.select_all_checkbox)
            select_all_row.add_widget(select_all_label)
            self.option_layout.add_widget(select_all_row)

        # Individual options
        for option in self.options:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                padding=[dp(10), 0],
                spacing=dp(10)
            )
            checkbox = CheckBox(size_hint=(None, None), size=(dp(25), dp(25)))
            if option in self.default_selected:
                checkbox.active = True

            def on_checkbox_change(cb, value, opt=option):
                if not self.multiselect and value:
                    for other, cbx in self.selected_options.items():
                        if other != opt:
                            cbx.active = False
                    self.dropdown.dismiss()

                if self.multiselect and self.select_all_checkbox:
                    self._sync_select_all_state()

                if self.preview_selected:
                    self._update_main_button_text()
                self.dispatch("on_select")

            checkbox.bind(active=on_checkbox_change)
            self.selected_options[option] = checkbox

            label = Label(
                text=option,
                size_hint_x=1,
                halign="left",
                valign="middle",
                color=(1, 1, 1, 1)
            )
            label.bind(size=self._update_label_text_size)

            row.add_widget(checkbox)
            row.add_widget(label)
            self.option_layout.add_widget(row)

        # Dropdown open button
        self.main_button = Button(
            text=self._get_preview_text(),
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.4, 0.6, 1),
            color=(1, 1, 1, 1)
        )
        self.main_button.bind(on_release=self._on_main_button_click)
        self.add_widget(self.main_button)

    def on_select(self, *args):
        pass

    def _update_label_text_size(self, label, size):
        label.text_size = size

    def _get_preview_text(self):
        if not self.preview_selected:
            return "Select Options"
        selected = self.get_selected()
        return ", ".join(selected) if selected else "Select Options"

    def _update_main_button_text(self):
        self.main_button.text = self._get_preview_text()

    def get_selected(self):
        return [text for text, cb in self.selected_options.items() if cb.active]

    def _on_select_all_toggle(self, instance, value):
        for opt, cb in self.selected_options.items():
            cb.unbind(active=self._sync_select_all_state)
            cb.active = value
            cb.bind(active=self._wrap_checkbox_change(opt))
        if self.preview_selected:
            self._update_main_button_text()

    def _sync_select_all_state(self, *args):
        if self.select_all_checkbox:
            all_selected = all(cb.active for cb in self.selected_options.values())
            self.select_all_checkbox.unbind(active=self._on_select_all_toggle)
            self.select_all_checkbox.active = all_selected
            self.select_all_checkbox.bind(active=self._on_select_all_toggle)

    def _wrap_checkbox_change(self, option):
        def wrapped(cb, value):
            if self.multiselect and self.select_all_checkbox:
                self._sync_select_all_state()
            if self.preview_selected:
                self._update_main_button_text()
            self.dispatch("on_select")
        return wrapped

    def _on_main_button_click(self, instance):
        if self.special and self.locked:
            self._show_unlock_popup()
        else:
            self.dropdown.open(instance)

    def _show_unlock_popup(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        password_input = TextInput(password=True, hint_text="Enter password", multiline=False)

        def try_unlock(instance):
            if password_input.text == "7564":  # Change to dynamic or secure logic
                self.locked = False
                self.popup.dismiss()
                self.dropdown.open(self.main_button)
                self._start_relock_timer()
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

        self.popup = Popup(title="Unlock Dropdown", content=layout, size_hint=(None, None), size=(dp(250), dp(200)))
        self.popup.open()

    def _start_relock_timer(self):
        if self.unlock_timer:
            self.unlock_timer.cancel()
        self.unlock_timer = Clock.schedule_once(lambda dt: self._relock(), 10)

    def _relock(self):
        if self.special:
            self.locked = True
            
            
            
            
            
"""
class CheckboxDropdown(BoxLayout):
    def __init__(self, label="Select:", options=None, default_selected=None,
                 multiselect=True, preview_selected=True, **kwargs):
                     
        self.register_event_type('on_select')
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10), **kwargs)

        self.label_text = label
        self.options = options or []
        self.default_selected = default_selected or []
        self.multiselect = multiselect
        self.preview_selected = preview_selected
        self.selected_options = {}

        # Label on the left
        self.label_widget = Label(
            text=self.label_text,
            size_hint_x=None,
            width=dp(100),
            halign="left",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        self.label_widget.bind(size=self._update_label_text_size)
        self.add_widget(self.label_widget)

        # Dropdown & scrollable content
        self.dropdown = StyledDropDown(auto_width=False, size_hint=(None, None))
        self.dropdown.width = dp(200)

        scroll_view = ScrollView(size_hint=(1, None), height=dp(3 * 40))  # Max 3 items visible
        self.option_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=dp(5))
        self.option_layout.bind(minimum_height=self.option_layout.setter('height'))
        scroll_view.add_widget(self.option_layout)
        self.dropdown.add_widget(scroll_view)

        # "Select All" row (if multiselect)
        if self.multiselect:
            self.select_all_checkbox = CheckBox(size_hint=(None, None), size=(dp(25), dp(25)))
            self.select_all_checkbox.bind(active=self._on_select_all_toggle)

            select_all_label = Label(
                text="Select All",
                size_hint_x=1,
                halign="left",
                valign="middle",
                color=(1, 1, 1, 1)
            )
            select_all_label.bind(size=self._update_label_text_size)

            select_all_row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                padding=[dp(10), 0],
                spacing=dp(10)
            )
            select_all_row.add_widget(self.select_all_checkbox)
            select_all_row.add_widget(select_all_label)
            self.option_layout.add_widget(select_all_row)

        # Individual checkboxes
        for option in self.options:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                padding=[dp(10), 0],
                spacing=dp(10)
            )
            checkbox = CheckBox(size_hint=(None, None), size=(dp(25), dp(25)))
            if option in self.default_selected:
                checkbox.active = True

            def on_checkbox_change(cb, value, opt=option):
                if not self.multiselect and value:
                    for other, cbx in self.selected_options.items():
                        if other != opt:
                            cbx.active = False
                    self.dropdown.dismiss()

                if self.multiselect and self.select_all_checkbox:
                    self._sync_select_all_state()

                if self.preview_selected:
                    self._update_main_button_text()
                self.dispatch("on_select")
                

            checkbox.bind(active=on_checkbox_change)
            self.selected_options[option] = checkbox

            label = Label(
                text=option,
                size_hint_x=1,
                halign="left",
                valign="middle",
                color=(1, 1, 1, 1)
            )
            label.bind(size=self._update_label_text_size)

            row.add_widget(checkbox)
            row.add_widget(label)
            self.option_layout.add_widget(row)

        # Dropdown open button (with ▼ hint)
        self.main_button = Button(
            text=self._get_preview_text(),        
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.4, 0.6, 1),
            color=(1, 1, 1, 1)
        )
        self.main_button.bind(on_release=self.dropdown.open)
        self.add_widget(self.main_button)

    def on_select(self, *args):
        pass  # This just makes the event bindable
        
    def _update_label_text_size(self, label, size):
        label.text_size = size

    def _get_preview_text(self):
        if not self.preview_selected:
            return "Select Options"
        selected = self.get_selected()
        return ", ".join(selected) if selected else "Select Options"

    def _update_main_button_text(self):
        self.main_button.text = self._get_preview_text()

    def get_selected(self):
        return [text for text, cb in self.selected_options.items() if cb.active]

    def _on_select_all_toggle(self, instance, value):
        # Called when "Select All" is toggled
        for opt, cb in self.selected_options.items():
            cb.unbind(active=self._sync_select_all_state)  # Avoid recursion
            cb.active = value
            cb.bind(active=self._wrap_checkbox_change(opt))  # Rebind safely

        if self.preview_selected:
            self._update_main_button_text()

    def _sync_select_all_state(self):
        if self.select_all_checkbox:
            all_selected = all(cb.active for cb in self.selected_options.values())
            self.select_all_checkbox.unbind(active=self._on_select_all_toggle)
            self.select_all_checkbox.active = all_selected
            self.select_all_checkbox.bind(active=self._on_select_all_toggle)

    def _wrap_checkbox_change(self, option):
        def wrapped(cb, value):
            if self.multiselect and self.select_all_checkbox:
                self._sync_select_all_state()
            if self.preview_selected:
                self._update_main_button_text()
            self.dispatch("on_select")
        return wrapped
        
        

"""        
        