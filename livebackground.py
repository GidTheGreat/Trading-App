from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, InstructionGroup
from kivy.clock import Clock
from random import uniform
from math import hypot

class Particle:
    def __init__(self, x, y, radius=5):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = uniform(-0.5, 0.5)
        self.vy = uniform(-0.5, 0.5)

    def update(self, width, height):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > width:
            self.vx *= -1
        if self.y < 0 or self.y > height:
            self.vy *= -1

class Ripple:
    def __init__(self, pos):
        self.x, self.y = pos
        self.radius = 0
        self.alpha = 0.5

    def update(self):
        self.radius += 10
        self.alpha -= 0.02
        return self.alpha > 0

class LiveBackground(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = [Particle(uniform(0, self.width), uniform(0, self.height)) for _ in range(40)]
        self.ripples = []
        Clock.schedule_interval(self.animate, 1/60)

    def on_size(self, *args):
        # Reposition particles on resize
        self.particles = [Particle(uniform(0, self.width), uniform(0, self.height)) for _ in range(40)]

    def on_touch_down(self, touch):
        self.ripples.append(Ripple(touch.pos))

    def animate(self, dt):
        self.canvas.clear()
        with self.canvas:
            # Draw drifting particles
            for p in self.particles:
                p.update(self.width, self.height)
                Color(0.4, 0.8, 1, 0.8)
                Ellipse(pos=(p.x - p.radius, p.y - p.radius), size=(p.radius*2, p.radius*2))

            # Draw neural connections
            for i, p1 in enumerate(self.particles):
                for j in range(i+1, len(self.particles)):
                    p2 = self.particles[j]
                    dist = hypot(p1.x - p2.x, p1.y - p2.y)
                    if dist < 100:
                        alpha = max(0, 1 - dist / 100)
                        Color(0.6, 1, 0.9, alpha * 0.3)
                        Line(points=[p1.x, p1.y, p2.x, p2.y], width=1)

            # Draw touch ripples
            updated_ripples = []
            for ripple in self.ripples:
                if ripple.update():
                    Color(0.3, 0.7, 1, ripple.alpha)
                    Line(circle=(ripple.x, ripple.y, ripple.radius), width=2)
                    updated_ripples.append(ripple)
            self.ripples = updated_ripples

class AliveApp(App):
    def build(self):
        return LiveBackground()

#AliveApp().run()