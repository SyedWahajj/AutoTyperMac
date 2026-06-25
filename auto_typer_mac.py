import time
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox

running = False
MAX_ALLOWED = 1000000000


def set_status(text):
    app.after(0, lambda: status_label.config(text=text))


def applescript_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_line(text):
    safe_text = applescript_escape(text)

    script = f'''
    tell application "System Events"
        keystroke "{safe_text}"
        key code 36
    end tell
    '''

    subprocess.run(["osascript", "-e", script], check=True)


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

    if delay < 0.5:
        messagebox.showerror("Error", "Delay must be at least 0.5 seconds.")
        return None

    if buy_every < 0:
        messagebox.showerror("Error", "Buy after every cannot be negative.")
        return None

    return text, buy_text, delay, repeat_count, buy_every


def typer_thread(settings):
    global running

    text, buy_text, delay, repeat_count, buy_every = settings

    set_status("Starting in 3 seconds. Click the chat/input box now...")
    time.sleep(3)

    count = 0

    try:
        while running and count < repeat_count:
            send_line(text)
            count += 1
            set_status(f"Sent {count}/{repeat_count}")
            time.sleep(delay)

            if running and buy_text and buy_every > 0 and count % buy_every == 0:
                send_line(buy_text)
                set_status(f"Sent buy command after {count}")
                time.sleep(delay)

    except subprocess.CalledProcessError:
        set_status("Permission issue. Allow Accessibility permission for AutoTyper.")
        app.after(0, lambda: messagebox.showerror(
            "Permission Needed",
            "Mac blocked keyboard control.\n\n"
            "Go to:\n"
            "System Settings → Privacy & Security → Accessibility\n\n"
            "Turn ON AutoTyper, then reopen the app."
        ))

    except Exception as e:
        set_status("Error stopped the app.")
        app.after(0, lambda: messagebox.showerror("Error", str(e)))

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


app = tk.Tk()
app.title("Auto Typer By Syed")
app.geometry("500x430")
app.resizable(False, False)

tk.Label(app, text="Auto Typer", font=("Arial", 16, "bold")).pack(pady=(15, 10))

tk.Label(app, text="Main Text:").pack()
text_entry = tk.Entry(app, width=60)
text_entry.insert(0, "!stun 467590746493419520")
text_entry.pack(pady=(0, 10))

tk.Label(app, text="Buy Text:").pack()
buy_entry = tk.Entry(app, width=60)
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
buy_every_entry.pack(pady=(0, 20))

button_frame = tk.Frame(app)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Start", width=16, command=start_typing).grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Stop", width=16, command=stop_typing).grid(row=0, column=1, padx=10)

status_label = tk.Label(app, text="Ready. Click Start, then click input box within 3 seconds.", wraplength=450)
status_label.pack(pady=15)

app.mainloop()
