"""
配置相关的 API 端点
"""
from aiohttp import web
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_CONFIG = {
        "service": "g4f",
        "service_list": [
            "G4F(免费)",
            "通义千问"
            ],
        "service_ID_list": [
            "g4f",
            "qianwen"
            ],
        "ai_params": {}
    }

DEFAULT_CONFIG_ai_params = {
            "temperature": 1,
            "max_tokens": 2000,
            "timeout": 300,
            "model": "gpt_4",
            "proxy": "",
            "api_key": "",
            "api_base": "",
            "api_type": "",
            "api_version": ""
            }
# 配置文件路径
SERVICES_CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__)))/ "configs"


def register_config_api(app):

    """注册配置相关的 API 路由"""
    app.router.add_get("/comfy_ai_assistant/config", get_config)
    app.router.add_post("/comfy_ai_assistant/save_config", set_config)
    print("ComfyUI AI Assistant: 配置 API 路由已注册")

async def get_config(request):
    """获取配置"""
    try:
        # 确保配置目录存在
        SERVICES_CONFIG_DIR.mkdir(exist_ok=True, parents=True)
        # 从请求中获取 service 参数
        service = request.query.get('service', None)
        print(f"请求服务配置: {service}")
        
        # 使用 get_merged_config 获取配置
        config = load_config()
        if service==None:
            service = config["service"]
        else:
            config["service"] = service
        
        config_ai_params = load_config(service)
        # 获取服务不支持的功能列表并设置为disabled
        if service:
            from ai_services import get_service
            service_class = get_service(service)
            if service_class:
                # 将不支持的功能设置为disabled
                unsupported_features = service_class.get_unsupported_features()
                for feature in config_ai_params:
                    if feature not in unsupported_features and config_ai_params[feature] == "disabled":
                        config_ai_params[feature] = ""
                    elif feature  in unsupported_features:
                        config_ai_params[feature] = "disabled"
            else:
                print(f"Service {service} not found in registered services")
        
        config["ai_params"] = config_ai_params
        print(f"返回配置: {config}")  # 添加调试输出
        
        return web.json_response({
            'success': True,
            'config': config
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def set_config(request):
    """保存配置"""
    try:
        # 确保配置目录存在
        SERVICES_CONFIG_DIR.mkdir(exist_ok=True, parents=True)
        data = await request.json()
        save_config(data)
        return web.json_response({
            'success': True
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500) 



def load_config(service: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件。

    Args:
        service: 服务名称。如果为 None，加载默认配置文件；否则加载服务相关配置文件。

    Returns:
        配置数据的字典。

    Raises:
        FileNotFoundError: 配置文件不存在。
        json.JSONDecodeError: 配置文件格式错误。
    """

    if service is None:
        config_file = SERVICES_CONFIG_DIR / "config.json"
            # 检查文件是否存在
        if not config_file.exists():
            return DEFAULT_CONFIG
    else:
        config_file = SERVICES_CONFIG_DIR / f"{service}.json"
        if not config_file.exists():
            return DEFAULT_CONFIG_ai_params

    # 读取并解析配置文件
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"配置文件格式错误: {config_file}", e.doc, e.pos)
    

def save_config(config):
    """保存主配置"""
    try:
        service = config["service"]
        config_file = SERVICES_CONFIG_DIR / "config.json"
        config_service_file = SERVICES_CONFIG_DIR / f"{service}.json"
        config_l=DEFAULT_CONFIG
        config_l["service"] = service
        config_l["ai_params"] = config["ai_params"]

        from ai_services import get_service
        service_class = get_service(service)
        if service_class:
            # 将不支持的功能设置为disabled
            unsupported_features = service_class.get_unsupported_features()
            for feature in config_l["ai_params"]:
                if config_l["ai_params"][feature] == "disabled" and feature not in unsupported_features:
                    config_l["ai_params"][feature] = ""

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_l, f, ensure_ascii=False, indent=4)
        with open(config_service_file, 'w', encoding='utf-8') as f:
            json.dump(config_l["ai_params"] , f, ensure_ascii=False, indent=4)
        
        print(f"保存配置成功: {config}")
        return True
    
    except Exception as e:
        print(f"保存配置失败: {str(e)}")
        return False