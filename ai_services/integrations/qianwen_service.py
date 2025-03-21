"""
千问服务实现
"""
import json
import aiohttp
from .base import BaseService
from ..config_api import load_config

class QianwenService(BaseService):
    """千问服务类"""
    
    def __init__(self):
        """初始化默认参数"""
        super().__init__()  # 先调用基类初始化
        # 覆盖特定参数
        self.api_endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        # 模型名称映射
        self.model_mapping = {
            "通义千问 Max": "qwen-max",
            "通义千问 Plus": "qwen-plus",
            "通义千问 Turbo": "qwen-turbo",
            "通义千问 VL Plus": "qwen-vl-plus",
            "通义千问 VL Max": "qwen-vl-max",
            "通义千问 VL Max Latest": "qwen-vl-max-latest",
            "通义千问 Long": "qwen-long",
            "通义千问 VL OCR": "qwen-vl-ocr"
        }
        # 其他参数使用基类默认值:
        # self.temperature = 1
        # self.max_tokens = 2000
        # self.timeout = 300
        # self.proxy = ""
        # self.api_key = ""  # 需要设置有效的API密钥
        # self.api_base = ""  # 千问不支持
        # self.api_type = ""  # 千问不支持
        # self.api_version = ""  # 千问不支持
        
    @classmethod
    def get_service_info(cls):
        """获取服务信息"""
        return {
            "id": "qianwen",
            "name": "千问",
            "description": "阿里云千问大模型服务"
        }
        
    @classmethod
    def get_unsupported_features(cls):
        """获取不支持的功能列表"""
        return [
            'api_base',     # 不支持自定义 API 基础 URL
            'api_type',     # 不支持 API 类型设置
            'api_version'   # 不支持 API 版本设置
        ]
        
    async def send_message(self, message, stream=False, images=None, host_url=None):
        """发送消息"""
        # 从配置文件加载参数
        config = load_config("qianwen")
        
        # 更新服务参数
        if config:
            self.set_temperature(config.get('temperature', self.temperature))
            self.set_max_tokens(config.get('max_tokens', self.max_tokens))
            self.set_timeout(config.get('timeout', self.timeout))
            self.set_model(config.get('model', self.model))
            self.set_proxy(config.get('proxy', self.proxy))
            self.set_api_key(config.get('api_key', self.api_key))
            
        if not self.api_key:
            raise Exception("请设置API密钥")
            
        # 构建消息
        messages = []
            
        # 处理图片
        if images and len(images) > 0:
            content = []
            # 添加文本
            if message:
                content.append({
                    "text": message
                })
            # 添加图片
            for image in images:
                # 如果是相对路径，添加host_url
                if host_url and not image.startswith(('http://', 'https://')):
                    image = f"{host_url.rstrip('/')}/{image.lstrip('/')}"
                content.append({
                    "image": image
                })
            messages.append({
                "role": "user",
                "content": content
            })
        else:
            # 纯文本消息
            messages.append({
                "role": "user",
                "content": message
            })
            
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 准备请求数据
        data = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
        }
        
        # 设置流式模式
        if stream:
            headers["X-DashScope-SSE"] = "enable"
            
        # 使用 aiohttp 发送请求
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=data,
                    proxy=self.proxy if self.proxy else None,
                    timeout=timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"千问 API 错误 ({response.status}): {error_text}")
                    
                    # 处理流式响应
                    if stream:
                        return response  # 返回响应对象，由调用方处理流
                    else:
                        # 处理常规响应
                        result = await response.json()
                        
                        if "output" in result and "text" in result["output"]:
                            return result["output"]["text"]
                        else:
                            raise Exception(f"千问 API 返回格式错误: {json.dumps(result)}")
        except aiohttp.ClientError as e:
            raise Exception(f"请求失败: {str(e)}")

    async def stream_chat(self, history=None, system_prompt=None):
        """
        流式对话
        
        Args:
            history: 历史消息
            system_prompt: 系统提示词
            
        Returns:
            流式生成器
        """
        if not history or len(history) == 0:
            raise Exception("聊天历史记录不能为空")
        
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(history):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        if user_message is None:
            raise Exception("未找到用户消息")
        
        # 调用流式发送消息
        return await self.send_message(user_message, stream=True)
    
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
        # 使用映射转换模型名称
        self.model = self.model_mapping.get(model, model)  # 如果找不到映射，使用原始值
    
    def set_proxy(self, proxy):
        """设置代理"""
        self.proxy = proxy
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.api_key = api_key
    
    def set_api_base(self, api_base):
        """设置API基础URL - 千问不支持"""
        pass
    
    def set_api_type(self, api_type):
        """设置API类型 - 千问不支持"""
        pass
    
    def set_api_version(self, api_version):
        """设置API版本 - 千问不支持"""
        pass

    async def get_models(self):
        """获取通义千问支持的模型列表  模型数组应该符合(id, name, description,)"""
        return [
            {"id": "qwen-max", "name": "通义千问 Max", "description": "最强大的文本模型"},
            {"id": "qwen-plus", "name": "通义千问 Plus", "description": "平衡性能和速度"},
            {"id": "qwen-turbo", "name": "通义千问 Turbo", "description": "最快的文本模型"},
            {"id": "qwen-vl-plus", "name": "通义千问 VL Plus", "description": "支持视觉的平衡模型"},
            {"id": "qwen-vl-max", "name": "通义千问 VL Max", "description": "支持视觉的最强大模型"},
            {"id": "qwen-vl-max-latest", "name": "通义千问 VL Max Latest", "description": "最新的视觉模型"},
            {"id": "qwen-long", "name": "通义千问 Long", "description": "支持长文本的模型"},
            {"id": "qwen-vl-ocr", "name": "通义千问 VL OCR", "description": "支持文字提取的视觉模型"}
        ] 