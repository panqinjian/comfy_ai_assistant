"""
服务基类定义
"""

import base64
import os
from urllib.parse import urlparse
from abc import ABC, abstractmethod

import aiohttp

class BaseService(ABC):
    """服务基类"""
    
    def __init__(self):
        """初始化默认参数"""
        self.temperature = 1
        self.max_tokens = 2000
        self.timeout = 300
        self.model = ""
        self.proxy = ""
        self.api_key = ""
        self.api_base = ""
        self.api_type = ""
        self.api_version = ""
    
    
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
        """设置API密钥"""
        self.api_key = api_key
        
    def set_api_base(self, api_base):
        """设置API基础URL"""
        self.api_base = api_base
        
    def set_api_type(self, api_type):
        """设置API类型"""
        self.api_type = api_type
        
    def set_api_version(self, api_version):
        """设置API版本"""
        self.api_version = api_version
    
    @abstractmethod
    async def send_message(self, message, stream=False, images=None, host_url=None, history=None, prompt=None):
        """
        发送消息的抽象方法
        
        Args:
            message: 消息内容
            stream: 是否使用流式响应
            images: 图片列表
            host_url: 主机URL（用于处理相对路径的图片）
            history: 对话历史记录，用于保持上下文
            prompt: 系统提示词
            
        Returns:
            AI 回复
        """
        raise NotImplementedError("子类必须实现send_message方法")
    
    async def get_models(self):
        """
        获取模型列表
        
        Returns:
            list: 模型列表，每个模型是一个字典，包含id、name和description
        """
        raise NotImplementedError
    
    
    @classmethod
    def get_service_info(cls):
        """
        获取服务信息
        
        Returns:
            dict: 服务信息，包含id、name和description
        """
        raise NotImplementedError

    @classmethod
    def get_unsupported_features(cls):
        """
        获取服务不支持的功能列表
        
        Returns:
            list: 不支持的功能列表，可能的值包括：
                - 'api_key': 不支持API密钥
                - 'api_base': 不支持自定义API基础URL
                - 'api_type': 不支持API类型设置
                - 'api_version': 不支持API版本设置
                - 'stream': 不支持流式输出
                - 'system_prompt': 不支持系统提示词
                - 'temperature': 不支持温度设置
                - 'max_tokens': 不支持最大令牌数设置
                - 'timeout': 不支持超时设置
                - 'proxy': 不支持代理设置
        """
        return []  # 默认支持所有功能

    async def stream_chat(self, history=None, system_prompt=None):
        """
        流式对话

        Args:
            history: 历史消息列表，每条消息是一个字典，包含role和content字段
            system_prompt: 系统提示词，如果提供则会覆盖当前的system_prompt

        Returns:
            流式生成器，用于返回分块的回复内容

        Raises:
            NotImplementedError: 子类必须实现此方法
            Exception: 聊天历史记录为空或未找到用户消息时抛出
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
        
        # 设置系统提示词
        if system_prompt:
            self.set_system_prompt(system_prompt)
        
        # 调用流式发送消息
        return await self.send_message(user_message, stream=True) 
    
    async def _process_image(self, image_path, host_url=None):
        """
        处理图片，将本地路径转换为 base64 或处理远程 URL

        Args:
            image_path: 图片路径或 URL
            host_url: 主机 URL（用于处理相对路径）

        Returns:
            处理后的图片数据（base64 或 URL）
        """
        try:
            # 检查是否是完整的外部 URL
            parsed = urlparse(image_path)
            if parsed.scheme in ('http', 'https') and not host_url:
                return image_path

            # 处理 ComfyUI API 或本地图片
            async with aiohttp.ClientSession() as session:
                if image_path.startswith('/api/view') and host_url:
                    # 处理 ComfyUI API 格式的 URL
                    base_path = image_path.split('&amp;rand=')[0]  # 移除随机参数

                    # 将 URL 对象转换为字符串
                    host_url_str = str(host_url)
                    if host_url_str.endswith('/'):
                        host_url_str = host_url_str[:-1]

                    full_url = f"{host_url_str}{base_path}"

                    # 获取图片内容
                    async with session.get(full_url) as response:
                        if response.status != 200:
                            raise Exception(f"获取图片失败: HTTP {response.status}")
                        image_data = await response.read()

                        # 转换为 base64
                        encoded_string = base64.b64encode(image_data).decode('utf-8')
                        return f"data:image/jpeg;base64,{encoded_string}"

                elif os.path.isfile(image_path):
                    # 处理本地文件
                    with open(image_path, 'rb') as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        return f"data:image/jpeg;base64,{encoded_string}"
                else:
                    raise Exception(f"无效的图片路径: {image_path}")

        except Exception as e:
            raise Exception(f"处理图片失败: {str(e)}")