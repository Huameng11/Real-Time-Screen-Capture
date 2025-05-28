# 即时录屏软件

一款 Windows 桌面即时录屏软件，实现便捷的窗口/区域选择、音视频同步录制，并支持快捷键即时触发。

## 功能特点

- 窗口/区域选择录制
- 系统声音和麦克风音频同步录制
- 全局快捷键触发录制
- 高效的视频编码与封装

## 环境要求

- Windows 10/11
- Python 3.8+

## 安装与使用

1. 克隆仓库
2. 创建并激活虚拟环境
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. 安装依赖
   ```
   pip install -r requirements.txt
   ```
4. 运行应用
   ```
   python src/main.py
   ```

## 快捷键

- `Ctrl+Alt+R`: 开始/停止录制
- `Ctrl+Alt+Q`: 退出应用

## 打包应用

```
pyinstaller --onefile --windowed --icon=assets/icon.ico src/main.py
``` 