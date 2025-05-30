"""
文件名: core/recorder.py
功能: 实现屏幕录制的核心功能，包括视频捕获和处理，
     以及音视频合并处理。支持指定区域录制，
     最终将内容合并为MP4文件或GIF动画输出。
"""

import os
import time
import threading
from datetime import datetime
import cv2
import numpy as np
import mss
from moviepy.editor import VideoFileClip, AudioFileClip, ImageSequenceClip
import imageio

from .audio_manager import AudioManager

class Recorder:
    """屏幕录制器核心类"""
    
    def __init__(self, region=None, output_dir=None, fps=30, output_format="mp4"):
        """初始化录制器
        
        Args:
            region (tuple): 录制区域 (left, top, width, height)
            output_dir (str): 输出目录路径
            fps (int): 帧率
            output_format (str): 输出格式：mp4 或 gif
        """
        self.region = region  # 录制区域 (left, top, width, height)
        self.output_dir = output_dir or os.getcwd()  # 输出目录
        self.fps = fps  # 帧率
        self.running = False  # 录制状态
        self.output_format = output_format.lower()  # 输出格式：mp4 或 gif
        
        # 输出文件路径
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = os.path.join(self.output_dir, f"video_{self.timestamp}.mp4")
        self.system_audio_path = os.path.join(self.output_dir, f"system_audio_{self.timestamp}.wav")
        
        # 根据输出格式设置最终输出文件路径
        if self.output_format == "gif":
            self.output_path = os.path.join(self.output_dir, f"recording_{self.timestamp}.gif")
            # GIF录制时，捕获的帧存储在这里
            self.frames = []
        else:  # 默认为MP4
            self.output_path = os.path.join(self.output_dir, f"recording_{self.timestamp}.mp4")
        
        # 线程
        self.video_thread = None
        
        # 音频管理器
        self.audio_manager = AudioManager(self.system_audio_path) 
        
        # 录制状态错误信息
        self.error_messages = {
            "system_audio": None,
            "video": None
        }
    
    def test_system_audio(self):
        """测试系统音频录制功能是否可用
        
        Returns:
            tuple: (是否可用, 错误信息)
        """
        return self.audio_manager.test_system_audio()
    
    def _record_video(self):
        """视频录制线程函数"""
        try:
            left, top, width, height = self.region
            
            # GIF录制模式
            if self.output_format == "gif":
                # 初始化屏幕捕获
                with mss.mss() as sct:
                    monitor = {"left": left, "top": top, "width": width, "height": height}
                    
                    # 记录帧
                    frame_count = 0
                    start_time = time.time()
                    
                    while self.running:
                        # 捕获屏幕
                        screenshot = sct.grab(monitor)
                        frame = np.array(screenshot)
                        
                        # 转换为RGB格式（GIF使用）
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                        
                        # 存储帧用于后续生成GIF
                        self.frames.append(frame)
                        
                        frame_count += 1
                        
                        # 维持帧率
                        elapsed_time = time.time() - start_time
                        sleep_time = (frame_count / self.fps) - elapsed_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                
                print(f"[调试] GIF录制结束，捕获了 {len(self.frames)} 帧")
            
            # MP4录制模式
            else:
                # 初始化视频写入器
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(self.video_path, fourcc, self.fps, (width, height))
                
                # 初始化屏幕捕获
                with mss.mss() as sct:
                    monitor = {"left": left, "top": top, "width": width, "height": height}
                    
                    # 记录帧
                    frame_count = 0
                    start_time = time.time()
                    
                    while self.running:
                        # 捕获屏幕
                        frame = np.array(sct.grab(monitor))
                        
                        # 转换为BGR格式（OpenCV格式）
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        
                        # 写入视频文件
                        out.write(frame)
                        
                        frame_count += 1
                        
                        # 维持帧率
                        elapsed_time = time.time() - start_time
                        sleep_time = (frame_count / self.fps) - elapsed_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                
                # 释放资源
                out.release()
                
        except Exception as e:
            self.error_messages["video"] = f"录制视频时出错: {str(e)}"
            print(self.error_messages["video"])
    
    def _create_gif(self):
        """从捕获的帧创建GIF动画"""
        try:
            print(f"[调试] 开始创建GIF: {self.output_path}")
            print(f"[调试] 帧数: {len(self.frames)}, 帧率: {self.fps}")
            
            # 使用imageio保存GIF
            imageio.mimsave(
                self.output_path,
                self.frames,
                fps=self.fps,
                optimize=True,
                subrectangles=True
            )
            
            print(f"[调试] GIF已保存到: {self.output_path}")
            return True
        except Exception as e:
            self.error_messages["video"] = f"创建GIF动画时出错: {str(e)}"
            print(f"[错误] {self.error_messages['video']}")
            import traceback
            traceback.print_exc()
            return False
    
    def _merge_audio_video(self):
        """合并音频和视频文件"""
        try:
            print(f"[调试] 开始合并音频和视频...")
            
            # 加载视频和音频
            video = VideoFileClip(self.video_path)
            
            # 检查音频文件是否存在
            if os.path.exists(self.system_audio_path):
                try:
                    audio = AudioFileClip(self.system_audio_path)
                    
                    # 音频时长可能大于视频时长，需要裁剪
                    if audio.duration > video.duration:
                        audio = audio.subclip(0, video.duration)
                    
                    # 设置音频
                    video = video.set_audio(audio)
                except Exception as e:
                    self.error_messages["system_audio"] = f"处理音频时出错: {str(e)}"
                    print(f"[错误] {self.error_messages['system_audio']}")
            else:
                self.error_messages["system_audio"] = "未找到音频文件，输出视频将没有声音"
                print(f"[警告] {self.error_messages['system_audio']}")
            
            # 写入最终视频
            video.write_videofile(
                self.output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=None,
                remove_temp=True,
                preset='ultrafast',
                threads=4
            )
            
            # 关闭并清理
            video.close()
            
            print(f"[调试] 视频已合并并保存到: {self.output_path}")
            return True
        except Exception as e:
            self.error_messages["video"] = f"合并音频和视频时出错: {str(e)}"
            print(f"[错误] {self.error_messages['video']}")
            import traceback
            traceback.print_exc()
            return False
    
    def start(self):
        """开始录制"""
        if self.running:
            print("[警告] 录制已经在进行中")
            return
            
        if not self.region:
            self.error_messages["video"] = "未指定录制区域"
            print(f"[错误] {self.error_messages['video']}")
            return
            
        # 重置错误消息
        self.error_messages = {
            "system_audio": None,
            "video": None
        }
        
        # 标记为运行状态
        self.running = True
        
        # 启动视频录制线程
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        # 如果是MP4格式，启动音频录制（GIF不需要音频）
        if self.output_format == "mp4":
            self.audio_manager.start_recording()
        
        print(f"[调试] 录制已开始，区域: {self.region}, 格式: {self.output_format.upper()}")
    
    def stop(self):
        """停止录制并处理文件
        
        Returns:
            tuple: (输出文件路径, 错误信息字典)
        """
        if not self.running:
            print("[警告] 录制未在进行中")
            return None, self.error_messages
            
        print("[调试] 正在停止录制...")
        
        # 标记为停止状态
        self.running = False
        
        # 等待视频线程完成
        if self.video_thread:
            self.video_thread.join()
            
        # 停止音频录制（如果有）
        if self.output_format == "mp4":
            audio_error = self.audio_manager.stop_recording()
            if audio_error:
                self.error_messages["system_audio"] = audio_error
        
        # 处理文件
        success = False
        if self.output_format == "gif":
            success = self._create_gif()
        else:  # mp4
            success = self._merge_audio_video()
            
        # 清理临时文件
        self._cleanup_temp_files()
        
        if success:
            return self.output_path, self.error_messages
        else:
            return None, self.error_messages
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 如果是MP4格式，清理临时视频和音频文件
            if self.output_format == "mp4":
                if os.path.exists(self.video_path):
                    os.remove(self.video_path)
                    print(f"[调试] 已删除临时视频文件: {self.video_path}")
                    
                if os.path.exists(self.system_audio_path):
                    os.remove(self.system_audio_path)
                    print(f"[调试] 已删除临时音频文件: {self.system_audio_path}")
                    
            # 清空帧列表（如果是GIF）
            if hasattr(self, 'frames'):
                self.frames.clear()
                
        except Exception as e:
            print(f"[警告] 清理临时文件时出错: {str(e)}")
            
    def is_running(self):
        """检查录制是否正在进行
        
        Returns:
            bool: 是否正在录制
        """
        return self.running 