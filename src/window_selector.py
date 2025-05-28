import tkinter as tk
import win32gui
import win32con
import win32api
from PIL import ImageGrab, ImageTk, Image

class WindowSelector:
    def __init__(self, parent):
        self.parent = parent
        self.selected_hwnd = None
        self.window_list = []
        
        # Get all top-level windows
        win32gui.EnumWindows(self._enum_windows_callback, None)
        
        # Filter out empty windows and sort by title
        self.window_list = [(hwnd, title) for hwnd, title in self.window_list if title]
        self.window_list.sort(key=lambda x: x[1].lower())
        
        # Create a new window for selection
        self.top = tk.Toplevel(parent)
        self.top.title("选择要录制的窗口")
        self.top.geometry("600x400")
        self.top.resizable(True, True)
        self.top.attributes("-topmost", True)
        
        # Instructions
        tk.Label(self.top, text="请选择要录制的窗口:", font=("Arial", 12)).pack(pady=10)
        
        # Create a frame for the listbox and scrollbar
        list_frame = tk.Frame(self.top)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox for window selection
        self.listbox = tk.Listbox(list_frame, font=("Arial", 10), yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Populate listbox
        for _, title in self.window_list:
            self.listbox.insert(tk.END, title)
        
        # Preview frame
        preview_frame = tk.Frame(self.top)
        preview_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(preview_frame, text="预览:", font=("Arial", 10)).pack(anchor=tk.W)
        
        self.preview_label = tk.Label(preview_frame, text="(选择窗口以查看预览)")
        self.preview_label.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.top)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="确定", command=self.on_select).pack(side=tk.RIGHT, padx=5)
        
        # Bind events
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.on_select())
        self.top.bind("<Escape>", self.cancel)
        
        # Wait for window to be ready
        self.top.update_idletasks()
        self.top.grab_set()
        self.top.wait_visibility()
        
        # Center the window
        self._center_window()
    
    def _center_window(self):
        """Center the window on the screen"""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f"{width}x{height}+{x}+{y}")
    
    def _enum_windows_callback(self, hwnd, _):
        """Callback for EnumWindows, adds windows to our list"""
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            self.window_list.append((hwnd, win32gui.GetWindowText(hwnd)))
    
    def _get_window_screenshot(self, hwnd):
        """Get a screenshot of the specified window"""
        # Get window rect
        try:
            rect = win32gui.GetWindowRect(hwnd)
            x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
            
            # Skip if window is minimized or has zero size
            if w <= 0 or h <= 0:
                return None
            
            # Capture the window
            screenshot = ImageGrab.grab((x, y, x + w, y + h))
            
            # Resize for preview if too large
            max_size = (300, 200)
            if screenshot.width > max_size[0] or screenshot.height > max_size[1]:
                screenshot.thumbnail(max_size, Image.LANCZOS)
            
            return ImageTk.PhotoImage(screenshot)
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None
    
    def on_listbox_select(self, event=None):
        """Handle listbox selection event"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            hwnd, title = self.window_list[index]
            
            # Show window preview
            preview_image = self._get_window_screenshot(hwnd)
            if preview_image:
                self.preview_label.config(image=preview_image)
                self.preview_label.image = preview_image  # Keep a reference
            else:
                self.preview_label.config(image=None, text="(无法获取预览)")
    
    def on_select(self):
        """Handle the OK button click"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_hwnd = self.window_list[index][0]
            self.top.destroy()
    
    def cancel(self, event=None):
        """Handle the Cancel button or Escape key"""
        self.selected_hwnd = None
        self.top.destroy()
    
    def get_selection(self):
        """Return the selected window handle"""
        return self.selected_hwnd 