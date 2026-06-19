import math
import threading
import time
import tkinter as tk
from tkinter import ttk

import numpy as np
import pyperclip
import keyboard
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

BG = "#0b0f1a"
PANEL = "#141a2a"
PANEL_LIGHT = "#1b2333"
ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
TEXT = "#e5e7eb"
SUBTEXT = "#8b93a7"
BORDER = "#252e44"


# ---------------------------------------------------------------------------
# Ring geometry
# ---------------------------------------------------------------------------

class RingParams:

    def __init__(self, center, radius, segments, thickness, height):
        self.center = center
        self.radius = radius
        self.segments = segments
        self.thickness = thickness   
        self.height = height         

    @property
    def outer_radius(self):
        return self.radius + self.thickness / 2

    @property
    def tangential_width(self):
        half_thickness = self.thickness / 2
        width = 2 * self.outer_radius * math.sin(math.pi / self.segments)

        for _ in range(8):
            half_width = width / 2
            corner_radius = math.hypot(self.radius + half_thickness, half_width)
            width = 2 * corner_radius * math.sin(math.pi / self.segments)

        return width

    def segment_position(self, index):
        angle = 2 * math.pi * index / self.segments
        cx, cy, cz = self.center
        x = cx + self.radius * math.cos(angle)
        z = cz + self.radius * math.sin(angle)
        y = cy
        return (x, y, z), angle


def read_ring_params(center_entry, radius_entry, segments_entry,
                      thickness_entry, height_entry):
    try:
        cx, cy, cz = map(float, center_entry.get().split(","))
        radius = float(radius_entry.get())
        segments = int(segments_entry.get())
        thickness = float(thickness_entry.get())
        height = float(height_entry.get())
        if segments < 3 or radius <= 0:
            return None
        return RingParams((cx, cy, cz), radius, segments, thickness, height)
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# 3D preview helpers
# ---------------------------------------------------------------------------

def cuboid_faces(center, size, facing_angle):
    cx, cy, cz = center
    sx, sy, sz = size
    hx, hy, hz = sx / 2, sy / 2, sz / 2

    corners = np.array([
        [-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
        [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz],
    ])

    c, s = math.cos(facing_angle), math.sin(facing_angle)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    world = corners @ rotation.T + np.array([cx, cy, cz])

    face_indices = [
        [0, 1, 2, 3], [4, 5, 6, 7],
        [0, 1, 5, 4], [2, 3, 7, 6],
        [1, 2, 6, 5], [0, 3, 7, 4],
    ]
    return [[world[i] for i in face] for face in face_indices]


def draw_ring_preview(ax, params):
    ax.clear()
    ax.set_facecolor(BG)

    cx, cy, cz = params.center
    width = params.tangential_width
    axis_len = params.radius + 5

    ax.plot([cx - axis_len, cx + axis_len], [cy, cy], [cz, cz], color="#ef4444", linewidth=0.8)
    ax.plot([cx, cx], [cy - axis_len, cy + axis_len], [cz, cz], color="#22c55e", linewidth=0.8)
    ax.plot([cx, cx], [cy, cy], [cz - axis_len, cz + axis_len], color="#3b82f6", linewidth=0.8)

    for i in range(params.segments):
        (px, py, pz), angle = params.segment_position(i)
        size = (params.thickness, params.height, width)
        faces = cuboid_faces((px, py, pz), size, -angle)

        poly = Poly3DCollection(faces, alpha=0.8, edgecolor="#c7d2fe", linewidth=0.4)
        poly.set_facecolor((0.39, 0.4, 0.95, 0.75))
        ax.add_collection3d(poly)

    pad = params.radius + max(params.thickness, 5)
    ax.set_xlim(cx - pad, cx + pad)
    ax.set_ylim(cy - params.height - 5, cy + params.height + 5)
    ax.set_zlim(cz - pad, cz + pad)
    ax.set_box_aspect([1, 1, 1])

    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_facecolor((0.08, 0.1, 0.16, 1))
    ax.tick_params(colors=SUBTEXT)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.label.set_color(SUBTEXT)


# ---------------------------------------------------------------------------
# Command generation
# ---------------------------------------------------------------------------

def build_commands(params, world_id=1):
    width = params.tangential_width
    lines = []

    for i in range(params.segments):
        (px, py, pz), angle = params.segment_position(i)
        facing_deg = (360 - math.degrees(angle)) % 360

        lines.append(f"create {world_id} part {px:.3f} {py:.3f} {pz:.3f}")
        lines.append(f"size {world_id} % {params.thickness:.3f} {params.height:.3f} {width:.3f}")
        lines.append(f"move {world_id} % {px:.3f} {py:.3f} {pz:.3f} 0.000 {facing_deg:.3f} 0.000")

    return lines


# ---------------------------------------------------------------------------
# Console pasting
# ---------------------------------------------------------------------------

class ConsoleTyper:

    def __init__(self):
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def run(self, lines, delay_seconds, start_delay=2.0):
        self.stop_flag = False
        time.sleep(start_delay)

        for raw_line in lines:
            if self.stop_flag:
                break

            line = raw_line.strip()
            if not line:
                continue

            self._send_line(line)
            time.sleep(delay_seconds)

    @staticmethod
    def _send_line(line):
        pyperclip.copy(line)

        keyboard.press("ctrl")
        time.sleep(0.02)
        keyboard.press_and_release("a")
        time.sleep(0.02)
        keyboard.release("ctrl")
        time.sleep(0.02)

        keyboard.press_and_release("delete")
        time.sleep(0.02)

        keyboard.press_and_release("ctrl+v")
        time.sleep(0.02)

        keyboard.press_and_release("enter")


def hotkey_listener(get_lines, get_delay, typer):
    while True:
        if keyboard.is_pressed("f1"):
            lines = get_lines()
            if lines:
                threading.Thread(
                    target=typer.run,
                    args=(lines, get_delay()),
                    daemon=True,
                ).start()
            time.sleep(1)

        if keyboard.is_pressed("f2"):
            typer.stop()
            time.sleep(0.3)

        time.sleep(0.05)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class RingBuilderApp:
    def __init__(self, root):
        self.root = root
        self.typer = ConsoleTyper()
        self.current_lines = []

        self._configure_style()
        self._build_layout()
        self._build_figure()

        threading.Thread(
            target=hotkey_listener,
            args=(lambda: self.current_lines, lambda: self.delay_var.get(), self.typer),
            daemon=True,
        ).start()

        self._refresh_loop()

    #styling 

    def _configure_style(self):
        self.root.title("Cuboid Ring Builder")
        self.root.geometry("1280x760")
        self.root.configure(bg=BG)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)

        style.configure(
            "TEntry",
            fieldbackground=PANEL_LIGHT,
            foreground=TEXT,
            bordercolor=BORDER,
            insertcolor=TEXT,
            padding=6,
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="white",
            borderwidth=0,
            padding=(14, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])

        style.configure(
            "Title.TLabel",
            background=PANEL,
            foreground=TEXT,
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "FieldLabel.TLabel",
            background=PANEL,
            foreground=SUBTEXT,
            font=("Segoe UI", 9, "bold"),
        )

    #layout

    def _build_layout(self):
        sidebar = ttk.Frame(self.root, style="Panel.TFrame", padding=16)
        sidebar.pack(side="left", fill="y")

        ttk.Label(sidebar, text="Ring Builder", style="Title.TLabel").pack(
            anchor="w", pady=(0, 16)
        )

        self.center_entry = self._field(sidebar, "Center (x, y, z)", "0,0,0")
        self.radius_entry = self._field(sidebar, "Radius", "10")
        self.segments_entry = self._field(sidebar, "Segments", "32")
        self.thickness_entry = self._field(sidebar, "Thickness", "1")
        self.height_entry = self._field(sidebar, "Height", "1")

        ttk.Label(sidebar, text="Command Delay (s)", style="FieldLabel.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.delay_var = tk.DoubleVar(value=0.01)
        ttk.Entry(sidebar, textvariable=self.delay_var, style="TEntry", width=28).pack(
            fill="x", pady=(0, 16)
        )

        ttk.Button(
            sidebar, text="Generate", style="Accent.TButton", command=self._generate
        ).pack(fill="x")

        ttk.Label(sidebar, text="Output", style="FieldLabel.TLabel").pack(
            anchor="w", pady=(16, 4)
        )
        self.output_text = tk.Text(
            sidebar,
            height=16,
            width=32,
            bg=PANEL_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            wrap="none",
        )
        self.output_text.pack(fill="both", expand=True)

        self.preview_frame = ttk.Frame(self.root)
        self.preview_frame.pack(side="right", fill="both", expand=True)

    def _field(self, parent, label, default):
        ttk.Label(parent, text=label, style="FieldLabel.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        entry = ttk.Entry(parent, style="TEntry", width=28)
        entry.insert(0, default)
        entry.pack(fill="x", pady=(0, 12))
        return entry

    def _build_figure(self):
        self.fig = plt.figure(facecolor=BG)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.preview_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    #actions

    def _current_params(self):
        return read_ring_params(
            self.center_entry, self.radius_entry, self.segments_entry,
            self.thickness_entry, self.height_entry,
        )

    def _generate(self):
        params = self._current_params()
        self.output_text.delete("1.0", tk.END)

        if params is None:
            self.current_lines = []
            return

        self.current_lines = build_commands(params)
        self.output_text.insert(tk.END, "\n".join(self.current_lines))

    def _refresh_loop(self):
        params = self._current_params()
        if params is not None:
            draw_ring_preview(self.ax, params)
            self.canvas.draw_idle()
        self.root.after(200, self._refresh_loop)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    RingBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()