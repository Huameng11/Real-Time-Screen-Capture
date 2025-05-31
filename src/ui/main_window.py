"""
文件名: ui/main_window.py
功能: 提供主窗口界面和布局管理
"""

import os
import sys
import platform
import tkinter as tk
from tkinter import ttk
from ui.styles import setup_styles
from ui.settings_panel import SettingsPanel
from ui.control_panel import ControlPanel

class MainWindow:
    """主窗口类，管理应用程序的主界面"""
    
    def __init__(self, app):
        """初始化主窗口
        
        Args:
            app: 应用程序实例
        """
        self.app = app
        
        # 初始化变量
        self.visible = True
        
        # 创建窗口
        self.root = tk.Tk()
        self.root.title("即时录屏")
        self.root.geometry("450x480")
        self.root.minsize(450, 480)
        
        # 设置主题和样式
        self.setup_theme()
        
        # 创建UI组件
        self.create_ui()
    
    def setup_theme(self):
        """设置主题和样式"""
        # 设置主题色调
        if platform.system() == "Windows":
            # 在Windows上使用特定的样式
            self.root.config(bg="#f0f0f0")
            
        elif platform.system() == "Darwin":
            # 在macOS上使用特定的样式
            pass
        
        # 设置全局样式
        setup_styles(self.root)
    
    def create_ui(self):
        """创建主窗口界面"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 设置面板
        self.settings_panel = SettingsPanel(main_frame, self.app.config)
        self.settings_panel.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 控制面板
        self.control_panel = ControlPanel(
            main_frame, 
            select_region_command=self.app.select_region,
            toggle_record_command=self.app.toggle_recording
        )
        self.control_panel.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame, 
            text="就绪", 
            style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)
    
    def setup_close_handler(self, handler):
        """设置窗口关闭处理函数
        
        Args:
            handler: 窗口关闭时调用的函数
        """
        self.root.protocol("WM_DELETE_WINDOW", handler)
    
    def update_status(self, message):
        """更新状态栏消息
        
        Args:
            message (str): 状态消息
        """
        self.status_label.config(text=message)
    
    def hide(self):
        """隐藏主窗口"""
        self.root.withdraw()
        self.visible = False
    
    def show(self):
        """显示主窗口"""
        self.root.deiconify()
        self.visible = True
        self.root.lift()
        self.root.focus_force()
    
    def toggle_visibility(self):
        """切换窗口显示/隐藏状态"""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def print_system_info(self):
        """打印系统信息（调试用）"""
        print(f"Python 版本: {sys.version}")
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"平台: {platform.platform()}")
        print(f"Tcl/Tk 版本: {tk.TkVersion}")
    
    def start_mainloop(self):
        """启动主事件循环"""
        self.root.mainloop() 