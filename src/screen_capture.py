"""
文件名: screen_capture.py
功能: 实现屏幕录制的核心功能，包括视频捕获和系统音频录制，
     以及音视频合并处理。支持指定区域录制，多线程分别处理视频和音频，
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
from datetime import datetime
from moviepy.editor import VideoFileClip, AudioFileClip

class ScreenRecorder:
    def __init__(self, region=None, output_dir=None, fps=30):
        self.region = region  # 录制区域 (left, top, width, height)
        self.output_dir = output_dir or os.getcwd()  # 输出目录
        self.fps = fps  # 帧率
        self.running = False  # 录制状态
        
        # 输出文件路径
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = os.path.join(self.output_dir, f"video_{self.timestamp}.mp4")
        self.system_audio_path = os.path.join(self.output_dir, f"system_audio_{self.timestamp}.wav")
        self.output_path = os.path.join(self.output_dir, f"recording_{self.timestamp}.mp4")
        
        # 线程
        self.video_thread = None
        self.system_audio_thread = None
        
        # 录制状态错误信息
        self.error_messages = {
            "system_audio": None,
            "video": None
        }
    
    def test_system_audio(self):
        """测试系统音频录制功能是否可用，返回(是否可用, 错误信息)"""
        try:
            print(f"[调试] 开始测试系统音频录制功能")
            
            # 获取带有回路(loopback)功能的录音设备
            loopback_devices = sc.all_microphones(include_loopback=True)
            print(f"[调试] 检测到的回路设备: {loopback_devices}")
            
            # 过滤出真正的回路设备（通常是扬声器设备的回路）
            speaker_loopbacks = [device for device in loopback_devices if 'Speaker' in str(device) or '扬声器' in str(device)]
            print(f"[调试] 扬声器回路设备: {speaker_loopbacks}")
            
            if not speaker_loopbacks:
                print(f"[错误] 未找到系统声音回路设备")
                return False, "未找到系统声音回路设备，无法录制系统声音"
            
            # 使用第一个回路设备
            loopback_device = speaker_loopbacks[0]
            print(f"[调试] 使用系统声音回路设备: {loopback_device}")
            
            # 尝试创建录音机
            print(f"[调试] 尝试创建录音机实例...")
            with loopback_device.recorder(samplerate=44100, channels=2, blocksize=1024) as recorder:
                print(f"[调试] 录音机实例创建成功，尝试录制测试数据...")
                # 尝试录制一小段
                data = recorder.record(100)  # 只录制100帧进行测试
                print(f"[调试] 测试数据录制完成，数据形状: {data.shape if data is not None else 'None'}")
                
                if data is None or len(data) == 0:
                    print(f"[错误] 录制测试返回空数据")
                    return False, "录制测试返回空数据"
                
                # 检查音频数据是否全为0或接近0(静音)
                max_amplitude = np.max(np.abs(data))
                print(f"[调试] 测试数据最大振幅: {max_amplitude}")
                
                if max_amplitude < 0.0001:
                    print(f"[警告] 录音设备工作，但可能未检测到声音（系统静音或没有播放内容）")
                    return True, "录音设备工作，但可能未检测到声音（可能是系统静音或没有播放内容）"
                
                print(f"[调试] 系统声音录制功能正常")
                return True, "系统声音录制功能正常"
        except Exception as e:
            error_msg = f"系统声音录制测试失败: {str(e)}"
            print(f"[错误] {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def _record_video(self):
        """视频录制线程函数"""
        try:
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
        except Exception as e:
            self.error_messages["video"] = f"录制视频时出错: {str(e)}"
            print(self.error_messages["video"])
    
    def _record_system_audio(self):
        """系统音频录制线程函数"""
        try:
            # 初始化系统音频捕获
            sample_rate = 44100  # Hz
            block_size = 1024
            
            print(f"[调试] 开始尝试录制系统音频")
            
            # 获取回路录音设备
            try:
                # 获取带有回路功能的录音设备
                loopback_devices = sc.all_microphones(include_loopback=True)
                print(f"[调试] 检测到的回路设备: {loopback_devices}")
                
                # 过滤出真正的回路设备（通常是扬声器设备的回路）
                speaker_loopbacks = [device for device in loopback_devices if 'Speaker' in str(device) or '扬声器' in str(device)]
                print(f"[调试] 扬声器回路设备: {speaker_loopbacks}")
                
                if not speaker_loopbacks:
                    error_msg = "未找到系统声音回路设备，无法录制系统声音"
                    self.error_messages["system_audio"] = error_msg
                    print(f"[错误] {error_msg}")
                    return
                    
                # 使用第一个回路设备
                loopback_device = speaker_loopbacks[0]
                print(f"[调试] 使用系统声音回路设备: {loopback_device}")
            except Exception as e:
                error_msg = f"获取系统声音回路设备时出错: {str(e)}"
                self.error_messages["system_audio"] = error_msg
                print(f"[错误] {error_msg}")
                import traceback
                traceback.print_exc()
                return
            
            # 打开音频文件进行写入
            try:
                with wave.open(self.system_audio_path, 'wb') as wf:
                    wf.setnchannels(2)  # 立体声
                    wf.setsampwidth(2)  # 16位
                    wf.setframerate(sample_rate)
                    print(f"[调试] 已创建音频文件: {self.system_audio_path}")
                    
                    # 录制系统音频
                    try:
                        print(f"[调试] 开始创建录音机实例...")
                        with loopback_device.recorder(samplerate=sample_rate, channels=2, blocksize=block_size) as recorder:
                            print(f"[调试] 录音机实例创建成功")
                            empty_frames = 0  # 计数器，记录连续的空帧
                            frames_recorded = 0  # 记录已录制的帧数
                            
                            while self.running:
                                try:
                                    print(f"[调试] 正在录制第 {frames_recorded+1} 个音频块...") if frames_recorded < 5 else None
                                    data = recorder.record(block_size)
                                    frames_recorded += 1
                                    
                                    # 检查是否有实际声音数据
                                    max_amplitude = np.max(np.abs(data))
                                    if max_amplitude < 0.0001:
                                        empty_frames += 1
                                        if empty_frames == 1 or empty_frames % 50 == 0:  # 第一帧为空或每隔约1秒检查一次
                                            print(f"[警告] 系统声音似乎没有被捕获 ({empty_frames} 个空帧), 最大振幅: {max_amplitude}")
                                    else:
                                        if empty_frames > 0:
                                            print(f"[调试] 检测到有效音频数据，最大振幅: {max_amplitude}")
                                        empty_frames = 0  # 重置计数器
                                    
                                    # 转换为int16 PCM
                                    audio_data = (data * 32767).astype(np.int16)
                                    wf.writeframes(audio_data.tobytes())
                                    
                                    if frames_recorded == 5:
                                        print(f"[调试] 已成功录制初始音频块，继续录制中...")
                                except Exception as e:
                                    error_msg = f"录制音频数据时出错: {str(e)}"
                                    print(f"[错误] {error_msg}")
                                    import traceback
                                    traceback.print_exc()
                                    # 尝试继续录制而不中断
                    except Exception as e:
                        error_msg = f"创建录音机实例时出错: {str(e)}"
                        self.error_messages["system_audio"] = error_msg
                        print(f"[错误] {error_msg}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                error_msg = f"创建音频文件时出错: {str(e)}"
                self.error_messages["system_audio"] = error_msg
                print(f"[错误] {error_msg}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            error_msg = f"录制系统音频时出错: {str(e)}"
            self.error_messages["system_audio"] = error_msg
            print(f"[错误] {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _merge_audio_video(self):
        """合并音频和视频文件到单个输出文件"""
        try:
            # 加载视频
            video = VideoFileClip(self.video_path)
            
            # 添加系统音频（如果已录制）
            if os.path.exists(self.system_audio_path) and os.path.getsize(self.system_audio_path) > 0:
                try:
                    system_audio = AudioFileClip(self.system_audio_path)
                    video = video.set_audio(system_audio)
                except Exception as e:
                    print(f"加载系统音频时出错: {e}")
            
            # 写入最终输出
            video.write_videofile(self.output_path, codec='libx264', audio_codec='aac')
            
            # 关闭剪辑
            video.close()
            
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
        
        # 重置错误信息
        self.error_messages = {
            "system_audio": None,
            "video": None
        }
        
        # 测试系统声音录制
        success, message = self.test_system_audio()
        if not success:
            print(f"警告: {message}")
            # 不阻止录制，但保存错误信息
            self.error_messages["system_audio"] = message
        
        self.running = True
        
        # 启动视频录制线程
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        # 启动系统音频录制线程
        self.system_audio_thread = threading.Thread(target=self._record_system_audio)
        self.system_audio_thread.daemon = True
        self.system_audio_thread.start()
    
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
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
        
        return output_path, self.error_messages 