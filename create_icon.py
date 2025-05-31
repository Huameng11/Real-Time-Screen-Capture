"""
文件名: create_icon.py
功能: 创建应用图标
"""

import os
from PIL import Image, ImageDraw

def create_icon():
    """创建应用图标"""
    # 确保assets目录存在
    if not os.path.exists('assets'):
        os.makedirs('assets')
        print("已创建assets目录")
    
    # 创建一个正方形图像
    size = 256
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # 绘制圆形背景
    center = size // 2
    radius = size // 2 - 10
    draw.ellipse(
        [(center - radius, center - radius), (center + radius, center + radius)], 
        fill=(30, 136, 229, 255)  # 主蓝色
    )
    
    # 绘制录制按钮（内圆）
    inner_radius = radius // 2
    draw.ellipse(
        [(center - inner_radius, center - inner_radius), 
         (center + inner_radius, center + inner_radius)], 
        fill=(229, 57, 53, 255)  # 红色
    )
    
    # 保存为ico文件
    icon_path = os.path.join('assets', 'icon.ico')
    image.save(icon_path, format='ICO', sizes=[(256, 256)])
    print(f"图标已保存到 {icon_path}")

if __name__ == "__main__":
    create_icon() 