# automa

Cross-platform desktop macro automation tool with setup-based organization and dedicated macro editor windows.

## Get the app (recommended)

Download the latest release for your OS and run it:

1. Open the repository Releases page.
2. Download the newest build for Windows, Linux, or macOS.
3. Launch the app.

## UI structure

- **Main window (Setup List View)**: heading `Setups`, buttons `New / Delete / Rename / Import / Export`, and setup rows with active checkbox, setup name, author, and right arrow.
- **Main window (Setup Editor View)**: selected setup title, buttons `New / Delete / Rename / Export`, and macro list (`Keybind` + macro name).
- **Macro Editor Window** (separate window): macro name, buttons `Add / Delete / Record-Stop / Save / Export`, draggable event list, and editable Event Properties panel.

## File formats

- `.ats` = automa setup file (`name`, `author`, `macros[]`)
- `.atm` = automa macro file (`name`, `author`, `events[]`)

Drag-and-drop `.ats` and `.atm` files onto the main window behaves the same as Import.

## Developer run

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m automa.main
```
