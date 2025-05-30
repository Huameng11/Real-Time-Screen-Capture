"""
文件名: utils/config_manager.py
功能: 管理应用配置和用户设置，提供配置读写功能
"""

import os
import json
import platform
from pathlib import Path
from functools import lru_cache

# 默认配置
DEFAULT_CONFIG = {
    "output_dir": str(Path.home() / "Desktop"),
    "fps": 30,
    "output_format": "mp4",
    "region": None,
    "ui": {
        "theme": "arc",
        "window_geometry": "450x550",
        "window_visible": True
    }
}

class ConfigManager:
    """配置管理器，负责读写应用配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 确定配置文件路径 - 使用当前脚本运行目录
        self.config_dir = os.getcwd()
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件
        
        Returns:
            dict: 配置字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（确保新增的配置项有默认值）
                return self._merge_configs(DEFAULT_CONFIG, config)
            except Exception as e:
                print(f"[错误] 加载配置文件失败: {str(e)}")
        
        # 如果配置文件不存在或加载失败，使用默认配置
        return DEFAULT_CONFIG.copy()
    
    @staticmethod
    def _merge_configs(default_config, user_config):
        """合并默认配置和用户配置
        
        Args:
            default_config (dict): 默认配置
            user_config (dict): 用户配置
            
        Returns:
            dict: 合并后的配置
        """
        merged = default_config.copy()
        
        # 递归合并字典
        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = ConfigManager._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"[调试] 配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"[错误] 保存配置失败: {str(e)}")
    
    def get(self, key, default=None):
        """获取配置项值
        
        Args:
            key (str): 配置项键名，支持使用点号分隔的多级键名
            default: 默认值（如果键不存在）
            
        Returns:
            配置项的值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key, value):
        """设置配置项值
        
        Args:
            key (str): 配置项键名，支持使用点号分隔的多级键名
            value: 要设置的值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历除最后一个键之外的所有键，确保路径存在
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
            
        # 设置最后一个键的值
        config[keys[-1]] = value
    
    def update_region(self, region):
        """更新录制区域配置
        
        Args:
            region (tuple): 录制区域 (x, y, width, height)
        """
        self.set('region', region)
        self.save_config()
    
    def update_ui_geometry(self, geometry):
        """更新窗口几何信息
        
        Args:
            geometry (str): 窗口几何信息，例如"450x550+100+100"
        """
        self.set('ui.window_geometry', geometry)
        self.save_config()
    
    @lru_cache(maxsize=8)
    def get_cached(self, key, default=None):
        """获取缓存的配置项值（用于频繁访问的配置）
        
        Args:
            key (str): 配置项键名
            default: 默认值（如果键不存在）
            
        Returns:
            配置项的值
        """
        return self.get(key, default) 