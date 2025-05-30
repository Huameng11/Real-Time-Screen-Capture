"""
文件名: main.py
作者: LI
创建日期: 2024-05-28
最后修改: 2024-05-28
功能: 即时录屏软件的主程序，提供图形用户界面，允许用户选择录制区域，
     控制录制开始和结束，支持系统声音录制，并通过全局快捷键控制。
"""

import os
import sys
import keyboard
import tkinter as tk
from tkinter import messagebox, ttk
import platform

from screen_capture import ScreenRecorder
from region_selector import RegionSelector

class ScreenRecorderApp:
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("即时录屏")
        self.root.geometry("400x350")  # 减小高度，因为减少了控件
        self.root.resizable(False, False)
        
        # 初始化录制状态和路径
        self.recorder = None
        self.recording = False
        self.output_dir = "C:\\Users\\admin\\desktop"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置UI和快捷键
        self.setup_ui()
        self.register_hotkeys()
        
        # 打印系统信息
        self.print_system_info()
        
    def print_system_info(self):
        """打印系统信息，帮助诊断问题"""
        print("\n" + "="*50)
        print("系统信息:")
        print("-"*50)
        print(f"操作系统: {platform.system()} {platform.release()} {platform.version()}")
        print(f"Python版本: {platform.python_version()}")
        print(f"处理器: {platform.processor()}")
        
        # 打印声音设备信息
        try:
            import soundcard as sc
            print("\n音频设备信息:")
            print("-"*50)
            
            # 扬声器
            speakers = sc.all_speakers()
            print(f"扬声器设备 ({len(speakers)}):")
            for i, speaker in enumerate(speakers):
                print(f"  {i+1}. {speaker}")
            
            # 回路设备
            loopback_devices = sc.all_microphones(include_loopback=True)
            speaker_loopbacks = [device for device in loopback_devices if 'Speaker' in str(device) or '扬声器' in str(device)]
            print(f"\n系统声音回路设备 ({len(speaker_loopbacks)}):")
            for i, device in enumerate(speaker_loopbacks):
                print(f"  {i+1}. {device}")
            
            # 默认设备
            print("\n默认设备:")
            try:
                default_speaker = sc.default_speaker()
                print(f"  默认扬声器: {default_speaker}")
            except Exception as e:
                print(f"  获取默认扬声器时出错: {e}")
                
        except Exception as e:
            print(f"获取音频设备信息时出错: {e}")
        
        print("="*50 + "\n")
    
    def setup_ui(self):
        # 输出路径选择框架
        path_frame = tk.Frame(self.root, padx=10, pady=10)
        path_frame.pack(fill=tk.X)
        
        tk.Label(path_frame, text="输出路径:").pack(anchor=tk.W, pady=(5, 0))
        
        # 输出路径输入框
        self.output_path_var = tk.StringVar(value=self.output_dir)
        self.output_path_entry = tk.Entry(path_frame, textvariable=self.output_path_var, width=50)
        self.output_path_entry.pack(fill=tk.X, pady=(0, 5))
        
        # 音频选项
        audio_frame = tk.Frame(self.root, padx=10, pady=5)
        audio_frame.pack(fill=tk.X)
        
        # 系统声音状态
        self.system_audio_status = tk.Label(audio_frame, text="系统声音: 检测中...", fg="gray")
        self.system_audio_status.pack(anchor=tk.W, pady=5)
        
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
        hotkey_frame.pack(fill=tk.X, side=tk.BOTTOM, before=status_frame)
        
        tk.Label(hotkey_frame, text="快捷键:").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+R: 开始/停止录制").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+Q: 退出应用").pack(anchor=tk.W)
        
        # 初始化时检测系统声音设备
        self.check_system_audio()
    
    def register_hotkeys(self):
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+alt+r', self.toggle_recording)
        keyboard.add_hotkey('ctrl+alt+q', self.quit_app)
    
    def check_system_audio(self):
        """检测系统声音录制功能并更新状态"""
        temp_recorder = ScreenRecorder()
        success, message = temp_recorder.test_system_audio()
        
        if success:
            self.system_audio_status.config(text=f"系统声音: 可用", fg="green")
        else:
            self.system_audio_status.config(text=f"系统声音: 不可用", fg="red")
            messagebox.showwarning("系统声音检测", f"系统声音录制可能不可用: {message}")
    
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
                output_dir=self.output_dir
            )
            
            # 开始录制
            self.recorder.start()
            self.recording = True
            self.record_button.config(text="停止录制")
            self.status_label.config(text="录制中...")
            
            # 检查是否有录制警告
            if self.recorder.error_messages["system_audio"]:
                warning_message = "录制已开始，但存在以下警告:\n\n"
                warning_message += f"- 系统声音: {self.recorder.error_messages['system_audio']}\n"
                
                # 创建警告对话框
                messagebox.showwarning("录制警告", warning_message)
                
        except Exception as e:
            messagebox.showerror("错误", f"录制启动失败: {str(e)}")
            self.status_label.config(text="录制启动失败")
    
    def stop_recording(self):
        # 停止录制
        if self.recorder:
            print("\n" + "="*50)
            print("[调试] 正在停止录制...")
            
            try:
                output_file, error_messages = self.recorder.stop()
                
                # 打印错误信息以便诊断
                print("[调试] 录制完成")
                print("-"*50)
                print("[调试] 错误信息:")
                for key, msg in error_messages.items():
                    if msg:
                        print(f"  - {key}: {msg}")
                    else:
                        print(f"  - {key}: 无错误")
                
                self.recorder = None
                self.recording = False
                self.record_button.config(text="开始录制")
                
                if output_file:
                    print(f"[调试] 输出文件: {output_file}")
                    self.status_label.config(text=f"录制完成: {output_file}")
                    
                    # 构建结果消息
                    result_message = f"视频已保存到:\n{output_file}"
                    
                    # 添加任何警告信息
                    warnings = []
                    if error_messages["system_audio"]:
                        warnings.append(f"系统声音: {error_messages['system_audio']}")
                    if error_messages["video"]:
                        warnings.append(f"视频: {error_messages['video']}")
                    
                    if warnings:
                        result_message += "\n\n警告:\n- " + "\n- ".join(warnings)
                        print("[警告] 录制过程中存在警告")
                        for warning in warnings:
                            print(f"  - {warning}")
                        messagebox.showwarning("录制完成 (有警告)", result_message)
                    else:
                        print("[调试] 录制过程中没有警告")
                        messagebox.showinfo("录制完成", result_message)
                else:
                    print("[错误] 无法获取输出文件")
                    self.status_label.config(text="录制失败")
                    messagebox.showerror("录制失败", "无法保存录制文件。请检查错误日志获取更多信息。")
            except Exception as e:
                print(f"[错误] 停止录制时发生异常: {str(e)}")
                import traceback
                traceback.print_exc()
                self.status_label.config(text="录制停止失败")
                messagebox.showerror("错误", f"录制停止失败: {str(e)}")
                self.recorder = None
                self.recording = False
                self.record_button.config(text="开始录制")
            
            print("="*50 + "\n")
    
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