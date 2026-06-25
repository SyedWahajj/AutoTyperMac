import pyautogui
import time
import threading
import tkinter as tk
from tkinter import messagebox

try:
    from pynput import keyboard as pynput_keyboard
except Exception:
    pynput_keyboard = None


running = False
hotkey_listener = None
capturing_for = None

MAX_ALLOWED = 100
pyautogui.FAILSAFE = True  # emergency stop: move mouse to top-left corner


# -----------------------------
# Safe UI helpers
# -----------------------------

def set_status(text):
    app.after(0, lambda: status_label.config(text=text))


def show_error(title, message):
    app.after(0, lambda: messagebox.showerror(title, message))


# -----------------------------
# Auto typing logic
# -----------------------------

def send_line(text):
    pyautogui.write(text, interval=0.01)
    pyautogui.press("enter")


def get_settings():
    text = text_entry.get().strip()
    buy_text = buy_entry.get().strip()

    try:
        delay = float(delay_entry.get().strip())
        repeat_count = int(repeat_entry.get().strip())
        buy_every = int(buy_every_entry.get().strip())
    except ValueError:
        messagebox.showerror("Error", "Delay, repeat count, and buy after every must be numbers.")
        return None

    if not text:
        messagebox.showerror("Error", "Main text cannot be empty.")
        return None

    if repeat_count < 1:
        messagebox.showerror("Error", "Repeat count must be at least 1.")
        return None

    if repeat_count > MAX_ALLOWED:
        messagebox.showerror("Limit", f"Max allowed is {MAX_ALLOWED} per run.")
        return None

    if delay < 0.2:
        messagebox.showerror("Error", "Delay must be at least 0.2 seconds.")
        return None

    if buy_every < 0:
        messagebox.showerror("Error", "Buy after every cannot be negative.")
        return None

    return {
        "text": text,
        "buy_text": buy_text,
        "delay": delay,
        "repeat_count": repeat_count,
        "buy_every": buy_every,
    }


def typer_thread(settings):
    global running

    set_status("Starting in 3 seconds. Click the input/chat box now...")
    time.sleep(3)

    count = 0

    try:
        while running and count < settings["repeat_count"]:
            send_line(settings["text"])
            count += 1
            set_status(f"Sent {count}/{settings['repeat_count']}")

            time.sleep(settings["delay"])

            if (
                running
                and settings["buy_text"]
                and settings["buy_every"] > 0
                and count % settings["buy_every"] == 0
            ):
                send_line(settings["buy_text"])
                set_status(f"Sent buy command after {count}")
                time.sleep(settings["delay"])

    except pyautogui.FailSafeException:
        set_status("Emergency stopped. Mouse moved to top-left corner.")
    except Exception as e:
        show_error("Typing Error", str(e))

    running = False
    set_status("Stopped.")


def start_typing():
    global running

    if running:
        return

    settings = get_settings()
    if settings is None:
        return

    running = True
    set_status("Started.")
    threading.Thread(target=typer_thread, args=(settings,), daemon=True).start()


def stop_typing():
    global running
    running = False
    set_status("Stop pressed.")


# -----------------------------
# Shortcut logic
# -----------------------------

def stop_hotkey_listener():
    global hotkey_listener

    try:
        if hotkey_listener is not None:
            hotkey_listener.stop()
            hotkey_listener = None
    except Exception:
        hotkey_listener = None


def install_hotkeys():
    global hotkey_listener

    if pynput_keyboard is None:
        set_status("pynput not available. Buttons still work.")
        return

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
        stop_hotkey_listener()

        hotkey_listener = pynput_keyboard.GlobalHotKeys({
            start_combo: start_typing,
            stop_combo: stop_typing,
        })

        hotkey_listener.start()
        set_status(f"Shortcuts ready: Start {start_combo} | Stop {stop_combo}")

    except Exception as e:
        set_status("Shortcut permission issue. Buttons still work.")
        messagebox.showwarning(
            "Shortcut Warning",
            "Could not activate global shortcuts.\n\n"
            "The Start/Stop buttons will still work.\n\n"
            "On Mac, allow the app in:\n"
            "System Settings → Privacy & Security → Input Monitoring\n"
            "and Accessibility.\n\n"
            f"Details: {e}"
        )


def begin_capture(which):
    global capturing_for

    capturing_for = which

    if which == "start":
        start_shortcut_var.set("Press shortcut now...")
        set_status("Press the START shortcut now.")
    else:
        stop_shortcut_var.set("Press shortcut now...")
        set_status("Press the STOP shortcut now.")

    # Stop global listener while capturing so it does not fight with Tkinter
    stop_hotkey_listener()

    app.focus_force()
    app.bind_all("<KeyPress>", capture_keypress)


def is_modifier_key(keysym):
    key = keysym.lower()
    return key in [
        "shift_l", "shift_r",
        "control_l", "control_r",
        "alt_l", "alt_r",
        "option_l", "option_r",
        "meta_l", "meta_r",
        "command", "command_l", "command_r",
        "super_l", "super_r",
    ]


def key_name_from_event(event):
    keysym = event.keysym.lower()

    special_keys = {
        "return": "enter",
        "escape": "esc",
        "backspace": "backspace",
        "delete": "delete",
        "space": "space",
        "tab": "tab",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
    }

    if keysym in special_keys:
        return f"<{special_keys[keysym]}>"

    if event.char and len(event.char) == 1 and event.char.isprintable():
        return event.char.lower()

    return f"<{keysym}>"


def combo_from_event(event):
    mods = []

    # Common Tk modifier state bits
    shift_pressed = bool(event.state & 0x0001)
    ctrl_pressed = bool(event.state & 0x0004)
    alt_pressed = bool(event.state & 0x0008)

    # Command key bit can vary across macOS/Tk builds
    cmd_pressed = bool(event.state & 0x0010) or bool(event.state & 0x0040) or bool(event.state & 0x0080)

    if ctrl_pressed:
        mods.append("<ctrl>")
    if alt_pressed:
        mods.append("<alt>")
    if shift_pressed:
        mods.append("<shift>")
    if cmd_pressed:
        mods.append("<cmd>")

    key = key_name_from_event(event)

    # Ignore modifier-only press
    if key in ["<ctrl>", "<alt>", "<shift>", "<cmd>"]:
        return None

    # Avoid shortcut with no modifier, like just "s"
    if not mods:
        return None

    return "+".join(mods + [key])


def capture_keypress(event):
    global capturing_for

    if capturing_for is None:
        return "break"

    if is_modifier_key(event.keysym):
        return "break"

    combo = combo_from_event(event)

    if combo is None:
        set_status("Use a combo like Control + Shift + S.")
        return "break"

    if capturing_for == "start":
        start_shortcut_var.set(combo)
        set_status(f"Start shortcut saved: {combo}")
    else:
        stop_shortcut_var.set(combo)
        set_status(f"Stop shortcut saved: {combo}")

    capturing_for = None
    app.unbind_all("<KeyPress>")

    install_hotkeys()
    return "break"


def save_manual_shortcuts():
    install_hotkeys()


def on_close():
    stop_hotkey_listener()
    app.destroy()


# -----------------------------
# UI
# -----------------------------

app = tk.Tk()
app.title("Auto Typer By Syed")
app.geometry("520x620")
app.resizable(False, False)

title = tk.Label(app, text="Auto Typer", font=("Arial", 16, "bold"))
title.pack(pady=(12, 5))

tk.Label(app, text="Main Text:").pack()
text_entry = tk.Entry(app, width=62)
text_entry.insert(0, "!stun 467590746493419520")
text_entry.pack(pady=(0, 10))

tk.Label(app, text="Buy Text:").pack()
buy_entry = tk.Entry(app, width=62)
buy_entry.insert(0, "!buy stun 40")
buy_entry.pack(pady=(0, 10))

tk.Label(app, text="Delay seconds:").pack()
delay_entry = tk.Entry(app, width=18, justify="center")
delay_entry.insert(0, "1.8")
delay_entry.pack(pady=(0, 10))

tk.Label(app, text="Repeat count:").pack()
repeat_entry = tk.Entry(app, width=18, justify="center")
repeat_entry.insert(0, "50")
repeat_entry.pack(pady=(0, 10))

tk.Label(app, text="Buy after every:").pack()
buy_every_entry = tk.Entry(app, width=18, justify="center")
buy_every_entry.insert(0, "20")
buy_every_entry.pack(pady=(0, 15))

tk.Label(app, text="Start Shortcut:").pack()
start_shortcut_var = tk.StringVar(value="<ctrl>+<shift>+s")
start_shortcut_box = tk.Entry(app, width=32, textvariable=start_shortcut_var, justify="center")
start_shortcut_box.pack(pady=(0, 5))
start_shortcut_box.bind("<Button-1>", lambda event: begin_capture("start"))

tk.Button(app, text="Click to Set Start Shortcut", width=28, command=lambda: begin_capture("start")).pack(pady=(0, 12))

tk.Label(app, text="Stop Shortcut:").pack()
stop_shortcut_var = tk.StringVar(value="<ctrl>+<shift>+x")
stop_shortcut_box = tk.Entry(app, width=32, textvariable=stop_shortcut_var, justify="center")
stop_shortcut_box.pack(pady=(0, 5))
stop_shortcut_box.bind("<Button-1>", lambda event: begin_capture("stop"))

tk.Button(app, text="Click to Set Stop Shortcut", width=28, command=lambda: begin_capture("stop")).pack(pady=(0, 12))

tk.Button(app, text="Save Shortcuts", width=20, command=save_manual_shortcuts).pack(pady=(0, 15))

button_frame = tk.Frame(app)
button_frame.pack(pady=5)

tk.Button(button_frame, text="Start", width=16, command=start_typing).grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Stop", width=16, command=stop_typing).grid(row=0, column=1, padx=10)

status_label = tk.Label(app, text="Ready. Use buttons or shortcuts.", wraplength=480)
status_label.pack(pady=15)

app.protocol("WM_DELETE_WINDOW", on_close)

install_hotkeys()
app.mainloop()
