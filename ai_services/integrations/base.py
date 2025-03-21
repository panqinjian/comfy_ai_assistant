"""
服务基类定义
"""

class BaseService:
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
    
    async def send_message(self, message, **kwargs):
        """
        发送消息
        
        Args:
            message: 消息内容
            **kwargs: 额外参数，如stream=True用于流式输出
            
        Returns:
            消息响应或生成器（流式输出时）
        """
        raise NotImplementedError
    
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