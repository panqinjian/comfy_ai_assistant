"""
ComfyUI AI Assistant 插件入口
"""
import os
import platform
import sys
import importlib
import importlib.util
from aiohttp import web


current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import ai_services  
except ImportError as e:
    print(f"ComfyUI AI Assistant: 导入服务模块失败: {e}")


def mklink_web_extensions(link_name, link_target):
    try:
        # 删除已存在的链接
        if os.path.exists(link_name):
            if platform.system() == "Windows":
                os.system(f'rmdir "{link_name}"')
            else:
                os.remove(link_name)
        
        # 创建链接
        if platform.system() == "Windows":
            # Windows: 使用 mklink /j 创建目录连接
            result = os.system(f'mklink /j "{link_name}" "{link_target}"')
            if result != 0:
                return
        else:
            # Linux/Mac: 使用 symlink
            os.symlink(link_target, link_name, target_is_directory=True)
    except Exception as e:
        print(f"ComfyUI AI Assistant: 创建符号链接失败: {e}")

current_dir = os.path.dirname(os.path.abspath(__file__))
extensions_dir = os.path.join(os.getcwd(), "web", "extensions")
os.makedirs(extensions_dir, exist_ok=True)
link_target = os.path.join(current_dir, "web")
link_name = os.path.join(extensions_dir, "comfy_ai_assistant")
mklink_web_extensions(link_name,link_target)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {} 
WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]