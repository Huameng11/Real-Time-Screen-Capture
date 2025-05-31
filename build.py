"""
文件名: build.py
功能: 用于将即时录屏项目打包成Windows可执行文件(.exe)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_previous_builds():
    """清理之前的构建文件"""
    print("清理之前的构建文件...")
    
    # 清理dist和build目录
    for folder in ['dist', 'build']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"已删除 {folder} 目录")
    
    # 清理spec文件
    for spec_file in Path('.').glob('*.spec'):
        os.remove(spec_file)
        print(f"已删除 {spec_file}")

def copy_assets():
    """复制资源文件到打包目录"""
    print("复制资源文件...")
    
    # 创建目标目录
    os.makedirs('dist/即时录屏/assets', exist_ok=True)
    
    # 复制资源文件
    if os.path.exists('assets'):
        for item in os.listdir('assets'):
            src = os.path.join('assets', item)
            dst = os.path.join('dist/即时录屏/assets', item)
            
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        print("资源文件复制完成")
    
    # 复制配置文件
    if os.path.exists('config.json'):
        shutil.copy2('config.json', 'dist/即时录屏/config.json')
        print("配置文件复制完成")
    else:
        print("未找到配置文件，将在首次运行时创建")
    
    # 创建README文件
    with open('dist/即时录屏/README.txt', 'w', encoding='utf-8') as f:
        f.write("即时录屏 v1.0.0\n")
        f.write("==============\n\n")
        f.write("快捷键:\n")
        f.write("- Ctrl+Alt+R: 开始/停止录制\n")
        f.write("- Ctrl+Alt+S: 显示/隐藏窗口\n\n")
        f.write("注意事项:\n")
        f.write("1. 首次运行时需要选择录制区域\n")
        f.write("2. 录制的文件默认保存在桌面\n")
        f.write("3. 如遇到问题，请联系开发者\n")
    
    print("README文件创建完成")

def create_windows_shortcut():
    """创建Windows快捷方式"""
    try:
        import win32com.client
        
        print("创建桌面快捷方式...")
        
        # 获取桌面路径
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # 创建快捷方式
        exe_path = os.path.abspath('dist/即时录屏/即时录屏.exe')
        shortcut_path = os.path.join(desktop, '即时录屏.lnk')
        
        shell = win32com.client.Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        
        print(f"快捷方式已创建: {shortcut_path}")
    except Exception as e:
        print(f"创建快捷方式失败: {e}")

def build_executable():
    """使用PyInstaller构建可执行文件"""
    print("开始构建可执行文件...")
    
    # PyInstaller命令参数
    pyinstaller_args = [
        'pyinstaller',
        '--name=即时录屏',
        '--windowed',  # 不显示控制台窗口
        '--noconfirm',  # 不询问覆盖确认
        '--clean',  # 在构建前清理PyInstaller缓存
        '--add-data=assets;assets',  # 添加资源文件
        '--add-data=config.json;.',  # 添加配置文件
        '--icon=assets/icon.ico',  # 添加图标
        '--hidden-import=PIL._tkinter_finder',  # 解决PIL可能的导入问题
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=ttkthemes',
        '--hidden-import=pystray',
        '--hidden-import=soundcard',
        '--hidden-import=imageio',
        '--hidden-import=moviepy',
        '--hidden-import=moviepy.video.io.ffmpeg_tools',
        '--hidden-import=imageio_ffmpeg',
        'src/main.py'  # 入口脚本
    ]
    
    # 过滤掉空参数
    pyinstaller_args = [arg for arg in pyinstaller_args if arg]
    
    # 执行PyInstaller命令
    try:
        subprocess.run(pyinstaller_args, check=True)
        print("构建成功完成!")
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=== 即时录屏应用打包程序 ===")
    
    # 清理之前的构建
    clean_previous_builds()
    
    # 构建可执行文件
    if build_executable():
        # 复制资源文件和配置文件
        copy_assets()
        
        # 创建Windows快捷方式(可选)
        # create_windows_shortcut()
        
        # 打印成功消息
        print("\n打包完成!")
        print(f"可执行文件位置: {os.path.abspath('dist/即时录屏/即时录屏.exe')}")
    else:
        print("\n打包失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 