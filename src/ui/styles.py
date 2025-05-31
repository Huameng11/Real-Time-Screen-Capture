"""
文件名: ui/styles.py
功能: 定义应用程序的样式和主题
"""

import tkinter as tk
from tkinter import ttk
import platform

# 颜色定义
COLORS = {
    "primary": "#1E88E5",  # 主色调
    "secondary": "#64B5F6",  # 次要色调
    "accent": "#2196F3",  # 强调色
    "danger": "#F44336",  # 危险色（红色）
    "success": "#4CAF50",  # 成功色（绿色）
    "warning": "#FFC107",  # 警告色（黄色）
    "info": "#2196F3",  # 信息色（蓝色）
    "bg": "#F5F5F5",  # 背景色
    "text": "#212121",  # 主文本色
    "text_secondary": "#757575",  # 次要文本色
    "border": "#BBDEFB"  # 边框颜色
}

def setup_styles(root):
    """设置应用程序样式
    
    Args:
        root: 根窗口
    """
    style = ttk.Style(root)
    
    # 设置基础样式
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("TButton", background=COLORS["primary"], foreground="white")
    style.configure("TEntry", fieldbackground="white")
    style.configure("TCombobox", fieldbackground="white")
    
    # LabelFrame样式 - 为面板添加边框和标题样式
    style.configure(
        "TLabelframe", 
        background=COLORS["bg"],
        bordercolor=COLORS["primary"],
        borderwidth=2
    )
    
    style.configure(
        "TLabelframe.Label", 
        background=COLORS["bg"],
        foreground=COLORS["primary"],
        font=("Arial", 12, "bold")
    )
    
    # 标题样式
    style.configure(
        "Heading.TLabel", 
        font=("Arial", 18, "bold"), 
        foreground=COLORS["primary"]
    )
    
    style.configure(
        "Title.TLabel", 
        font=("Arial", 14, "bold"), 
        foreground=COLORS["primary"],
        padding=5
    )
    
    # 小文本样式
    style.configure(
        "Small.TLabel", 
        font=("Arial", 9), 
        foreground=COLORS["text_secondary"]
    )
    
    # 状态标签样式
    style.configure(
        "Status.TLabel", 
        font=("Arial", 10), 
        foreground=COLORS["text_secondary"],
        background="#F0F0F0",
        padding=3
    )
    
    # 信息标签样式
    style.configure(
        "Info.TLabel", 
        foreground=COLORS["info"]
    )
    
    # 按钮样式
    # 主要按钮样式
    style.configure(
        "Primary.TButton", 
        background=COLORS["primary"],
        foreground="black",
        padding=5
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["secondary"])]
    )
    
    # 操作按钮样式（如开始录制）
    style.configure(
        "Action.TButton", 
        background=COLORS["accent"],
        foreground="black",
        font=("Arial", 12, "bold"),
        padding=8
    )
    style.map(
        "Action.TButton",
        background=[("active", COLORS["secondary"])]
    )
    
    # 危险按钮样式（如停止录制）
    style.configure(
        "Danger.TButton", 
        background=COLORS["danger"],
        foreground="white",
        font=("Arial", 12, "bold"),
        padding=8
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#D32F2F")]
    )
    
    # 平台特定样式调整
    if platform.system() == "Darwin":  # macOS
        # macOS 特定样式
        pass
    elif platform.system() == "Windows":
        # Windows 特定样式
        pass

def get_styles():
    """获取样式字典
    
    Returns:
        dict: 样式字典
    """
    return COLORS 