"""
文件名: utils/hotkey_manager.py
功能: 管理全局热键，提供注册和卸载功能
"""

import platform
from functools import lru_cache

# 根据平台导入适当的库
if platform.system() == "Windows":
    import keyboard
else:
    try:
        import keyboard
    except ImportError:
        print("警告: 未安装keyboard库，热键功能将不可用")
        keyboard = None

class HotkeyManager:
    """热键管理器，负责管理全局热键"""
    
    def __init__(self, app):
        """初始化热键管理器
        
        Args:
            app: 应用程序实例
        """
        self.app = app
        self.hotkeys = {}
        self.hotkey_info = {
            "开始/停止录制": "Ctrl+Alt+R",
            "显示/隐藏窗口": "Ctrl+Alt+S"
        }
    
    def register_hotkeys(self):
        """注册全局热键"""
        if not self._is_supported():
            print("警告: 当前平台不支持全局热键")
            return
            
        try:
            # 录制开始/停止
            keyboard.add_hotkey(
                "ctrl+alt+r", 
                self.app.toggle_recording, 
                suppress=True
            )
            self.hotkeys["toggle_recording"] = "ctrl+alt+r"
            
            # 显示/隐藏主窗口
            keyboard.add_hotkey(
                "ctrl+alt+s", 
                self.app.toggle_window_visibility, 
                suppress=True
            )
            self.hotkeys["toggle_window"] = "ctrl+alt+s"
            
            print("成功注册热键")
        except Exception as e:
            print(f"注册热键失败: {str(e)}")
    
    def unregister_all(self):
        """注销所有已注册的热键"""
        if not self._is_supported():
            return
            
        try:
            for hotkey in self.hotkeys.values():
                keyboard.remove_hotkey(hotkey)
            self.hotkeys.clear()
        except Exception as e:
            print(f"注销热键失败: {str(e)}")
    
    @lru_cache(maxsize=1)
    def get_hotkey_info(self):
        """获取热键信息
        
        Returns:
            dict: 热键信息字典
        """
        return self.hotkey_info
    
    def _is_supported(self):
        """检查热键功能是否支持
        
        Returns:
            bool: 是否支持热键功能
        """
        return keyboard is not None 