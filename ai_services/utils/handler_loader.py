# ai_services/utils/handler_loader.py
import importlib.util
import sys
from pathlib import Path
import os
from typing import Callable, Any, Optional

# 正确获取ai_services目录
ai_services_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 然后获取handlers目录
handlers_dir = ai_services_dir / "handlers"
handlers_dir.mkdir(exist_ok=True)  # 确保目录存在

def load_handler_function(module_path: str, function_name: str) -> Optional[Callable]:
    """
    动态加载指定模块中的处理函数，每次调用都重新加载模块
    
    Args:
        module_path: 模块文件名或相对路径 (相对于handlers目录)
        function_name: 函数名称
        
    Returns:
        加载的函数对象，如果加载失败则返回None
    """
    try:
        # 构建完整的文件路径
        if not module_path.endswith('.py'):
            module_path += '.py'
            
        full_path = handlers_dir / module_path
        
        # 检查文件是否存在
        if not full_path.exists():
            print(f"模块文件不存在: {full_path}")
            return None
        
        # 从文件名获取模块名 (不包含.py扩展名)
        module_name = f"ai_services.handlers.{Path(module_path).stem}"
        
        # 如果模块已在sys.modules中，先移除它
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # 每次都重新加载模块
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec is None:
            print(f"无法找到模块: {full_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 获取函数
        if hasattr(module, function_name):
            return getattr(module, function_name)
        else:
            print(f"函数 {function_name} 在模块 {full_path} 中不存在")
            return None
            
    except Exception as e:
        print(f"加载处理函数时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_ai_response(prompt_config: dict, ai_response: str, **kwargs) -> Any:
    """
    根据提示词配置处理AI响应
    
    Args:
        prompt_config: 提示词配置字典
        ai_response: AI返回的响应文本
        **kwargs: 传递给处理函数的额外参数
        
    Returns:
        处理函数的返回值，如果没有处理函数则返回原始响应
    """
    # 检查是否有处理函数配置
    if "prompt_fun_path" in prompt_config and "prompt_fun" in prompt_config:
        handler = load_handler_function(
            prompt_config["prompt_fun_path"], 
            prompt_config["prompt_fun"]
        )
        
        if handler:
            try:
                return handler(ai_response, **kwargs)
            except Exception as e:
                print(f"执行处理函数时出错: {e}")
                import traceback
                traceback.print_exc()
                return ai_response
    
    # 如果没有处理函数或处理失败，返回原始响应
    return ai_response