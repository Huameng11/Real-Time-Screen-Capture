"""
文件名: main.py
作者: LI
创建日期: 2024-05-28
最后修改: 2024-05-28
功能: 即时录屏软件的主程序，提供图形用户界面，允许用户选择录制区域或窗口，
     控制录制开始和结束，支持系统声音和麦克风录制，并通过全局快捷键控制。
"""

import os
import sys
import keyboard
import tkinter as tk
from tkinter import messagebox

from screen_capture import ScreenRecorder
from region_selector import RegionSelector
from window_selector import WindowSelector

class ScreenRecorderApp:
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("即时录屏")
        self.root.geometry("400x350")  # 增加高度以容纳新控件
        self.root.resizable(False, False)
        
        # 初始化录制状态和路径
        self.recorder = None
        self.recording = False
        self.output_dir = "C:\\Users\\admin\\desktop"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置UI和快捷键
        self.setup_ui()
        self.register_hotkeys()
        
    def setup_ui(self):
        # 录制选项框架
        options_frame = tk.Frame(self.root, padx=10, pady=10)
        options_frame.pack(fill=tk.X)
        
        # 录制类型选择
        tk.Label(options_frame, text="录制类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.record_type = tk.StringVar(value="region")
        tk.Radiobutton(options_frame, text="区域录制", variable=self.record_type, value="region").grid(row=0, column=1, sticky=tk.W)
        tk.Radiobutton(options_frame, text="窗口录制", variable=self.record_type, value="window").grid(row=0, column=2, sticky=tk.W)
        
        # 音频选项
        tk.Label(options_frame, text="音频录制:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.record_system_audio = tk.BooleanVar(value=False)  # 默认不录制系统声音
        self.record_mic = tk.BooleanVar(value=False)
        tk.Checkbutton(options_frame, text="系统声音", variable=self.record_system_audio).grid(row=1, column=1, sticky=tk.W)
        tk.Checkbutton(options_frame, text="麦克风", variable=self.record_mic).grid(row=1, column=2, sticky=tk.W)
        
        # 输出路径选择框架
        path_frame = tk.Frame(self.root, padx=10, pady=5)
        path_frame.pack(fill=tk.X)
        
        tk.Label(path_frame, text="输出路径:").pack(anchor=tk.W, pady=(5, 0))
        
        # 输出路径输入框
        self.output_path_var = tk.StringVar(value=self.output_dir)
        self.output_path_entry = tk.Entry(path_frame, textvariable=self.output_path_var, width=50)
        self.output_path_entry.pack(fill=tk.X, pady=(0, 5))
        
        # 按钮框架
        buttons_frame = tk.Frame(self.root, padx=10, pady=10)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.record_button = tk.Button(buttons_frame, text="开始录制", command=self.toggle_recording, width=15, height=2)
        self.record_button.pack(side=tk.LEFT, padx=10)
        
        quit_button = tk.Button(buttons_frame, text="退出", command=self.quit_app, width=15, height=2)
        quit_button.pack(side=tk.RIGHT, padx=10)
        
        # 状态框架
        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_frame, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # 快捷键信息
        hotkey_frame = tk.Frame(self.root, padx=10, pady=10)
        hotkey_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Label(hotkey_frame, text="快捷键:").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+R: 开始/停止录制").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+Q: 退出应用").pack(anchor=tk.W)
    
    def register_hotkeys(self):
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+alt+r', self.toggle_recording)
        keyboard.add_hotkey('ctrl+alt+q', self.quit_app)
    
    def toggle_recording(self):
        # 切换录制状态
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        try:
            # 更新输出目录
            self.output_dir = self.output_path_var.get().strip()
            if not self.output_dir:
                messagebox.showerror("错误", "请输入有效的输出路径")
                return
                
            # 确保输出目录存在
            try:
                os.makedirs(self.output_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {str(e)}")
                return
                
            if self.record_type.get() == "region":
                # 区域录制模式
                self.root.withdraw()  # 隐藏主窗口
                region_selector = RegionSelector(self.root)
                self.root.wait_window(region_selector.top)
                region = region_selector.get_selection()
                self.root.deiconify()  # 显示主窗口
                
                if not region:
                    self.status_label.config(text="录制已取消")
                    return
                
                # 使用选定区域启动录制器
                self.recorder = ScreenRecorder(
                    region=region,
                    record_system_audio=self.record_system_audio.get(),
                    record_mic=self.record_mic.get(),
                    output_dir=self.output_dir
                )
            else:  # 窗口录制模式
                self.root.withdraw()  # 隐藏主窗口
                window_selector = WindowSelector(self.root)
                self.root.wait_window(window_selector.top)
                window_handle = window_selector.get_selection()
                self.root.deiconify()  # 显示主窗口
                
                if not window_handle:
                    self.status_label.config(text="录制已取消")
                    return
                
                # 使用选定窗口启动录制器
                self.recorder = ScreenRecorder(
                    window_handle=window_handle,
                    record_system_audio=self.record_system_audio.get(),
                    record_mic=self.record_mic.get(),
                    output_dir=self.output_dir
                )
            
            # 开始录制
            self.recorder.start()
            self.recording = True
            self.record_button.config(text="停止录制")
            self.status_label.config(text="录制中...")
        except Exception as e:
            messagebox.showerror("错误", f"录制启动失败: {str(e)}")
            self.status_label.config(text="录制启动失败")
    
    def stop_recording(self):
        # 停止录制
        if self.recorder:
            output_file = self.recorder.stop()
            self.recorder = None
            self.recording = False
            self.record_button.config(text="开始录制")
            self.status_label.config(text=f"录制完成: {output_file}")
            messagebox.showinfo("录制完成", f"视频已保存到:\n{output_file}")
    
    def quit_app(self):
        # 退出应用
        if self.recording:
            if messagebox.askyesno("确认退出", "录制正在进行中，确定要退出吗？"):
                self.stop_recording()
                self.root.quit()
        else:
            self.root.quit()
    
    def run(self):
        # 运行应用
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenRecorderApp()
    app.run() 