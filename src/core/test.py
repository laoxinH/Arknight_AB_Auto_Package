"""
批量资源替换器
"""
import logging
import os
from typing import Optional
from pathlib import Path

import UnityPy
from PIL import Image
from UnityPy.enums import TextureFormat

class AssetBatchReplacer:
    """批量资源替换器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化批量资源替换器
        
        Args:
            output_dir: 输出目录，如果为None则使用当前目录
        """
        self.output_dir = output_dir or os.getcwd()
        self.logger = logging.getLogger(__name__)
        
    def replace_spine_files(self, data_dir: str, replace_dir: str, target_dir: str) -> bool:
        """
        替换Spine动画资源
        
        Args:
            data_dir: 原始资源目录
            replace_dir: 替换资源目录
            target_dir: 目标输出目录
            
        Returns:
            bool: 是否替换成功
        """
        try:
            # 参数验证
            if not os.path.exists(data_dir):
                raise FileNotFoundError(f"原始资源目录不存在: {data_dir}")
            if not os.path.exists(replace_dir):
                raise FileNotFoundError(f"替换资源目录不存在: {replace_dir}")
                
            # 创建目标目录
            target_path = Path(target_dir)
            if not target_path.parent.exists():
                target_path.parent.mkdir(parents=True)
                self.logger.info(f"创建目录: {target_path.parent}")
                
            # 遍历原始资源目录
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if not file.endswith('.ab'):
                        continue
                        
                    self.logger.info(f"处理文件: {file}")
                    
                    try:
                        # 构建路径
                        full_path = os.path.normpath(os.path.join(root, file))
                        base_path = os.path.normpath(data_dir)
                        relative_path = os.path.relpath(full_path, base_path)
                        bundle_path = os.path.join(root, file)
                        
                        # 加载资源包
                        env = UnityPy.load(bundle_path)
                        
                        # 处理资源包中的对象
                        for obj in env.objects:
                            try:
                                if obj.type.name == 'TextAsset':
                                    data = obj.read()
                                    
                                    # 处理.skel文件
                                    if data.m_Name.endswith('.skel'):
                                        for root1, dirs1, files1 in os.walk(replace_dir):
                                            for file1 in files1:
                                                if file1 == data.m_Name:
                                                    fp = os.path.join(root1, file1)
                                                    self.logger.info(f"替换.skel文件: {fp}")
                                                    with open(fp, 'rb') as f:
                                                        data.m_Script = f.read().decode("utf-8", "surrogateescape")
                                                    data.save()
                                                    self.logger.info(f"已替换.skel文件: {data.m_Name}")
                                                    
                                    # 处理.atlas文件
                                    elif data.m_Name.endswith('.atlas'):
                                        for root1, dirs1, files1 in os.walk(replace_dir):
                                            for file1 in files1:
                                                if file1 == data.m_Name:
                                                    fp = os.path.join(root1, file1)
                                                    # 检查关联文件
                                                    json_path = os.path.join(root1, data.m_Name.replace('.atlas', '.json'))
                                                    skel_path = os.path.join(root1, data.m_Name.replace('.atlas', '.skel'))
                                                    if os.path.exists(json_path):
                                                        if not os.path.exists(skel_path):
                                                            self.logger.info(f"找到.json文件但缺少.skel文件，跳过: {data.m_Name}")
                                                            continue
                                                    self.logger.info(f"替换.atlas文件: {fp}")
                                                    with open(fp, 'rb') as f:
                                                        data.m_Script = f.read().decode("utf-8", "surrogateescape")
                                                    data.save()
                                                    self.logger.info(f"已替换.atlas文件: {data.m_Name}")
                                                    
                                elif obj.type.name == 'Texture2D':
                                    data = obj.read()
                                    for root1, dirs1, files1 in os.walk(replace_dir):
                                        for file1 in files1:
                                            if f"{data.m_Name}_{obj.path_id}.png" == file1:
                                                # 检查关联文件
                                                json_path = os.path.join(root1, f"{data.m_Name}.json")
                                                skel_path = os.path.join(root1, f"{data.m_Name}.skel")
                                                if os.path.exists(json_path):
                                                    if not os.path.exists(skel_path):
                                                        self.logger.info(f"找到.json文件但缺少.skel文件，跳过: {data.m_Name}")
                                                        continue
                                                # 替换图片
                                                fp = os.path.join(root1, file1)
                                                self.logger.info(f"替换图片: {fp}")
                                                pil_img = Image.open(fp)
                                                data.set_image(img=pil_img, target_format=TextureFormat.RGBA32)
                                                data.save()
                                                self.logger.info(f"已替换图片: {data.m_Name}")
                                                
                            except Exception as e:
                                self.logger.error(f"处理对象时出错: {str(e)}")
                                continue
                                
                        # 保存修改后的资源包
                        output_path = os.path.join(target_dir, relative_path)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            envdata = env.file.save(packer="lz4")
                            f.write(envdata)
                        self.logger.info(f"已保存资源包: {output_path}")
                        
                    except Exception as e:
                        self.logger.error(f"处理资源包 {bundle_path} 时出错: {str(e)}")
                        continue
                        
            return True
            
        except Exception as e:
            self.logger.error(f"批量替换资源时出错: {str(e)}")
            return False

def main():
    import os

def get_relative_path(full_path, base_path):
    # 规范化路径
    full_path = os.path.normpath(full_path)
    base_path = os.path.normpath(base_path)

    # 获取相对路径
    relative_path = os.path.relpath(full_path, base_path)
    return relative_path

# 示例
full_path = "C:/a/v/b.txt"
base_path = "C:/a\\"
result = get_relative_path(full_path, base_path)
print(result)  # 输出: v/b.txt


main()
