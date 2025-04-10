"""
G4F 服务实现
"""

from .base import BaseService
import g4f
import os
import json
from pathlib import Path
from ..config_api import load_config

class G4FService(BaseService):
    """G4F服务类"""
    
    def __init__(self):
        """初始化默认参数"""
        super().__init__()  # 先调用基类初始化
        # 其他参数使用基类默认值:
        # self.temperature = 1
        # self.max_tokens = 2000
        # self.timeout = 300
        # self.proxy = ""
        # self.api_key = ""  # G4F 不需要
        # self.api_base = ""  # G4F 不支持
        # self.api_type = ""  # G4F 不支持
        # self.api_version = ""  # G4F 不支持
        
        # 设置模型缓存文件路径
        self.models_cache_file = Path(os.path.dirname(os.path.abspath(__file__))) / "models_cache" / "g4f_models.json"
        self.models_cache_file.parent.mkdir(exist_ok=True)
        
    def set_temperature(self, temperature):
        """设置温度"""
        self.temperature = float(temperature)
    
    def set_max_tokens(self, max_tokens):
        """设置最大令牌数"""
        self.max_tokens = int(max_tokens)
    
    def set_timeout(self, timeout):
        """设置超时时间"""
        self.timeout = int(timeout)
    
    def set_model(self, model):
        """设置模型"""
        self.model = model
    
    def set_proxy(self, proxy):
        """设置代理"""
        self.proxy = proxy
    
    def set_api_key(self, api_key):
        """设置API密钥 - G4F不需要"""
        pass
    
    def set_api_base(self, api_base):
        """设置API基础URL - G4F不支持"""
        pass
    
    def set_api_type(self, api_type):
        """设置API类型 - G4F不支持"""
        pass
    
    def set_api_version(self, api_version):
        """设置API版本 - G4F不支持"""
        pass
    
    @classmethod
    def get_service_info(cls):
        """获取服务信息"""
        return {
            "id": "g4f",
            "name": "G4F",
            "description": "免费的GPT服务"
        }
        
    @classmethod
    def get_unsupported_features(cls):
        """获取不支持的功能列表"""
        return [
            'api_key',      # G4F 不需要 API 密钥
            'api_base',     # 不支持自定义 API 基础 URL
            'api_type',     # 不支持 API 类型设置
            'api_version'   # 不支持 API 版本设置
        ]
        

    async def get_models(self):
        """获取 G4F 支持的模型列表"""
        # 定义缓存文件路径
        cache_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "models_cache"
        cache_file = cache_dir / "g4f_models.json"
        cache_dir.mkdir(exist_ok=True)
        
        # 1. 首先尝试从网络获取最新模型列表
        try:
            # 获取G4F支持的所有模型
            all_models = [name for name in dir(g4f.models) 
                        if not name.startswith('_') and isinstance(getattr(g4f.models, name), g4f.models.Model)
                        or (isinstance(getattr(g4f.models, name, None), str) and '_' in name and name.islower())]
            
            if all_models:
                # 格式化模型列表
                models = []
                for model_id in sorted(all_models):
                    display_name = model_id.replace('_', '-').upper()
                    models.append({
                        "id": model_id,
                        "name": display_name,
                        "model_path": f"g4f.models.{model_id}"
                    })
                
                #print(f"成功从网络获取到 {len(models)} 个G4F模型")
                
                # 更新缓存
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(models, f, ensure_ascii=False, indent=2)
                    #print("已更新模型缓存")
                except Exception as e:
                    print(f"更新模型缓存失败: {str(e)}")
                
                return models
        except Exception as e:
            print(f"从网络获取模型列表失败: {str(e)}")
        
        # 2. 如果网络获取失败，尝试从缓存读取
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_models = json.load(f)
                    #print(f"使用缓存中的 {len(cached_models)} 个G4F模型")
                    return cached_models
            except Exception as e:
                print(f"读取缓存失败: {str(e)}")
        
        # 3. 如果缓存也失败了，使用静态备份列表
        #print("使用静态备份模型列表")
        backup_models = [
            {"id": "gpt_35_turbo", "name": "GPT-3.5-Turbo", "model_path": "g4f.models.gpt_35_turbo"},
            {"id": "gpt_4", "name": "GPT-4", "model_path": "g4f.models.gpt_4"},
            {"id": "claude_3_opus", "name": "Claude-3-Opus", "model_path": "g4f.models.claude_3_opus"},
            {"id": "claude_3_sonnet", "name": "Claude-3-Sonnet", "model_path": "g4f.models.claude_3_sonnet"},
            {"id": "gemini_pro", "name": "Gemini Pro", "model_path": "g4f.models.gemini_pro"}
        ]
        
        # 尝试将备份列表写入缓存
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(backup_models, f, ensure_ascii=False, indent=2)
            #print("已将备份模型列表写入缓存")
        except Exception as e:
            print(f"写入备份模型列表到缓存失败: {str(e)}")
        
        return backup_models
        
        
    async def send_message(self, message, stream=False, images=None, host_url=None, history=None, prompt=None):
        """发送消息到 G4F"""
        try:           
            # 从配置文件加载参数
            config = load_config("g4f")
            
            # 更新服务参数
            if config:
                self.set_temperature(config.get('temperature', self.temperature))
                self.set_max_tokens(config.get('max_tokens', self.max_tokens))
                self.set_timeout(config.get('timeout', self.timeout))
                self.set_model(config.get('model', self.model))
                self.set_proxy(config.get('proxy', self.proxy))
            
            # 设置代理
            if self.proxy:
                os.environ["http_proxy"] = self.proxy
                os.environ["https_proxy"] = self.proxy
            
            # 构建消息
            messages = []
            if prompt:
                messages.append({"role": "system", "content": prompt})
            
            # 处理历史记录
            # history 格式: {'records': [{message_id, type, user: {content, images}, assistant: {content, images}}], 'has_more', 'next_id'}
            if isinstance(history, dict) and 'records' in history:
                # 按 message_id 排序，确保消息顺序正确
                sorted_records = sorted(history['records'], key=lambda x: x['message_id'])
                
                for record in sorted_records:
                    if record['type'] == 'message':
                        # 添加用户消息
                        if 'user' in record and 'content' in record['user']:
                            messages.append({
                                "role": "user",
                                "content": record['user']['content']
                            })
                        
                        # 添加助手回复
                        if 'assistant' in record and 'content' in record['assistant']:
                            messages.append({
                                "role": "assistant",
                                "content": record['assistant']['content']
                            })

            # 处理当前消息和图片
            if images and len(images) > 0:
                # 构建多模态消息
                current_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message}
                    ]
                }
                
                # 添加图片
                for image in images:
                    image_url = await self._process_image(image, host_url)
                    current_message["content"].append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
            else:
                # 纯文本消息
                current_message = {"role": "user", "content": message}
                
            messages.append(current_message)
            
            # 映射模型名称
            g4f_model = self._map_model_name(self.model)

            # 准备请求数据
            
            parameters={
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "enable_search": True,
                    "search_options": {
                         "num_results": 5,
                         "domain_whitelist": ["*.gov", "*.edu"],
                         "time_range": "2020-01-01.."
                         }
                }
            
            
            # 发送请求
            response = await g4f.ChatCompletion.create_async(
                model=g4f_model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
                parameters=parameters
            )

            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"G4F 服务错误: {str(e)}")        
    def _map_model_name(self, model_name):
        """
        将模型名称映射到 G4F 支持的模型
        
        Args:
            model_name: 用户选择的模型名称
            
        Returns:
            G4F 支持的模型对象
        """
        try:
            # 读取缓存的模型列表
            cache_file = Path(os.path.dirname(os.path.abspath(__file__))) / "models_cache" / "g4f_models.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                    # 查找匹配的模型
                    for model in models:
                        if model["id"] == model_name or model["name"] == model_name:
                            # 从model_path获取实际的模型对象
                            model_parts = model["model_path"].split('.')
                            model_obj = g4f
                            for part in model_parts[1:]:  # 跳过 'g4f'
                                model_obj = getattr(model_obj, part)
                            return model_obj
            
            # 如果没有找到匹配的模型，返回默认模型
            print(f"未找到匹配的模型 '{model_name}'，使用默认模型 gpt-3.5-turbo")
            return g4f.models.gpt_35_turbo
            
        except Exception as e:
            print(f"模型映射失败: {str(e)}，使用默认模型 gpt-3.5-turbo")
            return g4f.models.gpt_35_turbo
