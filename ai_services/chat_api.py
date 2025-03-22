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
        
        # 从请求中获取历史记录
        history = data.get('history', [])
        
        # 获取图片列表
        images = data.get('images', [])
        
        # 获取host_url，处理相对路径的图片
        host_url = request.url.origin()
        
        # 发送消息并获取响应，传递历史记录
        response = await service.send_message(
            message=data.get('message', ''),
            images=images, 
            host_url=host_url,
            history=history
        )
        
        return web.json_response({"success": True, "response": response})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": str(e)})

async def stream_chat(request):
    """流式聊天API"""
    try:
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
        
        try:
            # 获取请求数据
            data = await request.json()
            
            # 获取服务实例
            service_id = data.get('service', 'g4f')
            service_class = get_service(service_id)
            if not service_class:
                await response.write(f'data: {json.dumps({"error": "服务不存在"})}\n\n'.encode('utf-8'))
                await response.write(b'data: [DONE]\n\n')
                return response
                
            # 创建服务实例
            service = service_class()
            
            # 设置参数
            for param in ['system_prompt', 'temperature', 'max_tokens', 'timeout', 'model', 'proxy', 'api_key']:
                if param in data:
                    getattr(service, f'set_{param}')(data[param])
            
            # 从请求中获取历史记录
            history = data.get('history', [])
            
            # 获取图片列表
            images = data.get('images', [])
            
            # 获取host_url，处理相对路径的图片
            host_url = request.url.origin()
            
            try:
                # 发送消息并获取流式响应
                service_response = await service.send_message(
                    message=data.get('message', ''),
                    stream=True,
                    images=images,
                    host_url=host_url,
                    history=history
                )
                
                if isinstance(service_response, bool):
                    # 如果返回布尔值，说明出错了
                    await response.write(f'data: {json.dumps({"error": "服务返回无效响应"})}\n\n'.encode('utf-8'))
                    await response.write(b'data: [DONE]\n\n')
                    return response
                
                if hasattr(service_response, 'content'):
                    # 处理流式响应
                    async for chunk in service_response.content:
                        if chunk:
                            await response.write(f'data: {json.dumps({"content": chunk.decode("utf-8")})}\n\n'.encode('utf-8'))
                elif isinstance(service_response, str):
                    # 处理字符串响应
                    await response.write(f'data: {json.dumps({"content": service_response})}\n\n'.encode('utf-8'))
                else:
                    # 处理其他类型的响应
                    await response.write(f'data: {json.dumps({"content": str(service_response)})}\n\n'.encode('utf-8'))
                
                await response.write(b'data: [DONE]\n\n')
                return response
                
            except Exception as e:
                # 处理服务调用过程中的错误
                error_message = f'data: {json.dumps({"error": f"服务调用错误: {str(e)}"})}\n\n'
                await response.write(error_message.encode('utf-8'))
                await response.write(b'data: [DONE]\n\n')
                return response
            
        except Exception as e:
            # 处理请求数据解析过程中的错误
            error_message = f'data: {json.dumps({"error": f"请求处理错误: {str(e)}"})}\n\n'
            await response.write(error_message.encode('utf-8'))
            await response.write(b'data: [DONE]\n\n')
            return response
            
    except Exception as e:
        # 处理响应设置过程中的错误
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": f"响应设置错误: {str(e)}"}) 