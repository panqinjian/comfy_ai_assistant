"""
服务相关的 API 端点
"""
from aiohttp import web
from ai_services import get_service, get_all_services

def register_service_api(app):
    """注册服务相关的API路由"""
    app.router.add_get("/comfy_ai_assistant/models", get_models)
    app.router.add_get("/comfy_ai_assistant/services", get_services)

async def get_models(request):
    """获取模型列表"""
    try:
        # 获取服务ID
        service_id = request.query.get("service", "g4f")  # 默认使用g4f服务
        
        # 获取服务实例
        service_class = get_service(service_id)
        if not service_class:
            return web.json_response({"success": False, "error": "服务不存在"})
            
        # 创建服务实例并获取模型列表
        service = service_class()
        models = await service.get_models()
        
        # 直接返回模型列表
        return web.json_response({"success": True, "models": models})
        
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

async def get_services(request):
    """获取服务列表"""
    try:
        services = []
        for service_id, service_class in get_all_services().items():
            service_info = service_class.get_service_info()
            services.append(service_info)
        
        return web.json_response({
            "success": True,
            "services": services
        })
    except Exception as e:
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)