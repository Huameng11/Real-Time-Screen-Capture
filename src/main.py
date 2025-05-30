"""
文件名: main.py
作者: LI
创建日期: 2024-05-28
最后修改: 2024-06-20
功能: 即时录屏软件的主程序，提供现代化图形用户界面，允许用户选择录制区域，
     控制录制开始和结束，支持系统声音录制，并通过全局快捷键控制。
     支持MP4和GIF格式输出，界面采用现代化天空蓝主题设计。
"""

import os
import sys
import keyboard
import tkinter as tk
from tkinter import messagebox, ttk
import platform
from PIL import ImageGrab, ImageTk, Image, ImageDraw
from ttkthemes import ThemedTk, ThemedStyle
import tempfile
import io

try:
    import pystray
    from pystray import MenuItem as item
    TRAY_SUPPORT = True
except ImportError:
    print("pystray库未安装，系统托盘功能将不可用")
    TRAY_SUPPORT = False

from screen_capture import ScreenRecorder
from region_selector import RegionSelector

# 定义颜色主题
COLORS = {
    "primary": "#2D7DB3",     # 主色调-天空蓝
    "secondary": "#4A6572",   # 次要色调-深灰蓝
    "accent": "#FF5722",      # 强调色-橙色
    "bg": "#F5F7FA",          # 背景色-浅灰
    "text": "#2C3E50",        # 文本色-深蓝灰
    "success": "#4CAF50",     # 成功色-绿色
    "warning": "#FFC107",     # 警告色-黄色
    "error": "#F44336",       # 错误色-红色
    "disabled": "#B0BEC5"     # 禁用色-浅灰
}

class ScreenRecorderApp:
    def __init__(self):
        # 初始化主窗口，使用主题
        self.root = ThemedTk(theme="arc")  # 使用arc主题作为基础
        self.root.title("即时录屏")
        self.root.geometry("450x550")  # 略微增加窗口大小以适应新样式
        self.root.minsize(450, 550)    # 设置最小尺寸，防止窗口过小
        self.root.resizable(True, True)  # 允许调整窗口大小
        self.root.configure(background=COLORS["bg"])
        
        # 窗口状态跟踪
        self.window_visible = True     # 窗口可见状态标记
        
        # 应用自定义样式
        self.setup_styles()
        
        # 初始化录制状态和路径
        self.recorder = None
        self.recording = False
        self.output_dir = "C:\\Users\\admin\\desktop"
        self.current_region = None  # 添加存储当前区域信息
        self.region_selected = False  # 新增：标记是否已选择区域
        self.output_format = "mp4"  # 默认输出格式
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建系统托盘图标
        if TRAY_SUPPORT:
            self.setup_tray()
        
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
    
    def setup_styles(self):
        """设置自定义样式"""
        self.style = ThemedStyle(self.root)
        
        # 配置按钮样式
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Primary.TButton', background=COLORS["primary"], foreground="black")
        self.style.configure('Accent.TButton', background=COLORS["accent"], foreground="black")
        self.style.configure('Secondary.TButton', background=COLORS["secondary"], foreground="black")
        
        # 配置标签样式
        self.style.configure('TLabel', background=COLORS["bg"], foreground=COLORS["text"], font=('Arial', 10))
        self.style.configure('Title.TLabel', font=('Arial', 11, 'bold'))
        self.style.configure('Info.TLabel', foreground=COLORS["primary"])
        self.style.configure('Warning.TLabel', foreground=COLORS["warning"])
        self.style.configure('Error.TLabel', foreground=COLORS["error"])
        self.style.configure('Success.TLabel', foreground=COLORS["success"])
        
        # 配置框架样式
        self.style.configure('TFrame', background=COLORS["bg"])
        self.style.configure('Card.TFrame', relief='raised', borderwidth=1)
        
        # 配置单选按钮样式
        self.style.configure('TRadiobutton', background=COLORS["bg"], foreground=COLORS["text"])
        
        # 配置下拉框样式
        self.style.configure('TCombobox', padding=5)
        
        # 配置输入框样式
        self.style.configure('TEntry', padding=5)
        
        # 配置分组框样式
        self.style.configure('TLabelframe', background=COLORS["bg"], foreground=COLORS["primary"])
        self.style.configure('TLabelframe.Label', background=COLORS["bg"], foreground=COLORS["primary"], font=('Arial', 10, 'bold'))
    
    def setup_ui(self):
        # 创建主容器框架
        main_container = ttk.Frame(self.root, style='TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ===== 输出路径选择框架 =====
        path_frame = ttk.LabelFrame(main_container, text="输出设置", style='TLabelframe')
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        path_content = ttk.Frame(path_frame, style='TFrame')
        path_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(path_content, text="输出路径:", style='TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # 输出路径输入框
        self.output_path_var = tk.StringVar(value=self.output_dir)
        self.output_path_entry = ttk.Entry(path_content, textvariable=self.output_path_var, style='TEntry')
        self.output_path_entry.pack(fill=tk.X)
        
        # ===== 录制参数框架 =====
        params_frame = ttk.LabelFrame(main_container, text="录制参数", style='TLabelframe')
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        params_content = ttk.Frame(params_frame, style='TFrame')
        params_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 系统声音状态
        audio_frame = ttk.Frame(params_content, style='TFrame')
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(audio_frame, text="系统声音:", style='TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.system_audio_status = ttk.Label(audio_frame, text="检测中...", style='Info.TLabel')
        self.system_audio_status.pack(side=tk.LEFT)
        
        # 帧率选择
        fps_frame = ttk.Frame(params_content, style='TFrame')
        fps_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(fps_frame, text="帧率:", style='TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.fps_var = tk.StringVar(value="30")
        fps_values = ["15", "24", "30", "60"]
        fps_combobox = ttk.Combobox(fps_frame, textvariable=self.fps_var, values=fps_values, width=5, state="readonly")
        fps_combobox.pack(side=tk.LEFT)
        ttk.Label(fps_frame, text="FPS", style='TLabel').pack(side=tk.LEFT, padx=(5, 0))
        
        # 输出格式选择
        format_frame = ttk.Frame(params_content, style='TFrame')
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(format_frame, text="输出格式:", style='TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.format_var = tk.StringVar(value="mp4")
        
        # 创建单选按钮组
        mp4_radio = ttk.Radiobutton(format_frame, text="MP4 视频", variable=self.format_var, 
                                   value="mp4", command=self.update_format_info, style='TRadiobutton')
        mp4_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        gif_radio = ttk.Radiobutton(format_frame, text="GIF 动画", variable=self.format_var, 
                                   value="gif", command=self.update_format_info, style='TRadiobutton')
        gif_radio.pack(side=tk.LEFT)
        
        # 格式信息标签
        self.format_info_label = ttk.Label(params_content, text="", style='Info.TLabel')
        self.format_info_label.pack(fill=tk.X)
        
        # 初始化格式信息
        self.update_format_info()
        
        # ===== 按钮框架 =====
        buttons_frame = ttk.Frame(main_container, style='TFrame')
        buttons_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 区域选择按钮
        self.select_region_button = ttk.Button(buttons_frame, text="选择区域", command=self.select_region, 
                                             style='Primary.TButton', width=15)
        self.select_region_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 录制按钮 - 初始时禁用
        self.record_button = ttk.Button(buttons_frame, text="开始录制", command=self.toggle_recording,
                                      style='Accent.TButton', width=15, state=tk.DISABLED)
        self.record_button.pack(side=tk.LEFT)
        
        quit_button = ttk.Button(buttons_frame, text="退出", command=self.quit_app,
                               style='Secondary.TButton', width=15)
        quit_button.pack(side=tk.RIGHT)
        
        # ===== 录制区域信息框架 =====
        region_frame = ttk.LabelFrame(main_container, text="录制区域", style='TLabelframe')
        region_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        region_content = ttk.Frame(region_frame, style='TFrame')
        region_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.region_info_label = ttk.Label(region_content, text="未选择", style='TLabel')
        self.region_info_label.pack(fill=tk.X)
        
        # ===== 快捷键信息 =====
        hotkey_frame = ttk.LabelFrame(main_container, text="快捷键", style='TLabelframe')
        hotkey_frame.pack(fill=tk.BOTH, expand=True)
        
        hotkey_content = ttk.Frame(hotkey_frame, style='TFrame')
        hotkey_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(hotkey_content, text="Ctrl+Alt+S: 选择录制区域", style='TLabel').pack(anchor=tk.W)
        ttk.Label(hotkey_content, text="Ctrl+Alt+R: 开始/停止录制", style='TLabel').pack(anchor=tk.W)
        ttk.Label(hotkey_content, text="Ctrl+Alt+H: 显示/隐藏界面", style='TLabel').pack(anchor=tk.W)
        ttk.Label(hotkey_content, text="Ctrl+Alt+Q: 退出应用", style='TLabel').pack(anchor=tk.W)
        
        # ===== 状态框架 =====
        status_frame = ttk.Frame(self.root, style='TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W, 
                                    padding=(5, 2), background="#f0f0f0")
        self.status_label.pack(fill=tk.X)
        
        # 初始化时检测系统声音设备
        self.check_system_audio()
    
    def register_hotkeys(self):
        # 注册全局快捷键
        keyboard.add_hotkey('ctrl+alt+s', self.select_region)  # 区域选择快捷键
        keyboard.add_hotkey('ctrl+alt+r', self.toggle_recording)
        keyboard.add_hotkey('ctrl+alt+h', self.toggle_window_visibility)  # 窗口显示/隐藏快捷键
        keyboard.add_hotkey('ctrl+alt+q', self.quit_app)
    
    def check_system_audio(self):
        """检测系统声音录制功能并更新状态"""
        temp_recorder = ScreenRecorder()
        success, message = temp_recorder.test_system_audio()
        
        if success:
            self.system_audio_status.config(text="可用", style='Success.TLabel')
        else:
            self.system_audio_status.config(text="不可用", style='Error.TLabel')
            messagebox.showwarning("系统声音检测", f"系统声音录制可能不可用: {message}")
    
    def select_region(self):
        """选择录制区域"""
        try:
            # 保存当前窗口大小和位置
            self.window_geometry = self.root.geometry()
            
            # 隐藏主窗口
            self.root.withdraw()
            
            # 创建区域选择器
            region_selector = RegionSelector(self.root)
            self.root.wait_window(region_selector.top)
            region = region_selector.get_selection()
            
            # 显示主窗口并恢复大小和位置
            self.root.deiconify()
            if hasattr(self, 'window_geometry'):
                self.root.geometry(self.window_geometry)
            
            if region:
                # 更新区域信息
                self.update_region_info(region)
                self.status_label.config(text="区域已选择，可以开始录制")
            else:
                self.status_label.config(text="区域选择已取消")
        except Exception as e:
            messagebox.showerror("错误", f"选择区域时出错: {str(e)}")
            self.root.deiconify()  # 确保主窗口重新显示
            if hasattr(self, 'window_geometry'):
                self.root.geometry(self.window_geometry)
    
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
                
            # 保存当前窗口大小和位置
            self.window_geometry = self.root.geometry()
                
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
            self.record_button.config(text="停止录制", style='Accent.TButton')
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
                self.record_button.config(text="开始录制", style='Accent.TButton')
                self.select_region_button.config(state=tk.NORMAL)  # 恢复区域选择按钮
                
                # 恢复窗口大小和位置
                if hasattr(self, 'window_geometry'):
                    self.root.geometry(self.window_geometry)
                
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
                self.record_button.config(text="开始录制", style='Accent.TButton')
                self.select_region_button.config(state=tk.NORMAL)  # 恢复区域选择按钮
                
                # 恢复窗口大小和位置
                if hasattr(self, 'window_geometry'):
                    self.root.geometry(self.window_geometry)
            
            print("="*50 + "\n")
    
    def quit_app(self):
        # 退出应用
        if self.recording:
            if messagebox.askyesno("确认退出", "录制正在进行中，确定要退出吗？"):
                self.stop_recording()
                self.cleanup_and_exit()
        else:
            self.cleanup_and_exit()
    
    def run(self):
        # 设置关闭窗口时的行为
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
        
    def on_close(self):
        """当用户点击窗口关闭按钮时，最小化到系统托盘"""
        if TRAY_SUPPORT:
            self.toggle_window_visibility()  # 隐藏窗口而不是退出
            messagebox.showinfo("提示", "应用已最小化到系统托盘，按Ctrl+Alt+H可以重新显示窗口")
        else:
            self.quit_app()  # 如果不支持托盘，则直接退出
    
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
            
            self.region_info_label.config(text=info_text, style='Info.TLabel')
            self.region_selected = True
            
            # 启用录制按钮
            self.record_button.config(state=tk.NORMAL)
        else:
            self.current_region = None
            self.region_selected = False  # 重置区域选择状态
            self.region_info_label.config(text="未选择", style='TLabel')
            
            # 禁用录制按钮
            self.record_button.config(state=tk.DISABLED)

    def update_format_info(self):
        """根据所选格式更新格式信息提示"""
        selected_format = self.format_var.get()
        
        if selected_format == "gif":
            info_text = "注意: GIF格式文件较大，建议录制时间不要过长，且不包含音频"
            self.format_info_label.config(text=info_text, style='Warning.TLabel')
        else:
            info_text = "MP4格式可录制视频和系统声音"
            self.format_info_label.config(text=info_text, style='Info.TLabel')
        
        # 如果已经选择了区域，更新区域信息
        if self.current_region:
            self.update_region_info(self.current_region)

    def toggle_window_visibility(self):
        """切换窗口显示/隐藏状态"""
        if self.window_visible:
            # 保存当前窗口状态和位置
            self.window_geometry = self.root.geometry()
            self.root.withdraw()  # 隐藏窗口
            self.window_visible = False
            print("[调试] 窗口已隐藏")
        else:
            # 恢复窗口
            self.root.deiconify()  # 显示窗口
            if hasattr(self, 'window_geometry'):
                self.root.geometry(self.window_geometry)  # 恢复之前的窗口大小和位置
            self.window_visible = True
            print("[调试] 窗口已显示")

    def setup_tray(self):
        """设置系统托盘图标和菜单"""
        # 创建一个简单的图标
        icon_data = self.create_app_icon()
        
        # 托盘菜单项
        menu = (
            item('显示/隐藏', self.toggle_window_visibility),
            item('选择区域', self.select_region),
            item('开始/停止录制', self.toggle_recording),
            item('退出', self.quit_app)
        )
        
        # 创建系统托盘图标
        self.tray_icon = pystray.Icon("ScreenRecorder", icon_data, "即时录屏", menu)
        
        # 在单独的线程中启动托盘图标
        self.tray_icon.run_detached()
        
    def create_app_icon(self):
        """创建应用图标"""
        # 创建一个简单的16x16图标，使用主色调
        img = Image.new('RGB', (64, 64), color=COLORS["primary"])
        draw = ImageDraw.Draw(img)
        
        # 添加一个录制按钮图标
        draw.ellipse((16, 16, 48, 48), fill=COLORS["accent"])
        
        return img

    def cleanup_and_exit(self):
        """清理资源并退出应用"""
        # 注销快捷键
        try:
            keyboard.unhook_all()
        except:
            pass
            
        # 销毁托盘图标
        if TRAY_SUPPORT and hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
            
        # 退出应用
        self.root.quit()

if __name__ == "__main__":
    app = ScreenRecorderApp()
    app.run() 