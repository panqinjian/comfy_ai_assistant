"""
服务注册和路由设置
"""
from typing import Dict, Type
from aiohttp import web

# 服务注册表
_services: Dict[str, Type['BaseService']] = {}

def register_service(service_class: Type['BaseService']) -> None:
    """注册服务"""
    service_info = service_class.get_service_info()
    _services[service_info["id"]] = service_class
    
def get_service(service_id: str) -> Type['BaseService']:
    """获取服务类"""
    return _services.get(service_id)

def get_all_services() -> Dict[str, Type['BaseService']]:
    """获取所有已注册的服务"""
    return _services

# 导入服务基类
from .integrations.base import BaseService

# 导入具体服务实现
from .integrations.g4f_service import G4FService
from .integrations.qianwen_service import QianwenService

# 导入API模块
from . import chat_api
from . import service_api
from . import config_api
from . import history_api
from . import prompt_api
from . import ffmpeg_api


def setup_routes(app: web.Application) -> None:
    """设置所有API路由"""
    try:
        # 注册服务
        register_service(G4FService)
        register_service(QianwenService)
        
        # 注册API路由
        chat_api.register_chat_api(app)
        service_api.register_service_api(app)
        config_api.register_config_api(app)
        history_api.register_history_api(app)
        prompt_api.register_prompt_api(app)
        ffmpeg_api.register_ffmpeg_api(app)
        
        
        print("ComfyUI AI Assistant: API路由注册成功")
    except Exception as e:
        print(f"ComfyUI AI Assistant: API路由注册失败: {str(e)}")
        raise


def setup_api_routes():
    """设置 API 路由"""
    try:
        import server
        if hasattr(server, 'PromptServer'):
            server_instance = server.PromptServer.instance
            if hasattr(server_instance, 'app'):
                setup_routes(server_instance.app)
                print("ComfyUI AI Assistant: API 路由注册成功")
            else:
                print("ComfyUI AI Assistant: 无法获取 PromptServer 的 app 属性")
        else:
            print("ComfyUI AI Assistant: server 模块没有 PromptServer 属性")
    except Exception as e:
        print(f"ComfyUI AI Assistant: 注册 API 路由失败 - {str(e)}")

# 初始化扩展
setup_api_routes()
