import pyautogui
import time
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard as pynput_keyboard

running = False
hotkey_listener = None
capture_listener = None

MAX_ALLOWED = 100

pyautogui.FAILSAFE = True  # emergency stop: move mouse to top-left corner


# -----------------------------
# Auto typing logic
# -----------------------------

def set_status(text):
    app.after(0, lambda: status_label.config(text=text))


def send_line(text):
    pyautogui.write(text, interval=0.01)
    pyautogui.press("enter")


def run_typer():
    global running

    text = text_entry.get().strip()
    buy_text = buy_entry.get().strip()

    try:
        delay = float(delay_entry.get())
        max_times = int(times_entry.get())
        buy_every = int(buy_every_entry.get())
    except ValueError:
        app.after(0, lambda: messagebox.showerror(
            "Error",
            "Delay, repeat count, and buy every must be numbers."
        ))
        running = False
        return

    if max_times > MAX_ALLOWED:
        app.after(0, lambda: messagebox.showerror(
            "Limit",
            f"Max allowed is {MAX_ALLOWED} per run."
        ))
        running = False
        return

    if not text:
        app.after(0, lambda: messagebox.showerror(
            "Error",
            "Main text cannot be empty."
        ))
        running = False
        return

    set_status("Starting in 3 seconds. Click the input box now...")
    time.sleep(3)

    count = 0

    while running and count < max_times:
        send_line(text)
        count += 1
        set_status(f"Sent {count}/{max_times}")

        time.sleep(delay)

        if running and buy_text and buy_every > 0 and count % buy_every == 0:
            send_line(buy_text)
            set_status(f"Sent buy command after {count}")
            time.sleep(delay)

    running = False
    set_status("Stopped.")


def start():
    global running

    if not running:
        running = True
        set_status("Started.")
        threading.Thread(target=run_typer, daemon=True).start()


def stop():
    global running

    running = False
    set_status("Stop pressed.")


# -----------------------------
# Shortcut capture logic
# -----------------------------

MODIFIERS = ["<cmd>", "<ctrl>", "<alt>", "<shift>"]


def key_to_text(key):
    try:
        if isinstance(key, pynput_keyboard.KeyCode):
            if key.char:
                return key.char.lower()
    except Exception:
        pass

    name = getattr(key, "name", str(key).replace("Key.", ""))

    modifier_map = {
        "cmd": "<cmd>",
        "cmd_l": "<cmd>",
        "cmd_r": "<cmd>",
        "ctrl": "<ctrl>",
        "ctrl_l": "<ctrl>",
        "ctrl_r": "<ctrl>",
        "alt": "<alt>",
        "alt_l": "<alt>",
        "alt_r": "<alt>",
        "shift": "<shift>",
        "shift_l": "<shift>",
        "shift_r": "<shift>",
    }

    if name in modifier_map:
        return modifier_map[name]

    return f"<{name}>"


def build_combo(keys):
    parts = []

    for mod in MODIFIERS:
        if mod in keys:
            parts.append(mod)

    for key in keys:
        if key not in MODIFIERS:
            parts.append(key)

    return "+".join(parts)


def has_normal_key(keys):
    return any(key not in MODIFIERS for key in keys)


def install_hotkeys():
    global hotkey_listener

    start_combo = start_shortcut_var.get().strip()
    stop_combo = stop_shortcut_var.get().strip()

    if not start_combo or not stop_combo:
        return

    if "Press" in start_combo or "Press" in stop_combo:
        return

    if start_combo == stop_combo:
        messagebox.showerror("Shortcut Error", "Start and Stop shortcuts cannot be the same.")
        return

    try:
        if hotkey_listener is not None:
            hotkey_listener.stop()
            hotkey_listener = None

        hotkey_listener = pynput_keyboard.GlobalHotKeys({
            start_combo: start,
            stop_combo: stop
        })

        hotkey_listener.start()
        set_status(f"Shortcuts ready: Start {start_combo} | Stop {stop_combo}")

    except Exception as e:
        messagebox.showerror(
            "Shortcut Error",
            f"Could not set shortcut.\n\nTry something like:\n<cmd>+<shift>+s\n<cmd>+<shift>+x\n\nError:\n{e}"
        )


def capture_shortcut(which):
    global capture_listener, hotkey_listener

    if hotkey_listener is not None:
        hotkey_listener.stop()
        hotkey_listener = None

    if capture_listener is not None:
        capture_listener.stop()
        capture_listener = None

    if which == "start":
        target_var = start_shortcut_var
        label = "Start"
    else:
        target_var = stop_shortcut_var
        label = "Stop"

    pressed_keys = []

    target_var.set("Press shortcut now...")
    set_status(f"Press the keys for {label} shortcut now.")

    def on_press(key):
        key_text = key_to_text(key)

        if key_text and key_text not in pressed_keys:
            pressed_keys.append(key_text)

        combo = build_combo(pressed_keys)

        if combo:
            app.after(0, lambda: target_var.set(combo))

    def on_release(key):
        key_text = key_to_text(key)

        if has_normal_key(pressed_keys):
            combo = build_combo(pressed_keys)

            def save_combo():
                target_var.set(combo)
                set_status(f"{label} shortcut saved: {combo}")
                install_hotkeys()

            app.after(0, save_combo)
            return False

        if key_text in pressed_keys:
            pressed_keys.remove(key_text)

    capture_listener = pynput_keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    capture_listener.start()


# -----------------------------
# App UI
# -----------------------------

app = tk.Tk()
app.title("Auto Typer By Syed")
app.geometry("500x610")
app.resizable(False, False)

tk.Label(app, text="Main Text:").pack(pady=(12, 0))
text_entry = tk.Entry(app, width=58)
text_entry.insert(0, "!stun 467590746493419520")
text_entry.pack()

tk.Label(app, text="Buy Text:").pack(pady=(10, 0))
buy_entry = tk.Entry(app, width=58)
buy_entry.insert(0, "!buy stun 40")
buy_entry.pack()

tk.Label(app, text="Delay seconds:").pack(pady=(10, 0))
delay_entry = tk.Entry(app, width=18)
delay_entry.insert(0, "1.8")
delay_entry.pack()

tk.Label(app, text="Repeat count:").pack(pady=(10, 0))
times_entry = tk.Entry(app, width=18)
times_entry.insert(0, "50")
times_entry.pack()

tk.Label(app, text="Buy after every:").pack(pady=(10, 0))
buy_every_entry = tk.Entry(app, width=18)
buy_every_entry.insert(0, "20")
buy_every_entry.pack()

tk.Label(app, text="Start Shortcut:").pack(pady=(18, 0))
start_shortcut_var = tk.StringVar(value="<cmd>+<shift>+s")
start_shortcut_box = tk.Entry(
    app,
    width=28,
    textvariable=start_shortcut_var,
    justify="center",
    state="readonly"
)
start_shortcut_box.pack(pady=4)
start_shortcut_box.bind("<Button-1>", lambda event: capture_shortcut("start"))

tk.Button(
    app,
    text="Set Start Shortcut",
    width=22,
    command=lambda: capture_shortcut("start")
).pack(pady=4)

tk.Label(app, text="Stop Shortcut:").pack(pady=(14, 0))
stop_shortcut_var = tk.StringVar(value="<cmd>+<shift>+x")
stop_shortcut_box = tk.Entry(
    app,
    width=28,
    textvariable=stop_shortcut_var,
    justify="center",
    state="readonly"
)
stop_shortcut_box.pack(pady=4)
stop_shortcut_box.bind("<Button-1>", lambda event: capture_shortcut("stop"))

tk.Button(
    app,
    text="Set Stop Shortcut",
    width=22,
    command=lambda: capture_shortcut("stop")
).pack(pady=4)

button_frame = tk.Frame(app)
button_frame.pack(pady=18)

tk.Button(button_frame, text="Start", width=14, command=start).grid(row=0, column=0, padx=8)
tk.Button(button_frame, text="Stop", width=14, command=stop).grid(row=0, column=1, padx=8)

status_label = tk.Label(app, text="Ready. Click shortcut box to change keys.")
status_label.pack(pady=10)

install_hotkeys()

app.mainloop()