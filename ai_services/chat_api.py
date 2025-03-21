"""
聊天相关的 API 端点
"""
from aiohttp import web
import json
from . import get_service

def register_chat_api(app):
    """注册聊天相关的API路由"""
    app.router.add_post("/comfy_ai_assistant/chat", chat)
    app.router.add_post("/comfy_ai_assistant/stream_chat", stream_chat)

async def chat(request):
    """聊天API"""
    try:
        # 获取请求数据
        data = await request.json()
        
        # 获取服务实例
        service_id = data.get('service', 'g4f')
        service_class = get_service(service_id)
        if not service_class:
            return web.json_response({"success": False, "error": "服务不存在"})
            
        # 创建服务实例
        service = service_class()
        
        # 设置参数
        for param in ['system_prompt', 'temperature', 'max_tokens', 'timeout', 'model', 'proxy', 'api_key']:
            if param in data:
                getattr(service, f'set_{param}')(data[param])
        
        # 发送消息并获取响应
        response = await service.send_message(data.get('message', ''))
        return web.json_response({"success": True, "response": response})
        
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

async def stream_chat(request):
    """流式聊天API"""
    try:
        # 获取请求数据
        data = await request.json()
        
        # 获取服务实例
        service_id = data.get('service', 'g4f')
        service_class = get_service(service_id)
        if not service_class:
            return web.json_response({"success": False, "error": "服务不存在"})
            
        # 创建服务实例
        service = service_class()
        
        # 设置参数
        for param in ['system_prompt', 'temperature', 'max_tokens', 'timeout', 'model', 'proxy', 'api_key']:
            if param in data:
                getattr(service, f'set_{param}')(data[param])
        
        # 创建流式响应
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
        await response.prepare(request)
        
        # 发送消息并获取流式响应
        async for chunk in service.send_message(data.get('message', ''), stream=True):
            await response.write(f'data: {json.dumps({"content": chunk})}\n\n'.encode('utf-8'))
            
        await response.write(b'data: [DONE]\n\n')
        return response
        
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}) 