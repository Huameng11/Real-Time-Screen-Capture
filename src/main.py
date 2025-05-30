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
from tkinter import messagebox, ttk
import platform
import subprocess

from screen_capture import ScreenRecorder
from region_selector import RegionSelector
from window_selector import WindowSelector

class ScreenRecorderApp:
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("即时录屏")
        self.root.geometry("400x400")  # 增加高度以容纳新控件
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
            
            # 麦克风
            microphones = sc.all_microphones()
            print(f"\n麦克风设备 ({len(microphones)}):")
            for i, mic in enumerate(microphones):
                print(f"  {i+1}. {mic}")
            
            # 默认设备
            print("\n默认设备:")
            try:
                default_speaker = sc.default_speaker()
                print(f"  默认扬声器: {default_speaker}")
            except Exception as e:
                print(f"  获取默认扬声器时出错: {e}")
            
            try:
                default_mic = sc.default_microphone()
                print(f"  默认麦克风: {default_mic}")
            except Exception as e:
                print(f"  获取默认麦克风时出错: {e}")
                
        except Exception as e:
            print(f"获取音频设备信息时出错: {e}")
        
        print("="*50 + "\n")
    
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
        self.system_audio_cb = tk.Checkbutton(options_frame, text="系统声音", variable=self.record_system_audio, command=self.check_system_audio)
        self.system_audio_cb.grid(row=1, column=1, sticky=tk.W)
        self.mic_audio_cb = tk.Checkbutton(options_frame, text="麦克风", variable=self.record_mic, command=self.check_mic_audio)
        self.mic_audio_cb.grid(row=1, column=2, sticky=tk.W)
        
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
        
        self.test_button = tk.Button(buttons_frame, text="测试设备", command=self.test_devices, width=15, height=2)
        self.test_button.pack(side=tk.LEFT, padx=10)
        
        quit_button = tk.Button(buttons_frame, text="退出", command=self.quit_app, width=15, height=2)
        quit_button.pack(side=tk.RIGHT, padx=10)
        
        # 状态框架
        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_frame, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # 设备状态框架
        device_status_frame = tk.Frame(self.root, padx=10, pady=5)
        device_status_frame.pack(fill=tk.X, side=tk.BOTTOM, before=status_frame)
        
        tk.Label(device_status_frame, text="设备状态:").pack(anchor=tk.W)
        self.system_audio_status = tk.Label(device_status_frame, text="系统声音: 未测试", fg="gray")
        self.system_audio_status.pack(anchor=tk.W)
        self.mic_audio_status = tk.Label(device_status_frame, text="麦克风: 未测试", fg="gray")
        self.mic_audio_status.pack(anchor=tk.W)
        
        # 快捷键信息
        hotkey_frame = tk.Frame(self.root, padx=10, pady=10)
        hotkey_frame.pack(fill=tk.X, side=tk.BOTTOM, before=device_status_frame)
        
        tk.Label(hotkey_frame, text="快捷键:").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+R: 开始/停止录制").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+Q: 退出应用").pack(anchor=tk.W)
    
    def register_hotkeys(self):
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+alt+r', self.toggle_recording)
        keyboard.add_hotkey('ctrl+alt+q', self.quit_app)
    
    def check_system_audio(self):
        """当用户选择系统声音录制时测试并提供反馈"""
        if self.record_system_audio.get():
            self.test_system_audio()
    
    def check_mic_audio(self):
        """当用户选择麦克风录制时测试并提供反馈"""
        if self.record_mic.get():
            self.test_mic_audio()
    
    def test_system_audio(self):
        """测试系统声音录制功能"""
        temp_recorder = ScreenRecorder(record_system_audio=True, record_mic=False)
        success, message = temp_recorder.test_system_audio()
        
        if success:
            self.system_audio_status.config(text=f"系统声音: 可用", fg="green")
        else:
            self.system_audio_status.config(text=f"系统声音: 不可用", fg="red")
            messagebox.showwarning("系统声音测试", f"系统声音录制可能不可用: {message}\n\n可能的解决方案:\n1. 确保系统声音未静音\n2. 检查Windows声音设置中的'立体声混音'设备\n3. 尝试更新声卡驱动")
    
    def test_mic_audio(self):
        """测试麦克风录制功能"""
        temp_recorder = ScreenRecorder(record_system_audio=False, record_mic=True)
        success, message = temp_recorder.test_mic_audio()
        
        if success:
            self.mic_audio_status.config(text=f"麦克风: 可用", fg="green")
        else:
            self.mic_audio_status.config(text=f"麦克风: 不可用", fg="red")
            messagebox.showwarning("麦克风测试", f"麦克风录制可能不可用: {message}\n\n可能的解决方案:\n1. 确保麦克风未静音\n2. 检查Windows声音设置中的麦克风设备\n3. 尝试更新声卡驱动")
    
    def test_devices(self):
        """测试所有录音设备"""
        print("\n" + "="*50)
        print("[调试] 开始测试录音设备")
        print("-"*50)
        
        # 创建临时录制器进行测试
        temp_recorder = None
        
        if self.record_system_audio.get():
            print("[调试] 测试系统声音录制...")
            temp_recorder = ScreenRecorder(record_system_audio=True, record_mic=False)
            success, message = temp_recorder.test_system_audio()
            
            print(f"[调试] 系统声音测试结果: {'成功' if success else '失败'}")
            print(f"[调试] 系统声音测试消息: {message}")
            
            if success:
                self.system_audio_status.config(text=f"系统声音: 可用", fg="green")
            else:
                self.system_audio_status.config(text=f"系统声音: 不可用", fg="red")
                messagebox.showwarning("系统声音测试", f"系统声音录制可能不可用: {message}\n\n可能的解决方案:\n1. 确保系统声音未静音\n2. 检查Windows声音设置中的'立体声混音'设备\n3. 尝试更新声卡驱动")
        
        if self.record_mic.get():
            print("[调试] 测试麦克风录制...")
            if temp_recorder is None:
                temp_recorder = ScreenRecorder(record_system_audio=False, record_mic=True)
            success, message = temp_recorder.test_mic_audio()
            
            print(f"[调试] 麦克风测试结果: {'成功' if success else '失败'}")
            print(f"[调试] 麦克风测试消息: {message}")
            
            if success:
                self.mic_audio_status.config(text=f"麦克风: 可用", fg="green")
            else:
                self.mic_audio_status.config(text=f"麦克风: 不可用", fg="red")
                messagebox.showwarning("麦克风测试", f"麦克风录制可能不可用: {message}\n\n可能的解决方案:\n1. 确保麦克风未静音\n2. 检查Windows声音设置中的麦克风设备\n3. 尝试更新声卡驱动")
            
        if not self.record_system_audio.get() and not self.record_mic.get():
            print("[调试] 未选择任何录音设备")
            messagebox.showinfo("设备测试", "请先选择要测试的音频设备")
        
        print("="*50 + "\n")
    
    def show_windows_audio_help(self):
        """显示Windows系统声音录制帮助窗口"""
        help_window = tk.Toplevel(self.root)
        help_window.title("系统声音录制帮助")
        help_window.geometry("550x450")
        
        # 添加滚动文本区域
        text_frame = tk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # 帮助内容
        help_text = """
如何启用Windows系统声音录制:

1. 右键点击Windows任务栏上的扬声器图标，选择"声音设置"。

2. 在声音设置中，点击"声音控制面板"。

3. 在弹出的窗口中，切换到"录制"选项卡。

4. 右键点击空白区域，确保勾选了"显示禁用的设备"和"显示断开连接的设备"。

5. 找到"立体声混音"（可能也叫"Stereo Mix"、"What U Hear"或其他名称，取决于声卡）。
   - 注意：并非所有声卡都支持立体声混音功能，这取决于声卡和驱动程序。

6. 右键点击该设备，选择"启用"，然后右键点击并选择"设为默认设备"。

7. 如果看不到"立体声混音"或启用后仍然无法录制，可能是由于以下原因：
   - 声卡不支持此功能
   - 驱动程序未正确安装或配置
   - Windows更新后可能禁用了该功能

解决方案：

A. 更新声卡驱动：
   - 访问声卡制造商的官方网站下载最新驱动
   - 有时官方驱动比Windows自带驱动提供更多功能

B. 使用虚拟音频驱动：
   - 安装虚拟音频设备如VB-Cable（https://vb-audio.com/Cable/）
   - 配置方法：
     1. 下载并安装VB-Cable
     2. 在声音设置中将系统默认输出设置为"CABLE Input"
     3. 在录屏软件中选择"CABLE Output"作为录音输入源

C. 使用替代录制方法：
   - OBS Studio等专业录屏软件提供系统声音捕获功能
   - 某些专业音频接口提供回路功能

D. 检查Windows 10隐私设置：
   - 在Windows设置 > 隐私 > 麦克风中确保应用可以访问麦克风
   - 检查应用权限设置

如果问题仍然存在，请考虑使用上述虚拟音频驱动方案，这是最可靠的替代方法。
        """
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)  # 设为只读
        
        # 关闭按钮
        close_button = tk.Button(help_window, text="关闭", command=help_window.destroy)
        close_button.pack(pady=10)
    
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
            
            # 检查是否有录制警告
            has_warnings = False
            if self.record_system_audio.get() and self.recorder.error_messages["system_audio"]:
                has_warnings = True
            if self.record_mic.get() and self.recorder.error_messages["mic_audio"]:
                has_warnings = True
                
            if has_warnings:
                warning_message = "录制已开始，但存在以下警告:\n\n"
                if self.recorder.error_messages["system_audio"]:
                    warning_message += f"- 系统声音: {self.recorder.error_messages['system_audio']}\n"
                    # 检查是否是常见的系统声音问题
                    if "未找到" in self.recorder.error_messages["system_audio"] or "失败" in self.recorder.error_messages["system_audio"]:
                        warning_message += "\n要解决系统声音录制问题，请点击'帮助'按钮查看详细指南。\n"
                
                if self.recorder.error_messages["mic_audio"]:
                    warning_message += f"- 麦克风: {self.recorder.error_messages['mic_audio']}\n"
                    
                # 创建警告对话框
                warning_dialog = tk.Toplevel(self.root)
                warning_dialog.title("录制警告")
                warning_dialog.geometry("450x250")
                warning_dialog.transient(self.root)
                warning_dialog.grab_set()
                
                # 添加警告内容
                tk.Label(warning_dialog, text=warning_message, justify=tk.LEFT, padx=20, pady=20).pack(fill=tk.BOTH, expand=True)
                
                # 按钮框架
                button_frame = tk.Frame(warning_dialog)
                button_frame.pack(fill=tk.X, padx=10, pady=10)
                
                # 继续按钮
                tk.Button(button_frame, text="继续录制", command=warning_dialog.destroy).pack(side=tk.RIGHT, padx=5)
                
                # 帮助按钮 - 如果是系统声音问题
                if self.recorder.error_messages["system_audio"]:
                    tk.Button(button_frame, text="帮助", command=lambda: [warning_dialog.destroy(), self.show_windows_audio_help()]).pack(side=tk.LEFT, padx=5)
                
                # 停止录制按钮
                tk.Button(button_frame, text="停止录制", command=lambda: [warning_dialog.destroy(), self.stop_recording()]).pack(side=tk.LEFT, padx=5)
                
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
                    if error_messages["system_audio"] and self.record_system_audio.get():
                        warnings.append(f"系统声音: {error_messages['system_audio']}")
                    if error_messages["mic_audio"] and self.record_mic.get():
                        warnings.append(f"麦克风: {error_messages['mic_audio']}")
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