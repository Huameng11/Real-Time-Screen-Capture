"""
文件名: build.py
功能: 用于将即时录屏项目打包成Windows可执行文件(.exe)，优化版本
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
        '--noupx',  # 不使用UPX压缩
        '--add-data=assets;assets',  # 添加资源文件
        '--add-data=config.json;.',  # 添加配置文件
        '--icon=assets/icon.ico',  # 添加图标
        '--hidden-import=PIL._tkinter_finder',  # 解决PIL可能的导入问题
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=pystray',
        '--hidden-import=pycaw',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=PySide2',
        '--exclude-module=PySide6',
        '--exclude-module=IPython',
        '--exclude-module=pytest',
        '--exclude-module=sphinx',
        '--exclude-module=notebook',
        '--exclude-module=jupyter',
        '--exclude-module=docutils',
        '--exclude-module=setuptools',
        '--exclude-module=distutils',
        '--exclude-module=moviepy',
        '--exclude-module=imageio_ffmpeg',
        '--exclude-module=soundcard',
        '--exclude-module=ttkthemes',
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

def build_with_nuitka():
    """使用Nuitka构建可执行文件"""
    print("开始使用Nuitka构建可执行文件...")
    
    # Nuitka命令参数
    nuitka_args = [
        'python', '-m', 'nuitka',
        '--standalone',  # 独立模式
        '--windows-disable-console',  # 禁用控制台
        '--windows-icon=assets/icon.ico',  # 设置图标
        '--include-data-dir=assets=assets',  # 包含资源目录
        '--include-data-files=config.json=config.json',  # 包含配置文件
        '--output-dir=dist',  # 输出目录
        '--output-filename=即时录屏.exe',  # 输出文件名
        '--enable-plugin=tk-inter',  # 启用tkinter插件
        '--include-package=PIL',  # 包含PIL
        '--include-package=cv2',  # 包含OpenCV
        '--include-package=numpy',  # 包含numpy
        '--include-package=pystray',  # 包含pystray
        '--include-package=keyboard',  # 包含keyboard
        '--include-package=pycaw',  # 包含pycaw
        '--remove-output',  # 移除之前的输出
        '--assume-yes-for-downloads',  # 自动下载依赖
        '--low-memory',  # 低内存模式
        '--jobs=4',  # 并行编译数
        'src/main.py'  # 入口脚本
    ]
    
    # 执行Nuitka命令
    try:
        subprocess.run(nuitka_args, check=True)
        print("Nuitka构建成功完成!")
        
        # 重命名输出目录
        if os.path.exists('dist/main.dist'):
            os.rename('dist/main.dist', 'dist/即时录屏')
            print("已重命名输出目录")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Nuitka构建失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 即时录屏应用打包程序（优化版）===")
    
    # 清理之前的构建
    clean_previous_builds()
    
    # 选择构建方式
    build_method = input("选择构建方式: 1. PyInstaller  2. Nuitka (推荐) [2]: ").strip() or "2"
    
    success = False
    if build_method == "1":
        # 使用PyInstaller构建
        success = build_executable()
    else:
        # 使用Nuitka构建
        success = build_with_nuitka()
    
    if success:
        # 复制资源文件和配置文件
        copy_assets()
        
        # 打印成功消息
        print("\n打包完成!")
        print(f"可执行文件位置: {os.path.abspath('dist/即时录屏/即时录屏.exe')}")
    else:
        print("\n打包失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 