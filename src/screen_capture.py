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
        self.region = region  # (left, top, width, height)
        self.window_handle = window_handle
        self.record_system_audio = record_system_audio
        self.record_mic = record_mic
        self.output_dir = output_dir or os.getcwd()
        self.fps = fps
        self.running = False
        
        # Output file paths
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = os.path.join(self.output_dir, f"video_{self.timestamp}.mp4")
        self.system_audio_path = os.path.join(self.output_dir, f"system_audio_{self.timestamp}.wav")
        self.mic_audio_path = os.path.join(self.output_dir, f"mic_audio_{self.timestamp}.wav")
        self.output_path = os.path.join(self.output_dir, f"recording_{self.timestamp}.mp4")
        
        # Threads
        self.video_thread = None
        self.system_audio_thread = None
        self.mic_audio_thread = None
        
        # Initialize region if window handle is provided
        if self.window_handle and not self.region:
            self.region = self._get_window_region(self.window_handle)
    
    def _get_window_region(self, hwnd):
        """Get region for a specific window handle"""
        rect = win32gui.GetWindowRect(hwnd)
        x, y, w, h = rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
        return (x, y, w, h)
    
    def _record_video(self):
        """Record video thread function"""
        left, top, width, height = self.region
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.video_path, fourcc, self.fps, (width, height))
        
        # Initialize screen capture
        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": width, "height": height}
            
            # Record frames
            frame_count = 0
            start_time = time.time()
            
            while self.running:
                # Capture screen
                frame = np.array(sct.grab(monitor))
                
                # Convert to BGR (OpenCV format)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Write to video file
                out.write(frame)
                
                frame_count += 1
                
                # Maintain FPS
                elapsed_time = time.time() - start_time
                sleep_time = (frame_count / self.fps) - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        # Release resources
        out.release()
    
    def _record_system_audio(self):
        """Record system audio thread function"""
        try:
            # Initialize system audio capture
            sample_rate = 44100  # Hz
            block_size = 1024
            
            # Get default speaker
            speakers = sc.all_speakers()
            if not speakers:
                print("No speakers found")
                return
                
            default_speaker = speakers[0]
            
            # Open audio file for writing
            with wave.open(self.system_audio_path, 'wb') as wf:
                wf.setnchannels(2)  # Stereo
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                
                # Record system audio
                with default_speaker.recorder(samplerate=sample_rate, channels=2, blocksize=block_size) as recorder:
                    while self.running:
                        data = recorder.record(block_size)
                        # Convert to int16 PCM
                        audio_data = (data * 32767).astype(np.int16)
                        wf.writeframes(audio_data.tobytes())
        except Exception as e:
            print(f"Error recording system audio: {e}")
    
    def _record_mic_audio(self):
        """Record microphone audio thread function"""
        try:
            # Initialize microphone capture
            sample_rate = 44100  # Hz
            block_size = 1024
            
            # Get default microphone
            microphones = sc.all_microphones()
            if not microphones:
                print("No microphones found")
                return
                
            default_mic = microphones[0]
            
            # Open audio file for writing
            with wave.open(self.mic_audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                
                # Record microphone audio
                with default_mic.recorder(samplerate=sample_rate, channels=1, blocksize=block_size) as recorder:
                    while self.running:
                        data = recorder.record(block_size)
                        # Convert to int16 PCM
                        audio_data = (data * 32767).astype(np.int16)
                        wf.writeframes(audio_data.tobytes())
        except Exception as e:
            print(f"Error recording microphone audio: {e}")
    
    def _merge_audio_video(self):
        """Merge audio and video files into a single output file"""
        try:
            # Load video
            video = VideoFileClip(self.video_path)
            
            # Audio tracks to combine
            audio_clips = []
            
            # Add system audio if recorded
            if self.record_system_audio and os.path.exists(self.system_audio_path) and os.path.getsize(self.system_audio_path) > 0:
                try:
                    system_audio = AudioFileClip(self.system_audio_path)
                    audio_clips.append(system_audio)
                except Exception as e:
                    print(f"Error loading system audio: {e}")
            
            # Add mic audio if recorded
            if self.record_mic and os.path.exists(self.mic_audio_path) and os.path.getsize(self.mic_audio_path) > 0:
                try:
                    mic_audio = AudioFileClip(self.mic_audio_path)
                    audio_clips.append(mic_audio)
                except Exception as e:
                    print(f"Error loading microphone audio: {e}")
            
            # Combine audio tracks if any
            if audio_clips:
                combined_audio = CompositeAudioClip(audio_clips)
                video = video.set_audio(combined_audio)
            
            # Write final output
            video.write_videofile(self.output_path, codec='libx264', audio_codec='aac')
            
            # Close clips
            video.close()
            for clip in audio_clips:
                clip.close()
            
            return self.output_path
        except Exception as e:
            print(f"Error merging audio and video: {e}")
            # If merging fails, just return the video path
            if os.path.exists(self.video_path):
                return self.video_path
            return None
    
    def start(self):
        """Start recording"""
        if self.running:
            return
        
        self.running = True
        
        # Start video recording thread
        self.video_thread = threading.Thread(target=self._record_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        # Start system audio recording thread if enabled
        if self.record_system_audio:
            self.system_audio_thread = threading.Thread(target=self._record_system_audio)
            self.system_audio_thread.daemon = True
            self.system_audio_thread.start()
        
        # Start microphone recording thread if enabled
        if self.record_mic:
            self.mic_audio_thread = threading.Thread(target=self._record_mic_audio)
            self.mic_audio_thread.daemon = True
            self.mic_audio_thread.start()
    
    def stop(self):
        """Stop recording and produce final output file"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for threads to finish
        if self.video_thread:
            self.video_thread.join()
        
        if self.system_audio_thread:
            self.system_audio_thread.join()
        
        if self.mic_audio_thread:
            self.mic_audio_thread.join()
        
        # Merge audio and video
        output_path = self._merge_audio_video()
        
        # Clean up temporary files
        try:
            # Wait a bit to ensure files are released
            time.sleep(1)
            
            if os.path.exists(self.video_path):
                os.remove(self.video_path)
            if os.path.exists(self.system_audio_path):
                os.remove(self.system_audio_path)
            if os.path.exists(self.mic_audio_path):
                os.remove(self.mic_audio_path)
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")
        
        return output_path 