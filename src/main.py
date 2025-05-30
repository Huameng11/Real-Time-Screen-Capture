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
from PIL import ImageGrab, ImageTk

from screen_capture import ScreenRecorder
from region_selector import RegionSelector

class ScreenRecorderApp:
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("即时录屏")
        self.root.geometry("400x420")  # 增加高度，以适应新增控件
        self.root.resizable(False, False)
        
        # 初始化录制状态和路径
        self.recorder = None
        self.recording = False
        self.output_dir = "C:\\Users\\admin\\desktop"
        self.current_region = None  # 添加存储当前区域信息
        self.region_selected = False  # 新增：标记是否已选择区域
        self.output_format = "mp4"  # 默认输出格式
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
        
        # 录制参数框架
        params_frame = tk.Frame(self.root, padx=10, pady=5)
        params_frame.pack(fill=tk.X)
        
        # 帧率选择
        fps_frame = tk.Frame(params_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(fps_frame, text="帧率:").pack(side=tk.LEFT, padx=(0, 5))
        self.fps_var = tk.StringVar(value="30")
        fps_values = ["15", "24", "30", "60"]
        fps_combobox = ttk.Combobox(fps_frame, textvariable=self.fps_var, values=fps_values, width=5, state="readonly")
        fps_combobox.pack(side=tk.LEFT)
        tk.Label(fps_frame, text="FPS").pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出格式选择
        format_frame = tk.Frame(params_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT, padx=(0, 5))
        self.format_var = tk.StringVar(value="mp4")
        
        # 创建单选按钮组
        mp4_radio = tk.Radiobutton(format_frame, text="MP4 视频", variable=self.format_var, 
                                 value="mp4", command=self.update_format_info)
        mp4_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        gif_radio = tk.Radiobutton(format_frame, text="GIF 动画", variable=self.format_var, 
                                 value="gif", command=self.update_format_info)
        gif_radio.pack(side=tk.LEFT)
        
        # 格式信息标签
        self.format_info_label = tk.Label(params_frame, text="", fg="gray", anchor=tk.W, 
                                        font=("Arial", 8))
        self.format_info_label.pack(fill=tk.X, pady=(0, 5))
        
        # 初始化格式信息
        self.update_format_info()
        
        # 按钮框架
        buttons_frame = tk.Frame(self.root, padx=10, pady=10)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # 区域选择按钮（新增）
        self.select_region_button = tk.Button(buttons_frame, text="选择区域", command=self.select_region, width=15, height=2)
        self.select_region_button.pack(side=tk.LEFT, padx=10)
        
        # 录制按钮（修改）- 初始时禁用
        self.record_button = tk.Button(buttons_frame, text="开始录制", command=self.toggle_recording, width=15, height=2, state=tk.DISABLED)
        self.record_button.pack(side=tk.LEFT, padx=10)
        
        quit_button = tk.Button(buttons_frame, text="退出", command=self.quit_app, width=15, height=2)
        quit_button.pack(side=tk.RIGHT, padx=10)
        
        # 状态框架
        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_frame, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # 录制区域信息框架
        region_info_frame = tk.Frame(self.root, padx=10, pady=5)
        region_info_frame.pack(fill=tk.X, side=tk.BOTTOM, before=status_frame)
        
        # 标题和内容分开显示
        info_header_frame = tk.Frame(region_info_frame)
        info_header_frame.pack(fill=tk.X)
        
        tk.Label(info_header_frame, text="录制区域信息:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, anchor=tk.W)
        
        self.region_info_label = tk.Label(region_info_frame, text="未选择", anchor=tk.W, fg="gray")
        self.region_info_label.pack(fill=tk.X, pady=(0, 5))
        
        # 快捷键信息
        hotkey_frame = tk.Frame(self.root, padx=10, pady=10)
        hotkey_frame.pack(fill=tk.X, side=tk.BOTTOM, before=status_frame)
        
        tk.Label(hotkey_frame, text="快捷键:").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+S: 选择录制区域").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+R: 开始/停止录制").pack(anchor=tk.W)
        tk.Label(hotkey_frame, text="Ctrl+Alt+Q: 退出应用").pack(anchor=tk.W)
        
        # 初始化时检测系统声音设备
        self.check_system_audio()
    
    def register_hotkeys(self):
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+alt+s', self.select_region)  # 新增区域选择快捷键
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
    
    def select_region(self):
        """选择录制区域"""
        try:
            # 隐藏主窗口
            self.root.withdraw()
            
            # 创建区域选择器
            region_selector = RegionSelector(self.root)
            self.root.wait_window(region_selector.top)
            region = region_selector.get_selection()
            
            # 显示主窗口
            self.root.deiconify()
            
            if region:
                # 更新区域信息
                self.update_region_info(region)
                self.region_selected = True
                
                # 启用录制按钮
                self.record_button.config(state=tk.NORMAL)
                self.status_label.config(text="区域已选择，可以开始录制")
            else:
                self.status_label.config(text="区域选择已取消")
        except Exception as e:
            messagebox.showerror("错误", f"选择区域时出错: {str(e)}")
            self.root.deiconify()  # 确保主窗口重新显示
    
    def toggle_recording(self):
        # 切换录制状态
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        try:
            # 检查是否已选择区域
            if not self.region_selected or not self.current_region:
                messagebox.showwarning("警告", "请先选择录制区域")
                return
                
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
            
            # 获取当前输出格式
            output_format = self.format_var.get()
            
            # GIF格式提示
            if output_format == "gif":
                # 估算合理的最大录制时长
                x, y, width, height = self.current_region
                bytes_per_frame = width * height * 3  # RGB每像素3字节
                fps = int(self.fps_var.get())
                seconds = 10  # 假设10秒录制
                total_frames = fps * seconds
                estimated_size_mb = (bytes_per_frame * total_frames) / (1024 * 1024)
                max_time = min(30, int(100 / estimated_size_mb * 10))  # 限制在30秒内
                
                confirm = messagebox.askokcancel(
                    "GIF录制提示", 
                    f"您选择了GIF格式录制，请注意：\n\n"
                    f"1. GIF文件通常较大，特别是高分辨率时\n"
                    f"2. 建议录制时间不超过{max_time}秒\n"
                    f"3. GIF格式不包含声音\n\n"
                    f"是否继续？"
                )
                if not confirm:
                    return
            
            # 使用已选定区域启动录制器
            self.recorder = ScreenRecorder(
                region=self.current_region,
                output_dir=self.output_dir,
                fps=int(self.fps_var.get()),
                output_format=output_format
            )
            
            # 开始录制
            self.recorder.start()
            self.recording = True
            self.record_button.config(text="停止录制")
            self.select_region_button.config(state=tk.DISABLED)  # 录制时禁用区域选择
            self.status_label.config(text=f"正在录制 {output_format.upper()} ...")
            
            # 检查是否有录制警告（仅MP4格式）
            if output_format == "mp4" and self.recorder.error_messages["system_audio"]:
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
                self.select_region_button.config(state=tk.NORMAL)  # 恢复区域选择按钮
                
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
                self.select_region_button.config(state=tk.NORMAL)  # 恢复区域选择按钮
            
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

    def update_region_info(self, region=None):
        """更新区域信息显示"""
        if region:
            x, y, width, height = region
            self.current_region = region
            
            # 计算屏幕分辨率百分比
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            width_percent = round((width / screen_width) * 100, 1)
            height_percent = round((height / screen_height) * 100, 1)
            
            # 获取当前帧率和格式
            fps = self.fps_var.get()
            output_format = self.format_var.get()
            
            # 创建更详细的区域信息
            info_text = (
                f"分辨率: {width} × {height} 像素\n"
                f"屏幕占比: 宽 {width_percent}%, 高 {height_percent}%\n"
                f"位置: 左上角 ({x}, {y})\n"
                f"帧率: {fps} FPS"
            )
            
            # 添加格式信息
            if output_format == "gif":
                # 估算文件大小
                bytes_per_frame = width * height * 3  # RGB每像素3字节
                seconds = 10  # 假设10秒录制
                total_frames = int(fps) * seconds
                estimated_size_mb = (bytes_per_frame * total_frames) / (1024 * 1024)
                
                # 根据分辨率和帧率预估最大合理录制时间
                max_time = min(30, int(100 / estimated_size_mb * 10))  # 限制在30秒内
                
                info_text += f"\n格式: GIF 动画 (建议录制不超过{max_time}秒)"
            else:
                info_text += "\n格式: MP4 视频"
            
            self.region_info_label.config(
                text=info_text,
                fg="green"
            )
        else:
            self.current_region = None
            self.region_selected = False  # 重置区域选择状态
            self.region_info_label.config(
                text="未选择",
                fg="gray"
            )
            # 禁用录制按钮
            self.record_button.config(state=tk.DISABLED)

    def update_format_info(self):
        """根据所选格式更新格式信息提示"""
        selected_format = self.format_var.get()
        
        if selected_format == "gif":
            info_text = "注意: GIF格式文件较大，建议录制时间不要过长，且不包含音频"
            self.format_info_label.config(text=info_text, fg="#FF6600")
        else:
            info_text = "MP4格式可录制视频和系统声音"
            self.format_info_label.config(text=info_text, fg="gray")
        
        # 如果已经选择了区域，更新区域信息
        if self.current_region:
            self.update_region_info(self.current_region)

if __name__ == "__main__":
    app = ScreenRecorderApp()
    app.run() 