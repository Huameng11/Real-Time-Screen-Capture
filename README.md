# 即时录屏软件

一款简单易用的Windows即时录屏软件，支持区域录制和系统声音同步录制，提供全局快捷键操作。

## 功能特点

- 区域录制
- 系统声音录制
- 全局快捷键控制（开始/停止录制、退出应用）
- 自动检测设备可用性
- 自定义输出路径

## 系统要求

- Windows 10操作系统
- Python 3.8+
- 安装所有依赖项（见requirements.txt）

## 安装

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

## 使用方法

1. 运行主程序:
   ```
   python src/main.py
   ```

2. 设置输出路径
3. 点击"开始录制"按钮或使用快捷键Ctrl+Alt+R
4. 选择要录制的区域
5. 录制完成后，点击"停止录制"按钮或再次使用快捷键Ctrl+Alt+R

## 快捷键

- `Ctrl+Alt+R`: 开始/停止录制
- `Ctrl+Alt+Q`: 退出应用

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

## 开发者信息

本应用使用Python开发，主要依赖以下库：
- mss：屏幕捕捉
- keyboard：全局热键支持
- soundcard：音频录制
- opencv-python：视频处理
- moviepy：音视频合并

## 许可证

[MIT](LICENSE)

## 打包应用

```
pyinstaller --onefile --windowed --icon=assets/icon.ico src/main.py
``` 