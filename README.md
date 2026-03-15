# automa

Cross-platform desktop macro automation platform written in Python, with a modular architecture for recording, playback, editing, trigger-based automation, and image pattern detection.

## Get the app (recommended)

For normal use, **download the latest release for your OS and run it**:

1. Go to this repository's **Releases** page.
2. Download the newest asset for your platform:
   - Windows
   - Linux
   - macOS
3. Run the application bundle/executable.

> This is the primary install path. Most users should not need to run from source.

## First launch permissions (shown in-app)

On first launch, automa shows OS-specific setup instructions for required permissions:

- **Windows**: desktop/input access, and run as Administrator only if hooks fail.
- **Linux**: X11 recommended; Wayland may block global hooks depending on compositor policy.
- **macOS**: enable automa in **Accessibility**, **Input Monitoring**, and **Screen Recording**.

## macOS support

automa supports macOS in addition to Windows and Linux. The app includes first-launch guidance for macOS privacy permissions required for automation and screen capture.

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
    app_settings.py
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

## Developer setup (source)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
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
