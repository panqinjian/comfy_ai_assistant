"""
提示词管理 API
负责系统提示词的读取、保存和管理
"""

from aiohttp import web
import json
import os
from pathlib import Path
from typing import  Dict, Any
import traceback
import base64


# 默认提示词
DEFAULT_PROMPTS = {
    "prompts": [
        {
            "prompt_id": "comfyui_workflow",
            "prompt_name": "生成一份新的comfyui工作流",
            "prompt_content_path": "comfyui_workflow.ini",
        }
    ]
}

# 提示词文件路径
PROMPTS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "prompts"
PROMPTS_FILE = PROMPTS_DIR / "prompts.json"

def register_prompt_api(app):
    """注册提示词相关的 API 路由"""
    try:
        app.router.add_get("/comfy_ai_assistant/get_prompts", get_prompts)
        app.router.add_get("/comfy_ai_assistant/get_prompt", get_prompt)
        app.router.add_post("/comfy_ai_assistant/set_prompt", set_prompt)
        app.router.add_post("/comfy_ai_assistant/delete_prompt", delete_prompt)
        print("ComfyUI AI Assistant: 提示词 API 已注册")
    except Exception as e:
        print(f"ComfyUI AI Assistant: 注册提示词 API 失败: {e}")

async def get_prompts(request):  # 获取所有提示词
    """获取所有提示词"""
    try:
        # 确保提示词目录存在
        PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
        
        # 加载所有提示词
        prompts_data = load_prompts()
        
        return web.json_response({
            'success': True,
            'prompts': prompts_data  # 返回整个提示词数据，而不是只返回 prompts 列表
        })
    
    except Exception as e:
        traceback.print_exc()
        return web.json_response({'success': False,'error': str(e)}, status=500)

async def get_prompt(request):   # 获取指定id提示词，只返回提示词，不返回其他结构
    """获取当前或指定的提示词"""
    try:
        # 确保提示词目录存在
        PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
        
        # 从请求中获取 prompt_id 参数
        prompt_id = request.query.get('prompt_id', None)
        
        # 如果没有指定 ID，返回错误
        if not prompt_id:
            return web.json_response({'success': False,'error': '没有指定prompt_id'}, status=400)
        
        # 获取提示词内容
        content = load_prompt(prompt_id)
        
        # 如果找不到提示词内容，返回错误
        if not content:
            return web.json_response({'success': False,'error': "找不到指定的提示词内容"}, status=404)
        
        # 对提示词内容进行base64编码
        content_bytes = content.encode('utf-8')
        content_base64 = base64.b64encode(content_bytes).decode('utf-8')
        
        return web.json_response({
            'success': True,
            'content': content_base64
        })
    
    except Exception as e:
        traceback.print_exc()
        return web.json_response({'success': False,'error': str(e)}, status=500)
    
def load_prompts() -> Dict[str, Any]:  # 加载提示词数据
    """加载提示词数据"""
    # 确保提示词目录存在
    PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
    
    # 检查文件是否存在
    if not PROMPTS_FILE.exists():
        # 保存默认配置到文件
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROMPTS, f, ensure_ascii=False, indent=4)
        return DEFAULT_PROMPTS
    
    # 读取并解析提示词文件
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            prompts_data = json.load(f)
            # 验证数据结构
            if not isinstance(prompts_data, dict) or "prompts" not in prompts_data:
                return DEFAULT_PROMPTS
            return prompts_data
        
    except json.JSONDecodeError:
        return DEFAULT_PROMPTS
    except Exception as e:
        print(f"加载提示词数据失败: {str(e)}")
        return DEFAULT_PROMPTS

def load_prompt(prompt_id: str) -> str:  # 加载指定id的提示词内容
    """
    加载提示词内容
    
    Args:
        prompt_id: 提示词ID
        
    Returns:
        str: 提示词内容
    """
    try:
        # 获取提示词配置
        prompts_data = load_prompts()
        
        # 查找提示词配置
        prompt_config = None
        for p in prompts_data["prompts"]:
            if p["prompt_id"] == prompt_id:
                prompt_config = p
                break
                
        if not prompt_config:
            return ""
            
        # 读取提示词内容文件
        content_path = prompt_config.get("prompt_content_path")
        if not content_path:
            return ""
            
        content_file = PROMPTS_DIR / content_path
        if not content_file.exists():
            return ""
            
        # 读取内容
        with open(content_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        return content
        
    except Exception as e:
        print(f"加载提示词内容失败: {str(e)}")
        return ""

def save_prompts(prompts_data: Dict[str, Any]) -> bool:  # 保存提示词数据
    """保存提示词数据"""
    try:
        # 确保提示词目录存在
        PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
        
        # 写入提示词文件
        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, ensure_ascii=False, indent=4)
                
            return True
    except Exception as e:
        print(f"保存提示词失败: {str(e)}")
        return False

def save_prompt(prompt_id: str, prompt_name: str, prompt_content_path: str, prompt_content: str) -> bool:
    """
    保存提示词数据
    
    Args:
        prompt_id: 提示词ID
        prompt_name: 提示词名称
        prompt_content_path: 提示词内容文件路径
        prompt_content: 提示词内容
        
    Returns:
        bool: 是否保存成功
    """
    # 确保提示词目录存在
    prompts_data = load_prompts()
    
    # 构建提示词数据
    prompt_data = {
        "prompt_id": prompt_id,
        "prompt_name": prompt_name,
        "prompt_content_path": prompt_content_path
    }

    # 更新或添加提示词
    found = False
    for p in prompts_data["prompts"]:
        if p["prompt_id"] == prompt_id:
            p.update(prompt_data)
            found = True
            break
            
    if not found:
        prompts_data["prompts"].append(prompt_data)
    
    # 保存提示词内容到文件
    try:
        content_file = PROMPTS_DIR / prompt_content_path
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)
    except Exception as e:
        print(f"保存提示词内容失败: {str(e)}")
        return False
    
    return save_prompts(prompts_data)

async def set_prompt(request):
    """保存或更新提示词"""
    try:
        # 获取请求数据
        data = await request.json()
        prompt_id = data.get('prompt_id', None)
        prompt_name = data.get('prompt_name', None)
        prompt_content_path = data.get('prompt_content_path', None)
        prompt_content_base64 = data.get('prompt_content', None)  # 获取base64编码的内容
        
        # 验证数据
        if not prompt_id or not prompt_name or not prompt_content_path or not prompt_content_base64:
            return web.json_response({'success': False,'error': "缺少必要的参数"}, status=400)
            
        try:
            # 解码base64内容
            prompt_content = base64.b64decode(prompt_content_base64).decode('utf-8')
        except Exception as e:
            return web.json_response({'success': False,'error': "提示词内容解码失败"}, status=400)
        
        # 保存提示词
        if not save_prompt(prompt_id, prompt_name, prompt_content_path, prompt_content):
            return web.json_response({'success': False,'error': "保存提示词失败"}, status=500)
        
        return web.json_response({
            'success': True,
            'message': "提示词保存成功"
        })
    
    except Exception as e:
        traceback.print_exc()
        return web.json_response({'success': False,'error': str(e)}, status=500)

async def delete_prompt(request): # prompt_id 为all时，删除所有提示词
    """删除提示词"""
    try:
        # 获取请求数据
        data = await request.json()
        prompt_id = data.get('prompt_id', None)
        
        # 验证提示词 ID
        if not prompt_id:
            return web.json_response({'success': False,'error': "未提供提示词 ID"}, status=400)
            
        # 如果是删除所有提示词
        if prompt_id == 'all':
            try:
                # 删除整个提示词目录并重建
                if PROMPTS_DIR.exists():
                    import shutil
                    shutil.rmtree(PROMPTS_DIR)
                PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
                
                # 重新创建默认提示词配置
                save_prompt(DEFAULT_PROMPTS.get("prompt_id"), DEFAULT_PROMPTS.get("prompt_name"), 
                            DEFAULT_PROMPTS.get("prompt_content_path"), "你是一个comfyui专家，请帮用户处理工作流新建问题")
                
                return web.json_response({
                    'success': True,
                    'message': "所有提示词已删除并重置"
                })
            except Exception as e:
                return web.json_response({'success': False,'error': f"删除所有提示词失败: {str(e)}"}, status=500)
        
        # 删除指定提示词
        prompts_data = load_prompts()
        found = False
        
        for i, p in enumerate(prompts_data["prompts"]):
            if p["prompt_id"] == prompt_id:
                
                # 删除提示词内容文件
                content_path = p.get("prompt_content_path")
                if content_path:
                    content_file = PROMPTS_DIR / content_path
                    if content_file.exists():
                        content_file.unlink()
                
                # 从配置中删除提示词
                prompts_data["prompts"].pop(i)
                found = True
                break
        
        # 如果找不到提示词，返回错误
        if not found:
            return web.json_response({'success': False,'error': "找不到指定的提示词"}, status=404)
        
        # 保存更新后的配置
        if not save_prompts(prompts_data):
            return web.json_response({'success': False,'error': "保存提示词配置失败"}, status=500)
        
        return web.json_response({
            'success': True,
            'message': "提示词删除成功"
        })
    
    except Exception as e:
        traceback.print_exc()
        return web.json_response({'success': False,'error': str(e)}, status=500)

def load_prompt_data(prompt_id: str) -> dict:  # 加载指定id的提示词内容
    """
    加载提示词内容
    
    Args:
        prompt_id: 提示词ID
        
    Returns:
        dict: 提示词配置字典，如果未找到则返回空字典
    """
    try:
        # 获取提示词配置
        prompts_data = load_prompts()
        
        # 查找提示词配置
        for prompt in prompts_data["prompts"]:
            if prompt["prompt_id"] == prompt_id:
                # 如果找到匹配的提示词ID，直接返回该提示词配置
                return prompt
                
        # 如果未找到匹配的提示词ID，返回空字典
        return {}
        
    except Exception as e:
        print(f"加载提示词数据失败: {str(e)}")
        return {}