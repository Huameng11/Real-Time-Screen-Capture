"""
文件名: ui/control_panel.py
功能: 提供录制控制面板，包含选择区域和录制按钮
"""

import tkinter as tk
from tkinter import ttk
from ui.styles import get_styles

class ControlPanel(ttk.Frame):
    """控制面板组件，提供录制控制功能"""
    
    def __init__(self, parent, select_region_command, toggle_record_command, *args, **kwargs):
        """初始化控制面板
        
        Args:
            parent: 父级窗口组件
            select_region_command: 选择区域的回调函数
            toggle_record_command: 切换录制状态的回调函数
        """
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.select_region_command = select_region_command
        self.toggle_record_command = toggle_record_command
        self.styles = get_styles()
        
        # 初始化变量
        self.recording = False
        self.region_info = "未选择区域"
        self.hotkey_info = "加载中..."
        
        # 设置界面
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面布局"""
        # 使用LabelFrame替代普通Frame，提供边框和标题
        control_container = ttk.LabelFrame(self, text="录制控制", padding=(5, 5, 5, 5))
        control_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === 区域信息显示 ===
        region_frame = ttk.Frame(control_container)
        region_frame.pack(fill="x", pady=5)
        
        ttk.Label(region_frame, text="录制区域:").pack(side="left")
        
        self.region_label = ttk.Label(
            region_frame, 
            text=self.region_info,
            style="Info.TLabel"
        )
        self.region_label.pack(side="left", padx=5)
        
        # 选择区域按钮
        self.select_region_button = ttk.Button(
            region_frame,
            text="选择区域",
            command=self.select_region_command,
            style="Primary.TButton"
        )
        self.select_region_button.pack(side="right")
        
        # === 快捷键信息显示 ===
        hotkey_frame = ttk.Frame(control_container)
        hotkey_frame.pack(fill="x", pady=5)
        
        ttk.Label(hotkey_frame, text="快捷键:").pack(side="left")
        
        self.hotkey_label = ttk.Label(
            hotkey_frame, 
            text=self.hotkey_info,
            style="Info.TLabel"
        )
        self.hotkey_label.pack(side="left", padx=5)
        
        # === 录制按钮 ===
        button_frame = ttk.Frame(control_container)
        button_frame.pack(fill="x", pady=(20, 5))
        
        self.record_button = ttk.Button(
            button_frame,
            text="开始录制",
            command=self.toggle_record_command,
            style="Action.TButton"
        )
        self.record_button.pack(fill="x", ipady=5)
    
    def update_region_info(self, region, is_selected):
        """更新区域信息显示
        
        Args:
            region (tuple): 区域信息 (x, y, width, height)
            is_selected (bool): 是否已选择区域
        """
        if is_selected and region:
            x, y, width, height = region
            self.region_info = f"{width}x{height} (左上角: {x},{y})"
            self.region_label.config(
                text=self.region_info,
                foreground="green"
            )
            self.select_region_button.config(text="重新选择")
        else:
            self.region_info = "未选择区域"
            self.region_label.config(
                text=self.region_info,
                foreground="red"
            )
            self.select_region_button.config(text="选择区域")
    
    def update_hotkey_info(self, hotkeys):
        """更新快捷键信息显示
        
        Args:
            hotkeys (dict): 快捷键信息字典
        """
        if hotkeys:
            info = ", ".join([f"{desc}: {key}" for desc, key in hotkeys.items()])
            self.hotkey_info = info
            self.hotkey_label.config(text=info)
    
    def update_record_button_state(self, is_recording):
        """更新录制按钮状态
        
        Args:
            is_recording (bool): 是否正在录制
        """
        self.recording = is_recording
        
        if is_recording:
            self.record_button.config(
                text="停止录制",
                style="Danger.TButton"
            )
        else:
            self.record_button.config(
                text="开始录制",
                style="Action.TButton"
            ) 