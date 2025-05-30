"""
文件名: utils/tray_manager.py
功能: 管理系统托盘图标和相关菜单
"""

import os
import platform
import tempfile
from functools import partial
from PIL import Image

# 按平台导入适当的库
if platform.system() == "Windows":
    import pystray
    from PIL import Image
else:
    try:
        import pystray
        from PIL import Image
    except ImportError:
        print("警告: 未安装pystray或PIL库，系统托盘功能将不可用")
        pystray = None

class TrayManager:
    """系统托盘管理器，负责管理系统托盘图标和菜单"""
    
    def __init__(self, app):
        """初始化系统托盘管理器
        
        Args:
            app: 应用程序实例
        """
        self.app = app
        self.icon = None
        
        # 如果支持系统托盘，则创建图标
        if self._is_supported():
            self._create_tray_icon()
    
    def _create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建一个基本的图标
        icon_image = self._create_icon_image()
        
        # 创建菜单项
        menu_items = [
            pystray.MenuItem("显示/隐藏", self._toggle_window),
            pystray.MenuItem("选择区域", self.app.select_region),
            pystray.MenuItem("开始录制", self._start_recording),
            pystray.MenuItem("停止录制", self._stop_recording),
            pystray.MenuItem("退出", self.app.quit_app)
        ]
        
        # 创建系统托盘图标
        self.icon = pystray.Icon(
            "screen_recorder",
            icon_image,
            "即时录屏",
            pystray.Menu(*menu_items)
        )
        
        # 在单独的线程中启动图标
        self.icon.run_detached()
    
    def _create_icon_image(self):
        """创建图标图像
        
        Returns:
            PIL.Image: 图标图像
        """
        # 创建一个简单的蓝色图标
        width, height = 64, 64
        color1 = (30, 136, 229)  # 主蓝色
        color2 = (21, 101, 192)  # 深蓝色
        
        # 创建图像
        image = Image.new('RGB', (width, height), color1)
        
        # 添加一个简单的录制按钮
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        
        for x in range(width):
            for y in range(height):
                dx, dy = x - center_x, y - center_y
                distance = (dx**2 + dy**2)**0.5
                
                if distance < radius:
                    # 内部为红色录制按钮
                    image.putpixel((x, y), (229, 57, 53))
        
        return image
    
    def _toggle_window(self, icon, item):
        """切换窗口可见性
        
        Args:
            icon: 图标实例
            item: 菜单项实例
        """
        self.app.toggle_window_visibility()
    
    def _start_recording(self, icon, item):
        """开始录制
        
        Args:
            icon: 图标实例
            item: 菜单项实例
        """
        if not self.app.recording:
            self.app.toggle_recording()
    
    def _stop_recording(self, icon, item):
        """停止录制
        
        Args:
            icon: 图标实例
            item: 菜单项实例
        """
        if self.app.recording:
            self.app.toggle_recording()
    
    def stop(self):
        """停止系统托盘图标"""
        if self.icon:
            self.icon.stop()
    
    def _is_supported(self):
        """检查系统托盘功能是否支持
        
        Returns:
            bool: 是否支持系统托盘
        """
        return pystray is not None 