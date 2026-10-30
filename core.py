import pynput
from pynput.keyboard import HotKey, Key, KeyCode

mouse_listener = None
shortcut_listener = None
lock_hotkey = None
unlock_hotkey = None
emergency_hotkey = None
unlock_event_keys = set()
keyboard_locked = False
mouse_locked = False
changed = False


def parse_shortcut(shortcut_str):
    keys = []
    modifiers = {
        "ctrl": Key.ctrl,
        "control": Key.ctrl,
        "shift": Key.shift,
        "alt": Key.alt,
    }
    for token in (shortcut_str or "").lower().replace(" ", "").split("+"):
        if not token:
            continue
        if token in modifiers:
            keys.append(modifiers[token])
        elif hasattr(Key, token):
            special_key = getattr(Key, token)
            keys.append(KeyCode.from_vk(special_key.value.vk))
        elif len(token) == 1:
            keys.append(KeyCode.from_char(token))
        else:
            raise ValueError(f"Unsupported shortcut key: {token}")
    return keys


def start_shortcut_listener():
    global shortcut_listener
    if shortcut_listener is None:
        shortcut_listener = pynput.keyboard.Listener(
            win32_event_filter=keyboard_event_filter
        )
        shortcut_listener.start()
        print("Shortcut listener started.")


def configure_shortcuts(lock_shortcut, unlock_shortcut):
    global lock_hotkey, unlock_hotkey, emergency_hotkey, unlock_event_keys
    lock_keys = parse_shortcut(lock_shortcut or "ctrl+alt+l")
    unlock_keys = parse_shortcut(unlock_shortcut or "ctrl+q")
    emergency_keys = parse_shortcut("ctrl+alt+esc")
    lock_hotkey = HotKey(lock_keys, lambda: set_all_locked(True))
    unlock_hotkey = HotKey(unlock_keys, lambda: set_all_locked(False))
    emergency_hotkey = HotKey(emergency_keys, lambda: set_all_locked(False))
    unlock_event_keys = set(unlock_keys + emergency_keys)
    start_shortcut_listener()


def start_keyboard():
    global keyboard_locked
    keyboard_locked = True
    print("Keyboard locked.")


def stop_keyboard():
    global keyboard_locked
    keyboard_locked = False
    print("Keyboard unlocked.")


def start_mouse():
    global mouse_listener, mouse_locked
    if mouse_listener is None:
        mouse_listener = pynput.mouse.Listener(
            win32_event_filter=mouse_event_filter
        )
        mouse_listener.start()
    mouse_locked = True
    print("Mouse locked.")


def stop_mouse():
    global mouse_listener, mouse_locked
    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None
    mouse_locked = False
    print("Mouse unlocked.")


def lock_keyboard():
    global changed
    if keyboard_locked:
        stop_keyboard()
    else:
        start_keyboard()
    changed = True


def lock_mouse():
    global changed
    if mouse_locked:
        stop_mouse()
    else:
        start_mouse()
    changed = True


def set_all_locked(locked):
    global changed
    if locked:
        if not keyboard_locked:
            start_keyboard()
        if not mouse_locked:
            start_mouse()
    else:
        stop_keyboard()
        stop_mouse()
    changed = True


def release_all():
    """Restore input hooks during normal application shutdown."""
    global keyboard_locked, mouse_locked, shortcut_listener, mouse_listener
    keyboard_locked = False
    mouse_locked = False
    if shortcut_listener:
        shortcut_listener.stop()
        shortcut_listener = None
    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None
    print("All input locks released.")


def keyboard_event_filter(message, data):
    """Handle hotkeys before Windows decides whether to suppress a key."""
    if shortcut_listener is None:
        return True

    # Remote-control software such as UltraViewer usually delivers input via
    # Windows injected-event flags. Keep that input flowing while the local
    # physical keyboard is locked, and don't let remote keystrokes trigger
    # Keylock's local shortcuts.
    if data.flags & 0x12:  # LLKHF_INJECTED | LLKHF_LOWER_IL_INJECTED
        return True

    try:
        key = shortcut_listener._event_to_key(message, data.vkCode)
        key = shortcut_listener.canonical(key)
    except (AttributeError, OSError):
        return True

    press_messages = shortcut_listener._PRESS_MESSAGES
    release_messages = shortcut_listener._RELEASE_MESSAGES
    if message in press_messages:
        if lock_hotkey:
            lock_hotkey.press(key)
        if unlock_hotkey:
            unlock_hotkey.press(key)
        if emergency_hotkey:
            emergency_hotkey.press(key)
    elif message in release_messages:
        if lock_hotkey:
            lock_hotkey.release(key)
        if unlock_hotkey:
            unlock_hotkey.release(key)
        if emergency_hotkey:
            emergency_hotkey.release(key)

    # Keep configured unlock keys deliverable to Windows, and synchronously
    # suppress other keys only while the keyboard lock is active.
    if keyboard_locked and key not in unlock_event_keys:
        shortcut_listener.suppress_event()
    return True


def mouse_event_filter(message, data):
    """Suppress local mouse events but allow injected remote-control events."""
    if mouse_locked and not data.flags & 0x03:  # LLMHF_INJECTED | LOWER_IL
        mouse_listener.suppress_event()
    return True
