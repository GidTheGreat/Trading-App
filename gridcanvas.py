#gridcanvas.py
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Rectangle, InstructionGroup
from kivy.metrics import dp




class GridCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Background
        with self.canvas.before:
            self.bg_color = Color(0, 0, 0, 0.2)  # Pure black background
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        # Grid lines
        self.grid_group = InstructionGroup()
        self.canvas.before.add(self.grid_group)

        # Redraw on size/position change
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, *args):
        # Update background rectangle
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        # Draw grid lines
        self.grid_group.clear()
        self.grid_group.add(Color(0.3, 0.3, 0.3, 0.3))  # Soft gray grid lines

        step_x = dp(40)
        step_y = dp(40)
        width = int(self.width)
        height = int(self.height)

        for x in range(0, width, int(step_x)):
            self.grid_group.add(Line(points=[self.x + x, self.y, self.x + x, self.y + height], width=1))

        for y in range(0, height, int(step_y)):
            self.grid_group.add(Line(points=[self.x, self.y + y, self.x + width, self.y + y], width=1))

