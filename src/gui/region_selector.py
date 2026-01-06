import tkinter as tk

class RegionSelector:
    def __init__(self, master, on_complete):
        self.master = master
        self.on_complete = on_complete
        
        # Hide the main window
        self.master.withdraw()
        
        # Create a fullscreen, borderless, semi-transparent window
        self.selector_window = tk.Toplevel(self.master)
        self.selector_window.attributes("-fullscreen", True)
        self.selector_window.attributes("-alpha", 0.3) # Semi-transparent
        self.selector_window.configure(bg="grey")
        self.selector_window.overrideredirect(True) # Borderless

        self.canvas = tk.Canvas(self.selector_window, cursor="cross", bg="grey")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.selector_window.bind("<Escape>", self.cancel_selection)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, 
                                                outline='red', width=2)

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Ensure start_x < end_x and start_y < end_y
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)
        
        region = (int(left), int(top), int(right - left), int(bottom - top))
        
        self.selector_window.destroy()
        self.master.deiconify() # Restore main window
        self.on_complete(region)

    def cancel_selection(self, event=None):
        self.selector_window.destroy()
        self.master.deiconify() # Restore main window
        self.on_complete(None) # Signal that selection was cancelled
