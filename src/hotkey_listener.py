import keyboard
import threading

def start_hotkey_listener(stop_callback):
    """
    Starts a non-blocking listener for global hotkeys ('esc', 'ctrl+q')
    that triggers the provided stop_callback function.
    """
    def listener():
        # The keyboard library's `add_hotkey` is blocking if used with `wait`,
        # but here we just register them. The library handles the listening
        # in its own background threads.
        keyboard.add_hotkey('esc', stop_callback)
        keyboard.add_hotkey('ctrl+q', stop_callback)
        # We don't need a `keyboard.wait()` because the main Tkinter loop
        # will keep the application alive. The keyboard hooks are global.
        print("Global hotkey listener for 'esc' and 'ctrl+q' started.")

    # We don't need to run this in a separate thread because `add_hotkey`
    # is non-blocking and registers the hooks globally. We just need to call it once.
    listener()
