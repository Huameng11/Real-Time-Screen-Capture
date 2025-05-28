import tkinter as tk
from PIL import ImageGrab, ImageTk, Image

class RegionSelector:
    def __init__(self, parent):
        self.parent = parent
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.selection = None
        
        # Create a transparent fullscreen window
        self.top = tk.Toplevel(parent)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.3)
        self.top.attributes("-topmost", True)
        
        # Take a screenshot for the background
        self.screenshot = ImageGrab.grab()
        self.tk_image = ImageTk.PhotoImage(self.screenshot)
        
        # Create a canvas that fills the screen
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="grey")
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        
        # Display the screenshot on the canvas
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        
        # Create text with instructions
        self.canvas.create_text(
            self.screenshot.width // 2,
            20,
            text="点击并拖动以选择区域，按Esc取消",
            fill="white",
            font=("Arial", 16, "bold")
        )
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.top.bind("<Escape>", self.cancel)
        
        # Initialize rectangle to be drawn
        self.rect = None
        
        # Wait for window to be ready
        self.top.update_idletasks()
        self.top.grab_set()
        self.top.wait_visibility()
    
    def on_button_press(self, event):
        # Save mouse drag start position
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # Create a rectangle if not yet exist
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )
    
    def on_mouse_drag(self, event):
        # Update current position
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # Update rectangle
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.current_x, self.current_y)
        
        # Show the current size
        width = abs(self.current_x - self.start_x)
        height = abs(self.current_y - self.start_y)
        
        # Update or create size text
        if hasattr(self, "size_text"):
            self.canvas.delete(self.size_text)
        
        self.size_text = self.canvas.create_text(
            (self.start_x + self.current_x) // 2,
            (self.start_y + self.current_y) // 2,
            text=f"{int(width)} x {int(height)}",
            fill="white",
            font=("Arial", 12, "bold")
        )
    
    def on_button_release(self, event):
        # Update current position
        self.current_x = self.canvas.canvasx(event.x)
        self.current_y = self.canvas.canvasy(event.y)
        
        # Calculate the selection
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        # Ensure minimum size (10x10)
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            self.selection = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            self.top.destroy()
        else:
            # Reset if too small
            self.canvas.delete(self.rect)
            self.rect = None
            if hasattr(self, "size_text"):
                self.canvas.delete(self.size_text)
    
    def cancel(self, event=None):
        self.selection = None
        self.top.destroy()
    
    def get_selection(self):
        return self.selection 