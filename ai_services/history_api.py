"""
历史记录相关的 API 端点
"""
from aiohttp import web
import json
import os
from pathlib import Path
from typing import List, Dict

# 历史记录路径
HISTORY_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "history"

# 默认历史记录
DEFAULT_HISTORY: List[Dict[str, str]] = []

def register_history_api(app):
    """注册历史记录相关的 API 路由"""
    try:
        # 注册路由
        app.router.add_get("/comfy_ai_assistant/history", get_history)
        app.router.add_post("/comfy_ai_assistant/clear_history", clear_history)
        app.router.add_get('/comfy_ai_assistant/sessions', get_sessions)
        app.router.add_post('/comfy_ai_assistant/save_history', set_history)
        print("ComfyUI AI Assistant: 历史记录 API 路由已注册")
    except Exception as e:
        print(f"ComfyUI AI Assistant: 注册历史记录 API 路由失败: {e}")

async def get_history(request):
    """获取历史记录"""
    try:
        # 确保历史记录目录存在
        HISTORY_DIR.mkdir(exist_ok=True, parents=True)

        service = request.query.get('service', 'g4f')
        history = load_history_local(service)
        
        return web.json_response({
            'success': True,
            'history': history
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)
    
async def set_history(request):
    """保存历史记录"""
    # 如果没有指定服务，使用配置中的默认服务
    data = await request.json()
    service = data.get("service", None)
    if service is None:
        config = config.load_config()
        service = config.get("service", "g4f")

    # 确保服务目录存在
    return save_history_local(data.get("history"), service)

async def clear_history(request):
    """清除聊天历史"""
    try:
        data = await request.json()
        service = data.get("service", "g4f")
        
        # 保存空历史记录
        save_history_local([], service)
        
        return web.json_response({
            "success": True,
            "message": f"已清除历史记录"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def get_sessions(request):
    """获取会话列表"""
    try:
        # 确保历史记录目录存在
        HISTORY_DIR.mkdir(exist_ok=True, parents=True)
        
        service = request.query.get('service', 'g4f')
        
        return web.json_response({
            'success': True,
            'sessions': ['default']  # 只返回默认会话
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

def load_history_local(service: str) -> List[Dict[str, str]]:
    """加载历史记录

    Args:
        service: 服务名称

    Returns:
        历史记录列表
    """
    history_file = HISTORY_DIR / f"{service}.json"
    
    if not history_file.exists():
        return DEFAULT_HISTORY
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"历史记录文件格式错误: {history_file}", e.doc, e.pos)

def save_history_local(history: List[Dict[str, str]], service: str = "g4f") -> bool:
    """保存历史记录

    Args:
        history: 历史记录列表
        service: 服务名称

    Returns:
        是否保存成功
    """
    try:
        history_file = HISTORY_DIR / f"{service}.json"
        
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"保存历史记录失败: {str(e)}")
        return False