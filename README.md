# BHRM-Ring-Generator
Generates rings in BHRM5 by geneating rge commands and pasting them into the RGE console. The thickness, origin, radius, world number, and poly count of the ring can be tweaked by the user in a GUI

## Requirements

- Python 3.9 or newer
- Tkinter (usually bundled with Python - see note below if it's missing)
- The packages listed in `requirements.txt`:
  - `numpy` - vector math for cuboid corners and rotation
  - `matplotlib` - the live 3D preview
  - `pyperclip` - copies each command line to the clipboard before pasting
  - `keyboard` - global F1/F2 hotkeys and simulated key presses

### Installing

```bash
pip install numpy matplotlib pyperclip keyboard
```

```bash
sudo apt install python3-tk
```

**Keyboard note:** the `keyboard` library needs elevated permissions on
Linux/macOS to listen for global hotkeys and simulate key presses. On
Windows it generally works without extra setup. On Linux you may need to
run the script with `sudo`, and on macOS you'll need to grant the terminal
Accessibility/Input Monitoring permissions in System Settings.

## Running it

```bash
python ring_builder.py
```

## Using it

1. Set the center, radius, segment count, thickness, and height.
2. Click **Generate** to fill the output box with the console commands and
   update the 3D preview.
3. Go into the RGE console and ensure you are typing on it, then press **F1** to start typing the
   commands in (there's a 2 second delay first so you have time to click
   into the right window). Press **F2** at any point to kill the code.
4. The "Command Delay" field controls how long it waits between lines -
   raise it if the game console can't keep up.

## Acknowledgments
Portions of this code were developed with assistance from Claude (Anthropic).
