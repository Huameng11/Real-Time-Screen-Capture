# 即时录屏软件

一款简单易用的Windows即时录屏软件，支持区域录制和系统声音同步录制，提供全局快捷键操作，界面美观实用。

## 功能特点

- 区域选择录制，显示区域大小及分辨率信息
- 系统声音录制功能
- 支持MP4和GIF格式输出
- 全局快捷键控制（录制、显示/隐藏窗口）
- 自动检测设备可用性
- 自定义输出路径
- 现代化界面设计，支持窗口自由拉伸
- 系统托盘功能，最小化后继续工作
- 实时调试日志显示

## 系统要求

- Windows 10操作系统
- 2GB以上内存
- 100MB可用磁盘空间

## 安装

### 已打包版本

直接下载发布版本的exe文件，双击运行即可使用。

### 从源码运行

1. 克隆或下载本仓库

2. 创建虚拟环境（推荐）:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

4. 运行主程序:
   ```
   python src/main.py
   ```

## 使用方法

1. 设置输出路径和格式（MP4或GIF）
2. 点击"选择区域"按钮选择要录制的区域
3. 点击"开始录制"按钮或使用快捷键Ctrl+Alt+R开始录制
4. 录制完成后，点击"停止录制"按钮或再次使用快捷键Ctrl+Alt+R
5. 录制文件会自动保存到设置的输出路径

## 快捷键

- `Ctrl+Alt+R`: 开始/停止录制
- `Ctrl+Alt+S`: 显示/隐藏窗口

## 常见问题解决

### 无法录制系统声音

如果无法录制系统声音，请尝试以下解决方法：

1. **检查声卡设置**：
   - 确保系统声音未静音
   - 在Windows声音设置中启用"立体声混音"设备
   - 将"立体声混音"设为默认录制设备

2. **使用虚拟音频设备**：
   - 安装虚拟音频设备如VB-Cable（https://vb-audio.com/Cable/）
   - 配置Windows将系统声音输出到虚拟设备

### 界面显示异常

如果界面显示异常，可尝试以下解决方法：
- 确保已安装最新版本
- 检查系统DPI设置是否为100%
- 重新启动应用程序

## 开发者信息

本应用使用Python开发，主要依赖以下库：
- mss：屏幕捕捉
- pillow：图像处理
- keyboard：全局热键支持
- soundcard：音频录制
- opencv-python：视频处理
- moviepy：音视频合并
- ttkthemes：界面主题
- pystray：系统托盘支持
- imageio：GIF生成

开发者：睡到自然醒WakeUp  
B站主页：[@睡到自然醒WakeUp](https://space.bilibili.com/39979167)

## 许可证

[MIT](LICENSE)

## 从源码打包应用

使用提供的打包脚本：
```
python build.py
```

或手动使用PyInstaller：
```
pyinstaller --name=即时录屏 --windowed --icon=assets/icon.ico --add-data=assets;assets --add-data=config.json;. src/main.py
``` 