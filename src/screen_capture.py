"""
文件名: screen_capture.py
功能: 实现屏幕录制的核心功能，包括视频捕获、系统音频录制、麦克风录制，
     以及音视频合并处理。支持指定区域或窗口录制，多线程分别处理视频和音频，
     最终将所有内容合并为单个MP4文件输出。
"""

import os
import time
import threading
import cv2
import numpy as np
import mss
import soundcard as sc
import wave
import win32gui
import win32ui
import win32con
import win32api
from datetime import datetime
from PIL import Image
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

class ScreenRecorder:
    def __init__(self, region=None, window_handle=None, record_system_audio=True, record_mic=False, output_dir=None, fps=30):
        self.region = region  # 录制区域 (left, top, width, height)
        self.window_handle = window_handle  # 窗口句柄
        self.record_system_audio = record_system_audio  # 是否录制系统声音
        self.record_mic = record_mic  # 是否录制麦克风
        self.output_dir = output_dir or os.getcwd()  # 输出目录
        self.fps = fps  # 帧率
        self.running = False  # 录制状态
        
        # 输出文件路径
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = os.path.join(self.output_dir, f"video_{self.timestamp}.mp4")
        self.system_audio_path = os.path.join(self.output_dir, f"system_audio_{self.timestamp}.wav")
        self.mic_audio_path = os.path.join(self.output_dir, f"mic_audio_{self.timestamp}.wav")
        self.output_path = os.path.join(self.output_dir, f"recording_{self.timestamp}.mp4")
        
        # 线程
        self.video_thread = None
        self.system_audio_thread = None
        self.mic_audio_thread = None
        
        # 如果提供了窗口句柄但没有区域，则获取窗口区域
        if self.window_handle and not self.region:
            self.region = self._get_window_region(self.window_handle)
    
    def _get_window_region(self, hwnd):
        """获取指定窗口句柄的区域"""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        return (x, y, w, h)
    
    def _record_video(self):
        """视频录制线程函数"""
        left, top, width, height = self.region
        
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
    
    def _record_system_audio(self):
        """系统音频录制线程函数"""
        try:
            # 初始化系统音频捕获
            sample_rate = 44100  # Hz
            block_size = 1024
            
            # 获取默认扬声器
            speakers = sc.all_speakers()
            if not speakers:
                print("未找到扬声器")
                return
                
            default_speaker = speakers[0]
            
            # 打开音频文件进行写入
            with wave.open(self.system_audio_path, 'wb') as wf:
                wf.setnchannels(2)  # 立体声
                wf.setsampwidth(2)  # 16位
                wf.setframerate(sample_rate)
                
                # 录制系统音频
                with default_speaker.recorder(samplerate=sample_rate, channels=2, blocksize=block_size) as recorder:
                    while self.running:
                        data = recorder.record(block_size)
                        # 转换为int16 PCM
                        audio_data = (data * 32767).astype(np.int16)
                        wf.writeframes(audio_data.tobytes())
        except Exception as e:
            print(f"录制系统音频时出错: {e}")
    
    def _record_mic_audio(self):
        """麦克风音频录制线程函数"""
        try:
            # 初始化麦克风捕获
            sample_rate = 44100  # Hz
            block_size = 1024
            
            # 获取默认麦克风
            microphones = sc.all_microphones()
            if not microphones:
                print("未找到麦克风")
                return
                
            default_mic = microphones[0]
            
            # 打开音频文件进行写入
            with wave.open(self.mic_audio_path, 'wb') as wf:
                wf.setnchannels(1)  # 单声道
                wf.setsampwidth(2)  # 16位
                wf.setframerate(sample_rate)
                
                # 录制麦克风音频
                with default_mic.recorder(samplerate=sample_rate, channels=1, blocksize=block_size) as recorder:
                    while self.running:
                        data = recorder.record(block_size)
                        # 转换为int16 PCM
                        audio_data = (data * 32767).astype(np.int16)
                        wf.writeframes(audio_data.tobytes())
        except Exception as e:
            print(f"录制麦克风音频时出错: {e}")
    
    def _merge_audio_video(self):
        """合并音频和视频文件到单个输出文件"""
        try:
            # 加载视频
            video = VideoFileClip(self.video_path)
            
            # 要合并的音频轨道
            audio_clips = []
            
            # 添加系统音频（如果已录制）
            if self.record_system_audio and os.path.exists(self.system_audio_path) and os.path.getsize(self.system_audio_path) > 0:
                try:
                    system_audio = AudioFileClip(self.system_audio_path)
                    audio_clips.append(system_audio)
                except Exception as e:
                    print(f"加载系统音频时出错: {e}")
            
            # 添加麦克风音频（如果已录制）
            if self.record_mic and os.path.exists(self.mic_audio_path) and os.path.getsize(self.mic_audio_path) > 0:
                try:
                    mic_audio = AudioFileClip(self.mic_audio_path)
                    audio_clips.append(mic_audio)
                except Exception as e:
                    print(f"加载麦克风音频时出错: {e}")
            
            # 如果有音频轨道则合并
            if audio_clips:
                combined_audio = CompositeAudioClip(audio_clips)
                video = video.set_audio(combined_audio)
            
            # 写入最终输出
            video.write_videofile(self.output_path, codec='libx264', audio_codec='aac')
            
            # 关闭剪辑
            video.close()
            for clip in audio_clips:
                clip.close()
            
            return self.output_path
        except Exception as e:
            print(f"合并音频和视频时出错: {e}")
            # 如果合并失败，返回视频路径
            if os.path.exists(self.video_path):
                return self.video_path
            return None
    
    def start(self):
        """开始录制"""
        if self.running:
            return
        
        self.running = True
        
        # 启动视频录制线程
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        # 如果启用，启动系统音频录制线程
        if self.record_system_audio:
            self.system_audio_thread = threading.Thread(target=self._record_system_audio)
            self.system_audio_thread.daemon = True
            self.system_audio_thread.start()
        
        # 如果启用，启动麦克风录制线程
        if self.record_mic:
            self.mic_audio_thread = threading.Thread(target=self._record_mic_audio)
            self.mic_audio_thread.daemon = True
            self.mic_audio_thread.start()
    
    def stop(self):
        """停止录制并生成最终输出文件"""
        if not self.running:
            return
        
        self.running = False
        
        # 等待线程完成
        if self.video_thread:
            self.video_thread.join()
        
        if self.system_audio_thread:
            self.system_audio_thread.join()
        
        if self.mic_audio_thread:
            self.mic_audio_thread.join()
        
        # 合并音频和视频
        output_path = self._merge_audio_video()
        
        # 清理临时文件
        try:
            # 等待一段时间确保文件已释放
            time.sleep(1)
            
            if os.path.exists(self.video_path):
                os.remove(self.video_path)
            if os.path.exists(self.system_audio_path):
                os.remove(self.system_audio_path)
            if os.path.exists(self.mic_audio_path):
                os.remove(self.mic_audio_path)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
        
        return output_path 