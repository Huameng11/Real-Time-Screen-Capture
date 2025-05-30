"""
文件名: region_selector.py
功能: 提供屏幕区域选择功能，允许用户通过鼠标拖拽在屏幕上选择一个矩形区域进行录制。
     创建半透明覆盖层显示当前屏幕内容，并在用户拖拽时绘制醒目的矩形框标识选择区域，
     同时实时显示所选区域的尺寸信息，确保用户可以精确选择所需区域。
"""

import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import ctypes
import win32api
import win32con
import win32gui

class RegionSelector:
    def __init__(self, parent):
        self.parent = parent
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.selection = None
        
        # 获取屏幕信息
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        
        # 获取实际的DPI缩放因子
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        
        # 创建一个透明的全屏窗口
        self.top = tk.Toplevel(parent)
        self.top.overrideredirect(True)  # 无边框
        self.top.geometry(f"{self.screen_width}x{self.screen_height}+0+0")  # 确保覆盖整个屏幕
        self.top.attributes("-alpha", 0.4)  # 提高透明度，使背景更清晰
        self.top.attributes("-topmost", True)
        
        # 截取屏幕作为背景
        self.screenshot = ImageGrab.grab()
        self.tk_image = ImageTk.PhotoImage(self.screenshot)
        
        # 创建一个填满屏幕的画布
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="grey", 
                             width=self.screen_width, height=self.screen_height)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        
        # 在画布上显示截图
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        
        # 创建带有指令的文本 - 增加可见性
        self.instruction_text = self.canvas.create_text(
            self.screen_width // 2,
            30,
            text="点击并拖动以选择区域，按Esc取消",
            fill="white",
            font=("Arial", 18, "bold")
        )
        
        # 创建文本背景以增强可读性
        text_bbox = self.canvas.bbox(self.instruction_text)
        padding = 10
        self.text_bg = self.canvas.create_rectangle(
            text_bbox[0] - padding, 
            text_bbox[1] - padding, 
            text_bbox[2] + padding, 
            text_bbox[3] + padding,
            fill="black", 
            outline="",
            stipple="gray50"  # 半透明效果
        )
        self.canvas.tag_lower(self.text_bg, self.instruction_text)
        
        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.top.bind("<Escape>", self.cancel)
        
        # 初始化要绘制的矩形和阴影
        self.rect = None
        self.rect_shadow = None
        self.size_text = None
        self.size_text_bg = None
        
        # 等待窗口准备就绪
        self.top.update_idletasks()
        self.top.grab_set()
        self.top.wait_visibility()
        
        # 强制窗口到屏幕左上角
        self.top.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.top.update()
    
    def on_button_press(self, event):
        # 保存鼠标拖动的起始位置
        self.start_x = event.x
        self.start_y = event.y
        
        # 清除已有的图形
        self._clear_drawn_items()
        
        # 创建矩形的阴影效果（黑色边框）
        self.rect_shadow = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="black", width=4
        )
        
        # 创建主矩形（红色边框）
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#FF3333", width=2
        )
    
    def on_mouse_drag(self, event):
        # 更新当前位置
        self.current_x = event.x
        self.current_y = event.y
        
        # 更新矩形和阴影
        self.canvas.coords(self.rect_shadow, self.start_x, self.start_y, self.current_x, self.current_y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.current_x, self.current_y)
        
        # 显示当前尺寸
        width = abs(self.current_x - self.start_x)
        height = abs(self.current_y - self.start_y)
        
        # 计算文本位置 - 确保始终在矩形内可见
        text_x = (self.start_x + self.current_x) // 2
        text_y = (self.start_y + self.current_y) // 2
        
        # 删除旧的尺寸文本和背景
        if self.size_text:
            self.canvas.delete(self.size_text)
        if self.size_text_bg:
            self.canvas.delete(self.size_text_bg)
        
        # 尺寸文本
        text = f"{int(width)} × {int(height)} 像素"
        self.size_text = self.canvas.create_text(
            text_x, text_y,
            text=text,
            fill="white",
            font=("Arial", 14, "bold")
        )
        
        # 为文本创建背景以增强可读性
        text_bbox = self.canvas.bbox(self.size_text)
        padding = 8
        self.size_text_bg = self.canvas.create_rectangle(
            text_bbox[0] - padding, 
            text_bbox[1] - padding, 
            text_bbox[2] + padding, 
            text_bbox[3] + padding,
            fill="#333333",
            outline="#FF3333",
            width=1
        )
        self.canvas.tag_lower(self.size_text_bg, self.size_text)
    
    def on_button_release(self, event):
        # 更新当前位置
        self.current_x = event.x
        self.current_y = event.y
        
        # 计算选择区域
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        # 确保最小尺寸（10x10）
        if (x2 - x1) > 10 and (y2 - y1) > 10:
            # 直接使用实际屏幕坐标
            self.selection = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            self.top.destroy()
        else:
            # 如果太小则重置并显示提示
            self._clear_drawn_items()
            min_size_text = self.canvas.create_text(
                self.screen_width // 2,
                self.screen_height // 2,
                text="选择区域太小，请重试（至少10×10像素）",
                fill="white",
                font=("Arial", 16, "bold")
            )
            min_size_bg = self.canvas.create_rectangle(
                self.canvas.bbox(min_size_text),
                fill="black",
                outline="red",
                width=2
            )
            self.canvas.tag_lower(min_size_bg, min_size_text)
            self.canvas.update()
            self.top.after(1500, lambda: [
                self.canvas.delete(min_size_text),
                self.canvas.delete(min_size_bg)
            ])
    
    def _clear_drawn_items(self):
        """清除已绘制的所有图形元素"""
        for item in [self.rect, self.rect_shadow, self.size_text, self.size_text_bg]:
            if item:
                self.canvas.delete(item)
        self.rect = None
        self.rect_shadow = None
        self.size_text = None
        self.size_text_bg = None
    
    def cancel(self, event=None):
        # 取消选择
        self.selection = None
        self.top.destroy()
    
    def get_selection(self):
        # 返回选择的区域
        return self.selection 