"""
测试配置集成功能
"""
from src.config.config_manager import ConfigManager

def test_config():
    """测试所有配置项"""
    config = ConfigManager()
    
    print("=" * 50)
    print("配置集成测试")
    print("=" * 50)
    
    # 测试主题设置
    print("\n【主题设置】")
    print(f"主题模式: {config.get('theme_mode', 'auto')}")
    
    # 测试日志设置
    print("\n【日志设置】")
    print(f"日志启用: {config.get('log_enabled', True)}")
    print(f"日志等级: {config.get('log_level', 'INFO')}")
    
    # 测试路径设置
    print("\n【路径设置】")
    print(f"上次输入目录: {config.get('last_input_dir', '未设置')}")
    print(f"上次输出目录: {config.get('last_output_dir', '未设置')}")
    
    # 测试AB导出设置
    print("\n【资源编辑设置】")
    print(f"AB导出默认目录: {config.get('ab_export_default_dir', '未设置')}")
    
    # 测试实验室MOD设置
    print("\n【实验室MOD设置】")
    password = config.get('lab_mod_default_password', '')
    print(f"默认压缩密码: {'已设置' if password else '未设置'} (长度: {len(password)})")
    print(f"默认启用图种: {config.get('lab_mod_enable_image_steganography', False)}")
    description = config.get('lab_mod_default_description', '')
    print(f"默认MOD描述: {'已设置' if description else '未设置'} (长度: {len(description)}字符)")
    print(f"MOD导出默认目录: {config.get('lab_mod_export_default_dir', '未设置')}")
    
    # 测试窗口设置
    print("\n【窗口设置】")
    print(f"窗口宽度: {config.get('window_width', '未设置')}")
    print(f"窗口高度: {config.get('window_height', '未设置')}")
    print(f"窗口最大化: {config.get('window_maximized', False)}")
    
    print("\n" + "=" * 50)
    print(f"配置文件位置: {config.get_config_path()}")
    print("=" * 50)

if __name__ == "__main__":
    test_config()
