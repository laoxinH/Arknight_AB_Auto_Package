"""
配置系统测试脚本
用于验证配置管理功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.config_manager import ConfigManager
from src.utils.logger import setup_logger


def test_config_system():
    """测试配置系统"""
    print("=" * 60)
    print("配置系统测试")
    print("=" * 60)
    
    # 初始化日志
    logger = setup_logger()
    
    # 获取配置管理器实例
    config = ConfigManager()
    
    # 测试1: 获取配置文件路径
    print(f"\n1. 配置文件路径: {config.get_config_path()}")
    
    # 测试2: 获取默认配置
    print("\n2. 默认配置:")
    print(f"   主题模式: {config.get('theme_mode')}")
    print(f"   窗口宽度: {config.get('window_width')}")
    print(f"   自动更新: {config.get('auto_check_update')}")
    print(f"   语言: {config.get('language')}")
    
    # 测试3: 设置配置项
    print("\n3. 设置配置项...")
    config.set('theme_mode', 'dark', save_immediately=False)
    config.set('window_width', 1200, save_immediately=False)
    config.set('window_height', 800, save_immediately=False)
    config.set('last_input_dir', 'C:\\Test\\Path', save_immediately=False)
    config.save()
    print("   配置已保存")
    
    # 测试4: 读取修改后的配置
    print("\n4. 读取修改后的配置:")
    print(f"   主题模式: {config.get('theme_mode')}")
    print(f"   窗口宽度: {config.get('window_width')}")
    print(f"   窗口高度: {config.get('window_height')}")
    print(f"   最后输入目录: {config.get('last_input_dir')}")
    
    # 测试5: 批量更新
    print("\n5. 批量更新配置...")
    config.update(
        theme_mode='light',
        window_width=1400,
        window_height=900,
        save_immediately=True
    )
    print(f"   主题模式: {config.get('theme_mode')}")
    print(f"   窗口大小: {config.get('window_width')} x {config.get('window_height')}")
    
    # 测试6: 重新加载配置（模拟程序重启）
    print("\n6. 重新加载配置（模拟程序重启）...")
    config2 = ConfigManager()
    config2.load()
    print(f"   主题模式: {config2.get('theme_mode')}")
    print(f"   窗口大小: {config2.get('window_width')} x {config2.get('window_height')}")
    
    # 测试7: 获取不存在的配置项（使用默认值）
    print("\n7. 获取不存在的配置项:")
    non_exist = config.get('non_existent_key', 'default_value')
    print(f"   non_existent_key: {non_exist}")
    
    # 测试8: 导出配置
    print("\n8. 导出配置...")
    export_path = os.path.join(os.path.dirname(config.config_file), "config_backup.json")
    config.export_config(export_path)
    print(f"   配置已导出到: {export_path}")
    
    print("\n" + "=" * 60)
    print("配置系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_config_system()
