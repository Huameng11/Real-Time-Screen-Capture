"""
文件名: core/audio_manager.py
功能: 管理系统音频录制，提供音频捕获和处理功能
"""

import os
import wave
import threading
import numpy as np
import soundcard as sc

class AudioManager:
    """音频管理器，负责系统音频的检测和录制"""
    
    def __init__(self, output_file=None):
        """初始化音频管理器
        
        Args:
            output_file (str, optional): 音频输出文件路径
        """
        self.output_file = output_file
        self.running = False
        self.audio_thread = None
        self.error_message = None
    
    def test_system_audio(self):
        """测试系统音频录制功能是否可用
        
        Returns:
            tuple: (是否可用, 错误信息)
        """
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
    
    def start_recording(self):
        """开始录制系统音频"""
        if self.running:
            print("[警告] 音频录制已经在运行")
            return
            
        if not self.output_file:
            self.error_message = "未指定输出文件路径"
            print(f"[错误] {self.error_message}")
            return
            
        self.running = True
        self.error_message = None
        
        # 启动录制线程
        self.audio_thread = threading.Thread(target=self._record_system_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        print(f"[调试] 系统音频录制已启动，输出到: {self.output_file}")
    
    def stop_recording(self):
        """停止录制系统音频
        
        Returns:
            str: 错误信息（如果有）
        """
        self.running = False
        
        if self.audio_thread:
            self.audio_thread.join(timeout=5)  # 等待线程结束，最多5秒
            self.audio_thread = None
            
        print("[调试] 系统音频录制已停止")
        return self.error_message
    
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
                    self.error_message = error_msg
                    print(f"[错误] {error_msg}")
                    return
                    
                # 使用第一个回路设备
                loopback_device = speaker_loopbacks[0]
                print(f"[调试] 使用系统声音回路设备: {loopback_device}")
                
                # 开始录制
                print(f"[调试] 开始录制系统音频...")
                
                # 打开WAV文件准备写入
                with wave.open(self.output_file, 'wb') as wf:
                    wf.setnchannels(2)  # 立体声
                    wf.setsampwidth(2)  # 16位采样宽度
                    wf.setframerate(sample_rate)
                    
                    # 创建录音机并开始录制
                    with loopback_device.recorder(samplerate=sample_rate, channels=2, blocksize=block_size) as recorder:
                        print(f"[调试] 录音机已创建，开始录制...")
                        
                        # 持续录制直到停止信号
                        while self.running:
                            # 录制一块音频数据
                            data = recorder.record(block_size)
                            
                            # 检查数据
                            if data is None or len(data) == 0:
                                print(f"[警告] 录制返回空数据")
                                continue
                                
                            # 转换为16位整数并写入WAV文件
                            # 首先规范化到[-1, 1]范围，然后缩放到16位整数范围
                            int_data = (data * 32767).astype(np.int16)
                            wf.writeframes(int_data.tobytes())
            
            except Exception as e:
                self.error_message = f"系统音频录制过程中出错: {str(e)}"
                print(f"[错误] {self.error_message}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            self.error_message = f"系统音频录制线程启动失败: {str(e)}"
            print(f"[错误] {self.error_message}")
            import traceback
            traceback.print_exc()
    
    def get_available_devices(self):
        """获取可用的音频设备
        
        Returns:
            tuple: (扬声器列表, 回路设备列表, 默认扬声器)
        """
        try:
            # 扬声器
            speakers = sc.all_speakers()
            
            # 回路设备
            loopback_devices = sc.all_microphones(include_loopback=True)
            speaker_loopbacks = [device for device in loopback_devices if 'Speaker' in str(device) or '扬声器' in str(device)]
            
            # 默认设备
            try:
                default_speaker = sc.default_speaker()
            except Exception:
                default_speaker = None
                
            return speakers, speaker_loopbacks, default_speaker
            
        except Exception as e:
            print(f"[错误] 获取音频设备信息失败: {str(e)}")
            return [], [], None
            
    def set_output_file(self, output_file):
        """设置输出文件路径
        
        Args:
            output_file (str): 输出文件路径
        """
        self.output_file = output_file 