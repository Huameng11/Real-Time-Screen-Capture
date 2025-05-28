"""
文件名: window_selector.py
功能: 提供窗口选择功能，列出系统中所有可见窗口，允许用户选择要录制的特定窗口。
     显示窗口预览，并在选择后返回窗口句柄用于录制。自动获取窗口位置和大小信息，
     支持通过双击或确认按钮选择目标窗口。
"""

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
        
        # 获取所有顶级窗口
        win32gui.EnumWindows(self._enum_windows_callback, None)
        
        # 过滤掉空窗口并按标题排序
        self.window_list = [(hwnd, title) for hwnd, title in self.window_list if title]
        self.window_list.sort(key=lambda x: x[1].lower())
        
        # 创建窗口选择器窗口
        self.top = tk.Toplevel(parent)
        self.top.title("选择要录制的窗口")
        self.top.geometry("600x400")
        self.top.resizable(True, True)
        self.top.attributes("-topmost", True)
        
        # 说明文字
        tk.Label(self.top, text="请选择要录制的窗口:", font=("Arial", 12)).pack(pady=10)
        
        # 创建列表框和滚动条的框架
        list_frame = tk.Frame(self.top)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 窗口列表框
        self.listbox = tk.Listbox(list_frame, font=("Arial", 10), yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # 填充列表框
        for _, title in self.window_list:
            self.listbox.insert(tk.END, title)
        
        # 预览框架
        preview_frame = tk.Frame(self.top)
        preview_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(preview_frame, text="预览:", font=("Arial", 10)).pack(anchor=tk.W)
        
        self.preview_label = tk.Label(preview_frame, text="(选择窗口以查看预览)")
        self.preview_label.pack(fill=tk.X, pady=5)
        
        # 按钮
        button_frame = tk.Frame(self.top)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="确定", command=self.on_select).pack(side=tk.RIGHT, padx=5)
        
        # 绑定事件
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.on_select())
        self.top.bind("<Escape>", self.cancel)
        
        # 等待窗口准备就绪
        self.top.update_idletasks()
        self.top.grab_set()
        self.top.wait_visibility()
        
        # 居中窗口
        self._center_window()
    
    def _center_window(self):
        """将窗口居中显示"""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f"{width}x{height}+{x}+{y}")
    
    def _enum_windows_callback(self, hwnd, _):
        """EnumWindows的回调函数，将窗口添加到列表中"""
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            self.window_list.append((hwnd, win32gui.GetWindowText(hwnd)))
    
    def _get_window_screenshot(self, hwnd):
        """获取指定窗口的截图"""
        # 获取窗口矩形
        try:
            rect = win32gui.GetWindowRect(hwnd)
            x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
            
            # 如果窗口最小化或大小为零则跳过
            if w <= 0 or h <= 0:
                return None
            
            # 捕获窗口
            screenshot = ImageGrab.grab((x, y, x + w, y + h))
            
            # 如果太大则调整预览大小
            max_size = (300, 200)
            if screenshot.width > max_size[0] or screenshot.height > max_size[1]:
                screenshot.thumbnail(max_size, Image.LANCZOS)
            
            return ImageTk.PhotoImage(screenshot)
        except Exception as e:
            print(f"捕获窗口截图时出错: {e}")
            return None
    
    def on_listbox_select(self, event=None):
        """处理列表框选择事件"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            hwnd, title = self.window_list[index]
            
            # 显示窗口预览
            preview_image = self._get_window_screenshot(hwnd)
            if preview_image:
                self.preview_label.config(image=preview_image)
                self.preview_label.image = preview_image  # 保持引用
            else:
                self.preview_label.config(image=None, text="(无法获取预览)")
    
    def on_select(self):
        """处理确定按钮点击"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_hwnd = self.window_list[index][0]
            self.top.destroy()
    
    def cancel(self, event=None):
        """处理取消按钮或Esc键"""
        self.selected_hwnd = None
        self.top.destroy()
    
    def get_selection(self):
        """返回选定的窗口句柄"""
        return self.selected_hwnd 