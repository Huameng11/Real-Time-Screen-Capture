"""
文件名: main.py
作者: LI
创建日期: 2024-05-28
最后修改: 2024-06-01
功能: 即时录屏软件的主程序入口，初始化应用并启动主循环。
     该软件提供现代化图形用户界面，允许用户选择录制区域，
     控制录制开始和结束，支持系统声音录制，并通过全局快捷键控制。
     支持MP4和GIF格式输出，界面采用现代化天空蓝主题设计。
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import messagebox

from ui.main_window import MainWindow
from core.recorder import Recorder
from core.region_selector import RegionSelector
from utils.hotkey_manager import HotkeyManager
from utils.tray_manager import TrayManager
from utils.config_manager import ConfigManager

class ScreenRecorderApp:
    """屏幕录制应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        # 初始化核心组件
        self.config = ConfigManager()
        self.recorder = None
        self.recording = False
        self.current_region = self.config.get("region")
        self.region_selected = self.current_region is not None
        
        # 创建主窗口
        self.main_window = MainWindow(self)
        self.root = self.main_window.root
        
        # UI组件快捷引用
        self.settings_panel = self.main_window.settings_panel
        self.control_panel = self.main_window.control_panel
        self.status_label = self.main_window.status_label
        
        # 设置窗口关闭处理
        self.main_window.setup_close_handler(self.on_close)
        
        # 初始化工具组件
        self.hotkey_manager = HotkeyManager(self)
        self.tray_manager = TrayManager(self)
        
        # 启动初始化任务
        self._init_app()
    
    def _init_app(self):
        """初始化应用程序"""
        # 注册全局快捷键
        self.hotkey_manager.register_hotkeys()
        
        # 更新快捷键信息
        self.control_panel.update_hotkey_info(self.hotkey_manager.get_hotkey_info())
        
        # 检测系统音频
        self._check_system_audio()
        
        # 如果有保存的区域，显示它
        if self.current_region:
            self.control_panel.update_region_info(self.current_region, True)
            self.main_window.update_status("就绪，已加载保存的录制区域")
        else:
            self.main_window.update_status("就绪，请选择录制区域")
    
    def _check_system_audio(self):
        """检测系统声音录制功能"""
        # 在后台线程中运行，避免阻塞UI
        def check_audio():
            temp_recorder = Recorder()
            success, message = temp_recorder.test_system_audio()
            
            # 更新UI（回到主线程）
            self.root.after(0, lambda: self.settings_panel.update_system_audio_status(success, message))
        
        # 启动检测线程
        audio_thread = threading.Thread(target=check_audio)
        audio_thread.daemon = True
        audio_thread.start()
    
    def select_region(self):
        """选择录制区域"""
        # 保存当前窗口状态
        self.main_window.hide()
        
        try:
            # 创建区域选择器
            region_selector = RegionSelector(self.root)
            self.root.wait_window(region_selector.top)
            region = region_selector.get_selection()
            
            # 恢复主窗口
            self.main_window.show()
            
            if region:
                # 更新区域信息
                self.current_region = region
                self.region_selected = True
                self.control_panel.update_region_info(region, True)
                self.main_window.update_status("区域已选择，可以开始录制")
                
                # 保存区域到配置
                self.config.update_region(region)
            else:
                self.main_window.update_status("区域选择已取消")
        except Exception as e:
            self.main_window.show()
            self.main_window.update_status(f"区域选择出错: {str(e)}")
            messagebox.showerror("错误", f"选择区域时出错:\n{str(e)}")
    
    def toggle_recording(self):
        """切换录制状态（开始/停止）"""
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """开始录制"""
        if self.recording:
            return
            
        if not self.region_selected or not self.current_region:
            messagebox.showwarning("警告", "请先选择录制区域")
            return
            
        try:
            # 获取当前设置
            settings = self.settings_panel.get_settings()
            
            # 创建录制器
            self.recorder = Recorder(
                region=self.current_region,
                output_dir=settings["output_dir"],
                fps=settings["fps"],
                output_format=settings["output_format"]
            )
            
            # 开始录制
            self.recorder.start()
            self.recording = True
            
            # 更新UI状态
            self.control_panel.update_record_button_state(True)
            self.main_window.update_status(f"正在录制... (按Ctrl+Alt+R停止)")
            
            # 隐藏窗口
            self.main_window.hide()
            
        except Exception as e:
            self.main_window.update_status(f"开始录制出错: {str(e)}")
            messagebox.showerror("错误", f"开始录制时出错:\n{str(e)}")
    
    def _stop_recording(self):
        """停止录制"""
        if not self.recording or not self.recorder:
            return
            
        try:
            # 停止录制
            output_path, errors = self.recorder.stop()
            self.recording = False
            
            # 恢复窗口
            self.main_window.show()
            
            # 更新UI状态
            self.control_panel.update_record_button_state(False)
            
            # 显示结果
            if output_path and os.path.exists(output_path):
                self.main_window.update_status(f"录制已完成，保存到: {output_path}")
                
                # 显示成功消息和警告
                message = f"录制已完成，保存到:\n{output_path}"
                
                # 添加警告信息（如果有）
                if errors and any(errors.values()):
                    message += "\n\n警告:"
                    for key, error in errors.items():
                        if error:
                            message += f"\n- {error}"
                
                messagebox.showinfo("录制完成", message)
            else:
                error_msg = "录制失败"
                if errors and any(errors.values()):
                    for key, error in errors.items():
                        if error:
                            error_msg += f"\n- {error}"
                
                self.main_window.update_status(f"录制失败: {error_msg}")
                messagebox.showerror("录制失败", error_msg)
        except Exception as e:
            self.main_window.update_status(f"停止录制出错: {str(e)}")
            messagebox.showerror("错误", f"停止录制时出错:\n{str(e)}")
        finally:
            self.recorder = None
    
    def toggle_window_visibility(self):
        """切换窗口显示/隐藏状态"""
        self.main_window.toggle_visibility()
    
    def on_close(self):
        """窗口关闭处理"""
        if self.recording:
            if messagebox.askyesno("警告", "录制正在进行中，确定要退出吗？"):
                self._stop_recording()
            else:
                return  # 取消关闭
        
        # 保存窗口位置
        self.main_window.hide()
        
        # 注销全局快捷键
        self.hotkey_manager.unregister_all()
        
        # 停止系统托盘
        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.stop()
        
        # 退出应用
        self.root.destroy()
        sys.exit(0)
    
    def quit_app(self):
        """退出应用程序"""
        self.on_close()
    
    def run(self):
        """运行应用程序"""
        # 打印系统信息（调试用）
        # self.main_window.print_system_info()
        
        # 启动主循环
        self.main_window.start_mainloop()

def main():
    """程序入口点"""
    try:
        app = ScreenRecorderApp()
        app.run()
    except Exception as e:
        import traceback
        error_message = f"程序启动时发生错误:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_message)
        try:
            messagebox.showerror("启动错误", error_message)
        except:
            # 如果连消息框都无法显示，则直接打印错误
            print(error_message)

if __name__ == "__main__":
    main() 