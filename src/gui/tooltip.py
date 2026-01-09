"""
Tooltip widget for displaying help text on hover
"""
import tkinter as tk


class ToolTip:
    """Simple tooltip class for widgets"""

    def __init__(self, widget, text):
        """
        Create a tooltip for a widget

        Args:
            widget: The tkinter widget to attach the tooltip to
            text: The text to display in the tooltip
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        """Show the tooltip window"""
        if self.tooltip_window or not self.text:
            return

        # Get widget position
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        # Create tooltip label
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
            padx=4,
            pady=2
        )
        label.pack()

    def hide_tooltip(self, event=None):
        """Hide and destroy the tooltip window"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
