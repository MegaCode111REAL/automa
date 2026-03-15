# Automa

Cross-platform desktop macro automation platform written in Python, with a modular architecture for recording, playback, editing, trigger-based automation, and image pattern detection.

## Features

- Keyboard/mouse macro recording with timing preservation.
- Playback engine with pause/resume, looping support, and emergency stop via `pyautogui` failsafe (top-left corner).
- Macro editor (add, delete, reorder, and edit actions as JSON).
- Group/profile management for organizing macros.
- Trigger system for hotkeys, active-window matching, timer intervals, and image detection.
- OpenCV-based template matching for screen pattern detection.
- Macro import/export via JSON files.
- Modular code layout for future extension (OCR, scripting, conditional logic, etc.).

## Project Structure

```text
automa/
  main.py
  gui/
    main_window.py
    macro_editor.py
    group_manager.py
  core/
    macro_engine.py
    macro_recorder.py
    macro_store.py
    trigger_system.py
    models.py
  modules/
    keyboard_controller.py
    mouse_controller.py
    screen_capture.py
    image_detection.py
  data/
    macros.json
requirements.txt
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Run

```bash
python -m automa.main
```

## JSON Macro Format

```json
{
  "name": "example_macro",
  "actions": [
    {"type": "mouse_move", "x": 300, "y": 200},
    {"type": "mouse_click", "button": "left"},
    {"type": "delay", "time": 0.3},
    {"type": "key_press", "key": "a"}
  ]
}
```

## Trigger Types

- `hotkey`: Global shortcut combo (e.g., `<ctrl>+<alt>+e`).
- `window_active`: Fires when active window title matches configured text.
- `timer`: Runs a macro every N seconds.
- `image_detect`: Runs when template matching passes threshold.

## Safety Features

- `pyautogui.FAILSAFE = True` (moving mouse to top-left can stop unsafe automation).
- Manual `Stop` and `Pause/Resume` controls in GUI.
- Trigger service can be started/stopped independently.

## Notes

- Global hooks (recording/hotkeys) may require elevated permissions on some Linux desktop environments.
- Wayland sessions can limit low-level input hooks/capture for some libraries.
