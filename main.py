import atexit
import os
import sys
import core
import tkinter as tk
from core import lock_keyboard, lock_mouse
from settings import open_config, save_config

config = open_config()
refresh_rate = 1500
core.configure_shortcuts(config["general"]["lock"], config["general"]["unlock"])
atexit.register(core.release_all)

if os.name == "nt":
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"Could not set DPI awareness: {e}")


def load_asset(path):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(base, "assets")
    return os.path.join(assets, path)


root = tk.Tk()
root.geometry("360x352")
root.configure(bg="#ffffff")
root.title("Keylock")
root.iconbitmap(load_asset("icon.ico"))

canvas = tk.Canvas(
    root,
    bg="#ffffff",
    width=360,
    height=352,
    bd=0,
    highlightthickness=0,
    relief="ridge",
)

canvas.place(x=0, y=0)

keyboard_locked_image = tk.PhotoImage(file=load_asset("keyboard_locked.png"))
keyboard_unlocked_image = tk.PhotoImage(file=load_asset("keyboard_unlocked.png"))
mouse_locked_image = tk.PhotoImage(file=load_asset("mouse_locked.png"))
mouse_unlocked_image = tk.PhotoImage(file=load_asset("mouse_unlocked.png"))

image_1 = keyboard_unlocked_image
image_1_ref = canvas.create_image(180, 17, image=image_1)

image_2 = mouse_unlocked_image
image_2_ref = canvas.create_image(180, 53, image=image_2)

image_3 = tk.PhotoImage(file=load_asset("layout.png"))
canvas.create_image(182, 184, image=image_3)


def update_keyboard():
    global image_1
    if core.keyboard_locked:
        image_1 = keyboard_locked_image
        canvas.itemconfig(image_1_ref, image=image_1)
    else:
        image_1 = keyboard_unlocked_image
        canvas.itemconfig(image_1_ref, image=image_1)


def update_mouse():
    global image_2
    if core.mouse_locked:
        image_2 = mouse_locked_image
        canvas.itemconfig(image_2_ref, image=image_2)
    else:
        image_2 = mouse_unlocked_image
        canvas.itemconfig(image_2_ref, image=image_2)


lock_shortcut = tk.Entry(
    bd=0, bg="#f1f1f1", fg="#000000", insertbackground="#ffffff", highlightthickness=0
)
lock_shortcut.place(x=24, y=304, width=145, height=26)

unlock_shortcut = tk.Entry(
    bd=0, bg="#f1f1f1", fg="#000000", insertbackground="#ffffff", highlightthickness=0
)
unlock_shortcut.place(x=190, y=304, width=145, height=26)
tk.Label(root, text="Lock shortcut", bg="#ffffff", fg="#555555").place(x=24, y=284)
tk.Label(root, text="Unlock shortcut", bg="#ffffff", fg="#555555").place(x=190, y=284)
tk.Label(root, text="Emergency unlock: Ctrl+Alt+Esc", bg="#ffffff", fg="#777777").place(
    x=24, y=334
)

if config["startup"]["lock_keyboard"]:
    lock_keyboard()
if config["startup"]["lock_mouse"]:
    lock_mouse()
if config["general"]["quit_after"] != "never":
    root.after(int(config["general"]["quit_after"]), sys.exit)
lock_shortcut.insert(0, config["general"]["lock"])
unlock_shortcut.insert(0, config["general"]["unlock"])

debounce_timers = {"lock": None, "unlock": None}


def save_shortcuts(config_key):
    entry = lock_shortcut if config_key == "lock" else unlock_shortcut
    timer = debounce_timers[config_key]
    if timer is not None:
        root.after_cancel(timer)
    core.configure_shortcuts(lock_shortcut.get(), unlock_shortcut.get())
    debounce_timers[config_key] = root.after(
        500,
        lambda: save_config(key=config_key, value=entry.get()),
    )


lock_shortcut.bind("<KeyRelease>", lambda e: save_shortcuts("lock"))
unlock_shortcut.bind("<KeyRelease>", lambda e: save_shortcuts("unlock"))


def check_change():
    if core.changed:
        update_keyboard()
        update_mouse()
        core.changed = False
    root.after(config["general"]["refresh_rate"], check_change)


root.after(100, check_change)

button_1_image = tk.PhotoImage(file=load_asset("1.png"))
button_1 = tk.Button(
    image=button_1_image,
    relief="flat",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: (lock_keyboard(), lock_mouse()),
)
button_1.place(x=23, y=240, width=315, height=39)

button_2_image = tk.PhotoImage(file=load_asset("2.png"))
button_2 = tk.Button(
    image=button_2_image,
    relief="flat",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: (lock_keyboard(), update_keyboard()),
)
button_2.place(x=24, y=176, width=144, height=39)

button_3_image = tk.PhotoImage(file=load_asset("3.png"))
button_3 = tk.Button(
    image=button_3_image,
    relief="flat",
    borderwidth=0,
    highlightthickness=0,
    command=lambda: (lock_mouse(), update_mouse()),
)
button_3.place(x=194, y=176, width=144, height=39)


def close_app():
    core.release_all()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)
root.resizable(False, False)
root.mainloop()
