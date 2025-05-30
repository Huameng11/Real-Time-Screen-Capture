"""
文件名: ui/settings_panel.py
功能: 设置面板组件，提供录制设置选项
"""

import os
import tkinter as tk
from tkinter import ttk
from ui.styles import get_styles

class SettingsPanel(ttk.Frame):
    """设置面板组件，负责管理录制设置"""
    
    def __init__(self, parent, config_manager, *args, **kwargs):
        """初始化设置面板
        
        Args:
            parent: 父级窗口组件
            config_manager: 配置管理器实例
        """
        super().__init__(parent, *args, **kwargs)
        
        self.parent = parent
        self.config_manager = config_manager
        self.styles = get_styles()
        
        # 设置初始值
        self.fps_var = tk.StringVar(value=str(config_manager.get("fps", 30)))
        self.output_format_var = tk.StringVar(value=config_manager.get("output_format", "mp4"))
        self.output_dir_var = tk.StringVar(value=config_manager.get("output_dir", os.path.join(os.path.expanduser("~"), "Desktop")))
        self.system_audio_var = tk.BooleanVar(value=True)
        
        # 设置布局
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面布局"""
        # 面板标题
        self.title_label = ttk.Label(
            self, 
            text="录制设置", 
            style="Title.TLabel"
        )
        self.title_label.pack(fill="x", padx=5, pady=(10, 5))
        
        # 设置选项容器
        settings_container = ttk.Frame(self)
        settings_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # === 输出目录设置 ===
        dir_frame = ttk.Frame(settings_container)
        dir_frame.pack(fill="x", pady=5)
        
        ttk.Label(dir_frame, text="保存位置:").pack(side="top", anchor="w")
        
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill="x", pady=2)
        
        self.output_dir_entry = ttk.Entry(
            dir_entry_frame, 
            textvariable=self.output_dir_var,
            state="readonly"
        )
        self.output_dir_entry.pack(fill="x", side="left", expand=True)
        
        # === FPS设置 ===
        fps_frame = ttk.Frame(settings_container)
        fps_frame.pack(fill="x", pady=5)
        
        ttk.Label(fps_frame, text="帧率设置:").pack(side="left")
        
        fps_values = ["15", "20", "24", "30", "60"]
        self.fps_combo = ttk.Combobox(
            fps_frame, 
            textvariable=self.fps_var,
            values=fps_values,
            width=5,
            state="readonly"
        )
        self.fps_combo.pack(side="left", padx=5)
        
        ttk.Label(fps_frame, text="FPS").pack(side="left")
        
        # 提示文本
        ttk.Label(
            fps_frame, 
            text="(较高的FPS需要更多性能)",
            style="Small.TLabel"
        ).pack(side="left", padx=5)
        
        # === 输出格式设置 ===
        format_frame = ttk.Frame(settings_container)
        format_frame.pack(fill="x", pady=5)
        
        ttk.Label(format_frame, text="输出格式:").pack(side="left")
        
        # 创建单选按钮
        mp4_radio = ttk.Radiobutton(
            format_frame, 
            text="MP4", 
            variable=self.output_format_var, 
            value="mp4"
        )
        mp4_radio.pack(side="left", padx=(5, 10))
        
        gif_radio = ttk.Radiobutton(
            format_frame, 
            text="GIF", 
            variable=self.output_format_var, 
            value="gif"
        )
        gif_radio.pack(side="left", padx=5)
        
        # === 系统音频设置 ===
        audio_frame = ttk.Frame(settings_container)
        audio_frame.pack(fill="x", pady=5)
        
        self.audio_check = ttk.Checkbutton(
            audio_frame,
            text="录制系统声音",
            variable=self.system_audio_var
        )
        self.audio_check.pack(side="left")
        
        self.audio_status_label = ttk.Label(
            audio_frame,
            text="(检测中...)",
            style="Small.TLabel"
        )
        self.audio_status_label.pack(side="left", padx=5)
    
    def update_system_audio_status(self, success, message):
        """更新系统音频状态
        
        Args:
            success (bool): 是否检测成功
            message (str): 状态消息
        """
        if success:
            self.audio_status_label.config(
                text="(已检测到系统声音)",
                foreground="green"
            )
        else:
            self.audio_status_label.config(
                text=f"(警告: {message})",
                foreground="red"
            )
            # 如果检测失败，默认禁用系统音频
            self.system_audio_var.set(False)
    
    def get_settings(self):
        """获取当前设置值
        
        Returns:
            dict: 包含当前设置的字典
        """
        return {
            "output_dir": self.output_dir_var.get(),
            "fps": int(self.fps_var.get()),
            "output_format": self.output_format_var.get(),
            "record_system_audio": self.system_audio_var.get()
        }
    
    def save_settings(self):
        """保存当前设置到配置文件"""
        settings = self.get_settings()
        for key, value in settings.items():
            self.config_manager.set(key, value)
        self.config_manager.save_config() 