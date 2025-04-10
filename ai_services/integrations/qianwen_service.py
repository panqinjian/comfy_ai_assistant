"""千问服务实现"""
import json
import aiohttp
from urllib.parse import urlparse
from .base import BaseService
from ..config_api import load_config

class QianwenService(BaseService):
    """千问服务类"""

    def __init__(self):
        """初始化默认参数"""
        super().__init__()  # 先调用基类初始化
        # 覆盖特定参数
        self.api_endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.api_endpoint_image = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
        self.vision_api_endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        # 模型名称映射
        self.model_mapping_text  = {
            "通义千问 Max": "qwen-max",
            "通义千问 Plus": "qwen-plus",
            "通义千问 Turbo": "qwen-turbo",
            "通义千问 Long": "qwen-long",
        }
        self.model_mapping_vision = {
            "通义千问 VL Plus": "qwen-vl-plus",
            "通义千问 VL Max": "qwen-vl-max",
            "通义千问 VL Max Latest": "qwen-vl-max-latest",
            "通义千问 VL OCR": "qwen-vl-ocr"
        }
        # 其他参数使用基类默认值:
        self.temperature = 1
        self.max_tokens = 2000
        self.timeout = 300
        self.proxy = ""
        self.api_key = ""  # 需要设置有效的API密钥
        self.session_token = None  # 会话令牌

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
            'api_base',  # 不支持自定义 API 基础 URL
            'api_type',  # 不支持 API 类型设置
            'api_version'  # 不支持 API 版本设置
        ]


    async def send_image(self, message,stream=False, images=None, host_url=None, history=None, prompt=None):
        """
        发送图片请求到通义千问视觉模型

        Args:
            image_url: 图片URL或Base64编码
            prompt: 提示文本
            task: 任务类型 (如 "ocr", "image_captioning")
            stream: 是否使用流式输出（视觉模型可能不支持）

        Returns:
            模型的文本响应
        """
        try:
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

            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            if self.model not in self.model_mapping_vision:
                self.model = self.model_mapping_vision["通义千问 VL Plus"]

            messages = []

            if prompt:
                messages.append({"role": "system", "content": prompt})

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
            
            
            # 初始化计数器
            i = 0  # 必须添加的初始化
            image_content = []  # PEP8空格规范

            # 处理图片URL
            for image in images:
                image_url = await self._process_image(image, host_url)
                i += 1  # 更规范的写法
                if i <= 5:  # 限制最多5张图（i=1到5）
                    image_content.append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
                else:
                    break  # 超过5张时停止处理
            if prompt:
                content_list.append({"type": "text", "text": prompt})
            # 构建消息内容（展开列表）
            content_list = [{"type": "text", "text": message}]  # 文本部分

                
            content_list.extend(image_content)  # 关键修正：展开图片内容

            messages.append({
                                    "role": "user",
                                    "content": content_list
                                })

            data = {
                "model": self.model,
                "messages": messages,
                 "parameters": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "enable_search": True
                }
            }


            # 设置超时
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.vision_api_endpoint,
                    headers=headers,
                    json=data,
                    proxy=self.proxy if self.proxy else None,
                    timeout=timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"视觉API错误 ({response.status}): {error_text}")

                    result = await response.json()
                    
                    # 解析返回数据
                    if "choices" in result and len(result["choices"]) > 0:
                        message = result["choices"][0].get("message", {})
                        if "content" in message:
                            return message["content"]
                        elif "output" in result and "text" in result["output"]:
                            return result["output"]["text"]
                        else:
                            raise Exception("API返回数据缺少content字段")
                    else:
                        raise Exception(f"视觉API返回格式错误: {json.dumps(result)}")

        except aiohttp.ClientError as e:
            raise Exception(f"视觉请求失败: {str(e)}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"视觉服务错误: {str(e)}")
    
    
    async def send_message(self, message, stream=False, images=None, host_url=None, history=None, prompt=None):
        """发送消息"""
        try:
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

            # 如果有图片，使用视觉API
            if images and len(images) > 0:

                # 调用视觉API
                return await self.send_image(message=message,stream=stream,images=images, host_url=host_url, history=history,prompt=prompt)

            # 构建消息数组，包含历史记录
            messages = []

            if prompt:
                messages.append({"role": "system", "content": prompt})

            # 如果提供了历史记录，将其添加到消息列表中
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

            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message
            })

            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if self.model not in self.model_mapping_text:
                self.model = self.model_mapping_text["通义千问 Max"]



            # 准备请求数据
            data = {
                "model": self.model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "enable_search": True
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
        except Exception as e:
                import traceback
                traceback.print_exc()
                raise Exception(f"千问服务错误: {str(e)}")

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
        # 检查是否在文本模型映射中
        if model in self.model_mapping_text:
            self.model = self.model_mapping_text[model]
        # 检查是否在视觉模型映射中
        elif model in self.model_mapping_vision:
            self.model = self.model_mapping_vision[model]
        else:
            # 如果找不到映射，使用原始值
            self.model = model

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
        """获取通义千问支持的模型列表 模型数组应该符合(id, name, description,)"""
        return [
            {"id": "qwen-max", "name": "通义千问 Max", "description": "最强大的文本模型"},
            {"id": "qwen-plus", "name": "通义千问 Plus", "description": "平衡性能和速度"},
            {"id": "qwen-turbo", "name": "通义千问 Turbo", "description": "最快的文本模型"},
            {"id": "qwen-long", "name": "通义千问 Long", "description": "支持长文本的模型"},
            {"id": "qwen-vl-plus", "name": "通义千问 VL Plus", "description": "支持视觉的平衡模型"},
            {"id": "qwen-vl-max", "name": "通义千问 VL Max", "description": "支持视觉的最强大模型"},
            {"id": "qwen-vl-max-latest", "name": "通义千问 VL Max Latest", "description": "最新的视觉模型"},
            {"id": "qwen-vl-ocr", "name": "通义千问 VL OCR", "description": "支持文字提取的视觉模型"}
        ]