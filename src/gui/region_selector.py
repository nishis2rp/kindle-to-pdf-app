import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

class RegionSelector:
    def __init__(self, master, on_complete, monitor=None):
        """
        Initialize the region selector.

        Args:
            master: Parent Tk window
            on_complete: Callback function to call with selected region
            monitor: Optional monitor dict with 'left', 'top', 'width', 'height' keys
                     If None, uses primary monitor
        """
        self.master = master
        self.on_complete = on_complete
        self.monitor = monitor
        self.confirmed_region = None  # Store confirmed region

        # Hide the main window
        self.master.withdraw()

        # Create a fullscreen, borderless, semi-transparent window
        self.selector_window = tk.Toplevel(self.master)

        # Set borderless FIRST (before geometry to prevent window manager interference)
        self.selector_window.overrideredirect(True)  # Borderless
        self.selector_window.attributes("-topmost", True)  # Always on top
        self.selector_window.attributes("-alpha", 0.4)  # Semi-transparent
        self.selector_window.configure(bg="black")

        # Configure for specific monitor if provided
        if monitor:
            # Position and size window to cover specific monitor
            print(f"[RegionSelector] Setting up for monitor: {monitor}")
            self.monitor_offset_x = monitor['left']
            self.monitor_offset_y = monitor['top']
            self.monitor_width = monitor['width']
            self.monitor_height = monitor['height']

            # Set geometry with monitor position
            geometry_str = f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}"
            print(f"[RegionSelector] Applying geometry: {geometry_str}")
            self.selector_window.geometry(geometry_str)

            # Force update to apply geometry
            self.selector_window.update_idletasks()
            self.selector_window.update()
        else:
            # Fallback to fullscreen on primary monitor
            print("[RegionSelector] No monitor specified, using fullscreen on primary")
            self.selector_window.attributes("-fullscreen", True)
            self.monitor_offset_x = 0
            self.monitor_offset_y = 0
            self.monitor_width = self.selector_window.winfo_screenwidth()
            self.monitor_height = self.selector_window.winfo_screenheight()

        # Force focus to this window
        self.selector_window.focus_force()

        self.canvas = tk.Canvas(
            self.selector_window,
            cursor="cross",
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Update window to get accurate dimensions
        self.selector_window.update_idletasks()

        # Get canvas center for text placement
        canvas_center_x = self.canvas.winfo_width() // 2 if self.canvas.winfo_width() > 1 else self.monitor_width // 2

        # Add instruction text
        self.instruction_font = tkfont.Font(family="Arial", size=24, weight="bold")
        self.instruction_text = self.canvas.create_text(
            canvas_center_x,
            50,
            text="ドラッグしてキャプチャ範囲を選択してください (ESCでキャンセル)",
            font=self.instruction_font,
            fill="white",
            anchor="n"
        )

        # Add English instruction
        self.instruction_text2 = self.canvas.create_text(
            canvas_center_x,
            90,
            text="Drag to select capture area (ESC to cancel)",
            font=("Arial", 18),
            fill="yellow",
            anchor="n"
        )

        self.start_x = None
        self.start_y = None
        self.rect = None
        self.bright_rect = None  # Brightened area inside selection

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.selector_window.bind("<Escape>", self.cancel_selection)

        # Update canvas after it's displayed
        self.selector_window.update_idletasks()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        if self.bright_rect:
            self.canvas.delete(self.bright_rect)

        # Create rectangle with thicker border
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#00FF00',  # Bright green
            width=4,
            fill='',
            dash=(5, 5)  # Dashed line
        )

    def on_mouse_drag(self, event):
        cur_x = event.x
        cur_y = event.y

        # Update border rectangle
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

        # Update brightened area
        if self.bright_rect:
            self.canvas.delete(self.bright_rect)

        # Create a semi-transparent white rectangle to brighten the selected area
        self.bright_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, cur_x, cur_y,
            fill='white',
            stipple='gray50',  # Makes it semi-transparent (50% pattern)
            outline=''
        )

        # Keep the border on top
        self.canvas.tag_raise(self.rect)

    def on_button_release(self, event):
        end_x = event.x
        end_y = event.y

        # Ensure start_x < end_x and start_y < end_y
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        right = max(self.start_x, end_x)
        bottom = max(self.start_y, end_y)

        # Convert canvas coordinates to screen coordinates by adding monitor offset
        screen_left = int(left + self.monitor_offset_x)
        screen_top = int(top + self.monitor_offset_y)
        width = int(right - left)
        height = int(bottom - top)

        # Check if selection is too small
        if width < 50 or height < 50:
            messagebox.showwarning(
                "選択範囲が小さすぎます / Selection too small",
                "選択範囲が小さすぎます。もう一度ドラッグして選択してください。\n\n"
                "The selection is too small. Please drag again to select."
            )
            # Clear current selection
            if self.rect:
                self.canvas.delete(self.rect)
            if self.bright_rect:
                self.canvas.delete(self.bright_rect)
            self.rect = None
            self.bright_rect = None
            return

        # Show confirmation dialog
        self.show_confirmation_dialog((screen_left, screen_top, width, height), left, top, right, bottom)

    def show_confirmation_dialog(self, region, canvas_left, canvas_top, canvas_right, canvas_bottom):
        """Show confirmation dialog and handle response"""
        response = messagebox.askyesno(
            "領域選択の確認 / Confirm Selection",
            f"この範囲でよろしいですか？ / Is this selection OK?\n\n"
            f"位置: ({region[0]}, {region[1]})\n"
            f"サイズ: {region[2]} x {region[3]} pixels\n\n"
            f"「はい」で確定、「いいえ」で再選択します。\n"
            f"Yes to confirm, No to reselect."
        )

        if response:  # Yes - confirm selection
            self.confirmed_region = region
            self.close_and_return()
        else:  # No - clear and allow reselection
            # Clear current selection
            if self.rect:
                self.canvas.delete(self.rect)
            if self.bright_rect:
                self.canvas.delete(self.bright_rect)
            self.rect = None
            self.bright_rect = None
            self.start_x = None
            self.start_y = None

            # Show instruction again
            messagebox.showinfo(
                "再選択 / Reselect",
                "もう一度ドラッグして範囲を選択してください。\n\n"
                "Please drag again to select the area."
            )

    def close_and_return(self):
        """Close the selector and return the confirmed region"""
        self.selector_window.destroy()
        self.master.deiconify()  # Restore main window
        self.on_complete(self.confirmed_region)

    def cancel_selection(self, event=None):
        self.selector_window.destroy()
        self.master.deiconify()  # Restore main window
        self.on_complete(None)  # Signal that selection was cancelled
