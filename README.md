# ComfyUI AI Assistant

今天发现阿里已经有一个同样的项目：https://github.com/AIDC-AI/ComfyUI-Copilot/tree
大公司做的产品肯定效果好，我个人做起来效率不行，效果也达不到要求，以后这个项目将不在更新

ComfyUI AI Assistant 是一个集成于 ComfyUI 的 AI 助手扩展，支持多种 AI 服务，包括本地模型、云端 API 以及免费开源模型服务。助手可以回答问题、协助工作流创建以及处理图像等任务。

## 功能特点

- 🤖 支持多种 AI 服务（G4F、本地模型等）
- 🖼️ 支持图像上传和处理
- 💬 流式响应，实时显示 AI 回复
- 📝 保存和加载聊天历史
- 🔧 可自定义的参数设置
- 🌐 无需外部 API 密钥

## 安装方法

### 方法一：Git Clone（推荐）

```bash
cd custom_nodes
git clone https://github.com/panqinjian/comfy_ai_assistant.git
cd comfy_ai_assistant
pip install -r requirements.txt
```

### 方法二：下载 Zip

1. 下载本仓库的 ZIP 文件
2. 解压到 ComfyUI 的 `custom_nodes` 目录
3. 进入解压后的目录，运行 `pip install -r requirements.txt`

## 依赖项

详见 `requirements.txt` 文件。主要依赖包括：

- aiohttp - 异步 HTTP 客户端/服务器
- g4f - 免费 GPT API 服务
- pillow - 图像处理
- python-dotenv - 环境变量管理
- requests - HTTP 请求
- ujson - 高性能 JSON 处理

## 使用方法

1. 启动 ComfyUI
2. 点击界面右下角的 AI 助手图标
3. 在设置中选择 AI 服务和模型
4. 开始对话

## 开发文档

### 目录结构

```
comfy_ai_assistant/
├── __init__.py               # 入口文件
├── requirements.txt          # 依赖清单
├── models_cache/             # 模型缓存目录
├── ai_services/              # AI 服务实现
│   ├── __init__.py           # 服务模块初始化
│   ├── base_service.py       # 基础服务类
│   ├── service_manager.py    # 服务管理器
│   └── integrations/         # 具体服务实现
│       ├── __init__.py
│       ├── g4f_service.py    # G4F 服务实现
│       ├── local_service.py  # 本地模型服务
│       └── claude_service.py # Claude 服务
├── server/                   # 服务器实现
│   ├── __init__.py
│   ├── api_server.py         # API 服务器
│   ├── routes.py             # 路由定义
│   ├── utils.py              # 服务器工具
│   └── validators.py         # 数据验证
└── web/                      # 前端实现
    ├── ai_index.js           # 入口文件
    ├── ai_ui.js              # UI 管理
    ├── manifest.json         # 扩展清单
    ├── README.md             # 前端文档
    ├── styles/               # 样式
    ├── services/             # 前端服务
    └── components/           # UI 组件
```

### 后端架构

ComfyUI AI Assistant 后端采用模块化设计，主要由以下几个部分组成：

#### 1. 入口模块 (`__init__.py`)

负责初始化扩展并注册到 ComfyUI，包括：

- 初始化 API 服务器
- 注册扩展 Web 目录
- 配置日志系统
- 服务模型初始化

#### 2. 服务管理 (`ai_services/`)

AI 服务层负责与各种 AI 模型的交互：

- `base_service.py`: 定义服务基类接口
- `service_manager.py`: 管理所有 AI 服务实例
- `integrations/`: 各种 AI 服务的具体实现

#### 3. 服务器 (`server/`)

处理 HTTP 请求和路由：

- `api_server.py`: API 服务器实现
- `routes.py`: 路由定义
- `utils.py`: 工具函数
- `validators.py`: 请求数据验证

### 核心类和接口

#### 1. 服务基类 (`BaseService`)

```python
class BaseService:
    def __init__(self, service_id, name, description, **kwargs):
        self.service_id = service_id
        self.name = name
        self.description = description
        self.is_initialized = False
        self.config = {}
        self.set_config(kwargs)
    
    def set_config(self, config):
        """设置服务配置"""
        self.config.update(config)
    
    async def initialize(self):
        """初始化服务，子类需实现"""
        self.is_initialized = True
        return True
    
    async def send_message(self, message, history=None, options=None):
        """发送消息，子类需实现"""
        raise NotImplementedError
    
    def get_models(self):
        """获取可用模型列表，子类需实现"""
        raise NotImplementedError
    
    def get_config_template(self):
        """获取配置模板，子类需实现"""
        raise NotImplementedError
```

#### 2. 服务管理器 (`ServiceManager`)

```python
class ServiceManager:
    def __init__(self):
        self.services = {}
        self.default_service = None
    
    def register_service(self, service):
        """注册 AI 服务"""
        self.services[service.service_id] = service
        if self.default_service is None:
            self.default_service = service.service_id
    
    def get_service(self, service_id=None):
        """获取指定 ID 的服务实例"""
        if service_id is None:
            service_id = self.default_service
        return self.services.get(service_id)
    
    def get_all_services(self):
        """获取所有已注册服务"""
        return {id: {
            "id": s.service_id,
            "name": s.name,
            "description": s.description
        } for id, s in self.services.items()}
```

#### 3. G4F 服务实现 (`G4FService`)

```python
class G4FService(BaseService):
    def __init__(self):
        super().__init__(
            service_id="g4f",
            name="G4F Models",
            description="Free and open source models via G4F library"
        )
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_cache")
        self.cache_file = os.path.join(self.cache_dir, "g4f_models.json")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_models(self):
        """获取模型列表，优先从网络获取，失败则从缓存读取，都失败则使用静态列表"""
        try:
            # 尝试从 G4F 动态获取
            models = []
            # 获取所有模型
            for model in g4f.models.ModelUtils.convert():
                model_id = model.__name__
                model_name = model.__name__.replace('_', '-').upper()
                model_path = f"g4f.models.{model_id}"
                models.append({
                    "id": model_id,
                    "name": model_name,
                    "model_path": model_path
                })
            
            # 成功获取后保存到缓存
            self._save_to_cache(models)
            return models
        except Exception as e:
            logger.warning(f"Failed to get models from G4F: {e}")
            
            # 尝试从缓存读取
            try:
                return self._load_from_cache()
            except Exception as e:
                logger.warning(f"Failed to load models from cache: {e}")
                
                # 使用静态列表作为备选
                static_models = [
                    {"id": "gpt_35_turbo", "name": "GPT-3.5-Turbo", "model_path": "g4f.models.gpt_35_turbo"},
                    {"id": "gpt_4", "name": "GPT-4", "model_path": "g4f.models.gpt_4"},
                    {"id": "claude", "name": "Claude", "model_path": "g4f.models.claude"},
                ]
                
                # 保存静态列表到缓存
                self._save_to_cache(static_models)
                return static_models
    
    def _map_model_name(self, model_name):
        """映射模型名称到实际模型对象"""
        models = self.get_models()
        
        # 检查是否直接匹配 ID 或名称
        for model in models:
            if model_name.lower() == model['id'].lower() or model_name.lower() == model['name'].lower():
                try:
                    # 使用 model_path 动态获取模型对象
                    model_path = model['model_path'].split('.')
                    model_module = importlib.import_module('.'.join(model_path[:-1]))
                    return getattr(model_module, model_path[-1])
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error importing model {model_name}: {e}")
                    break
        
        # 默认返回GPT-3.5
        return g4f.models.gpt_35_turbo

    async def send_message(self, message, history=None, options=None):
        """发送消息到 G4F 服务"""
        if options is None:
            options = {}
        
        model_name = options.get('model', 'gpt_35_turbo')
        model = self._map_model_name(model_name)
        
        # 构建消息历史
        messages = []
        if history:
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
        
        # 添加当前消息
        if isinstance(message, str):
            messages.append({"role": "user", "content": message})
        else:
            messages.append(message)
        
        try:
            # 调用 G4F API
            response = await g4f.ChatCompletion.create_async(
                model=model,
                messages=messages,
                temperature=float(options.get('temperature', 0.7)),
                top_p=float(options.get('top_p', 1.0)),
                max_tokens=int(options.get('max_tokens', 4000)),
                stream=options.get('stream', False)
            )
            
            return response
        except Exception as e:
            logger.error(f"Error in G4F service: {e}")
            return f"Error: {str(e)}"
    
    def _save_to_cache(self, models):
        """保存模型列表到缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(models, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save models to cache: {e}")
    
    def _load_from_cache(self):
        """从缓存文件加载模型列表"""
        if not os.path.exists(self.cache_file):
            raise FileNotFoundError(f"Cache file not found: {self.cache_file}")
        
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
```

#### 4. API 服务器 (`APIServer`)

```python
class APIServer:
    def __init__(self, comfy_app):
        self.comfy_app = comfy_app
        self.service_manager = ServiceManager()
        self.initialize_services()
        self.register_routes()
    
    def initialize_services(self):
        """初始化并注册所有 AI 服务"""
        # 注册 G4F 服务
        g4f_service = G4FService()
        self.service_manager.register_service(g4f_service)
        
        # 注册其他服务...
    
    def register_routes(self):
        """注册 API 路由"""
        from .routes import register_routes
        register_routes(self.comfy_app, self.service_manager)
```

### API 路由

API 路由定义在 `server/routes.py` 中，主要包括：

#### 1. 获取服务列表

```python
@routes.get("/ai/services")
async def get_services(request):
    """获取所有可用的 AI 服务"""
    service_manager = request.app['ai_service_manager']
    services = service_manager.get_all_services()
    return web.json_response({"success": True, "services": services})
```

#### 2. 获取模型列表

```python
@routes.get("/ai/models")
async def get_models(request):
    """获取指定服务的可用模型"""
    service_manager = request.app['ai_service_manager']
    service_id = request.query.get('service', None)
    
    service = service_manager.get_service(service_id)
    if not service:
        return web.json_response({
            "success": False,
            "error": f"Service {service_id} not found"
        }, status=404)
    
    models = service.get_models()
    return web.json_response({"success": True, "models": models})
```

#### 3. 发送消息

```python
@routes.post("/ai/chat")
async def chat(request):
    """发送消息到 AI 服务"""
    try:
        data = await request.json()
        service_manager = request.app['ai_service_manager']
        
        # 验证请求数据
        validate_chat_request(data)
        
        # 获取服务
        service_id = data.get('service', None)
        service = service_manager.get_service(service_id)
        if not service:
            return web.json_response({
                "success": False,
                "error": f"Service {service_id} not found"
            }, status=404)
        
        # 处理消息
        message = data.get('message', '')
        history = data.get('history', [])
        options = data.get('options', {})
        
        # 处理图像
        if 'images' in data and data['images']:
            message = await process_images(message, data['images'])
        
        # 发送消息
        response = await service.send_message(message, history, options)
        
        return web.json_response({
            "success": True,
            "response": response
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)
```

#### 4. 保存历史记录

```python
@routes.post("/ai/save_history")
async def save_history(request):
    """保存聊天历史记录"""
    try:
        data = await request.json()
        
        # 验证数据
        if 'history' not in data or not isinstance(data['history'], list):
            return web.json_response({
                "success": False,
                "error": "Invalid history data"
            }, status=400)
        
        # 获取服务 ID
        service_id = data.get('service', 'default')
        
        # 保存历史记录
        history_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history")
        os.makedirs(history_dir, exist_ok=True)
        
        history_file = os.path.join(history_dir, f"{service_id}_history.json")
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data['history'], f, indent=2)
        
        return web.json_response({"success": True})
    except Exception as e:
        logger.error(f"Error saving history: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)
```

#### 5. 加载历史记录

```python
@routes.get("/ai/history")
async def get_history(request):
    """获取聊天历史记录"""
    try:
        service_id = request.query.get('service', 'default')
        
        history_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history")
        history_file = os.path.join(history_dir, f"{service_id}_history.json")
        
        if not os.path.exists(history_file):
            return web.json_response({"success": True, "history": []})
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        return web.json_response({"success": True, "history": history})
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)
```

### 开发指南

#### 添加新的 AI 服务

1. 在 `ai_services/integrations/` 目录创建新的服务文件，例如 `new_service.py`
2. 实现 `BaseService` 的子类，确保实现所有必要方法
3. 在 `service_manager.py` 中注册新服务

```python
# 新服务示例
class NewService(BaseService):
    def __init__(self):
        super().__init__(
            service_id="new_service",
            name="New AI Service",
            description="Description of the new service"
        )
    
    async def initialize(self):
        # 初始化代码
        return True
    
    async def send_message(self, message, history=None, options=None):
        # 发送消息实现
        pass
    
    def get_models(self):
        # 获取模型列表
        return [
            {"id": "model1", "name": "Model 1"},
            {"id": "model2", "name": "Model 2"}
        ]
    
    def get_config_template(self):
        # 配置模板
        return {
            "api_key": {"type": "string", "required": True, "description": "API Key"}
        }
```

#### 添加新的 API 端点

1. 在 `server/routes.py` 中定义新的路由处理函数
2. 使用 `routes.get()` 或 `routes.post()` 装饰器注册路由

```python
# 新 API 端点示例
@routes.post("/ai/new_endpoint")
async def new_endpoint(request):
    try:
        data = await request.json()
        # 处理逻辑
        return web.json_response({"success": True, "data": result})
    except Exception as e:
        logger.error(f"Error in new endpoint: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)
```

#### 数据验证

使用 `server/validators.py` 中的验证函数确保请求数据符合预期：

```python
def validate_chat_request(data):
    """验证聊天请求数据"""
    if 'message' not in data and 'images' not in data:
        raise ValueError("Request must contain 'message' or 'images'")
    
    if 'options' in data and not isinstance(data['options'], dict):
        raise ValueError("'options' must be an object")
    
    if 'history' in data and not isinstance(data['history'], list):
        raise ValueError("'history' must be an array")
```

### 调试技巧

1. 日志记录
   - 项目使用 Python 的 `logging` 模块记录日志
   - 日志级别在 `__init__.py` 中配置
   - 重要操作和错误都会记录在日志中

2. 错误处理
   - 服务和 API 端点都有完善的错误处理机制
   - 错误信息会返回给前端并记录到日志

3. 测试工具
   - 可以使用 `curl` 或 Postman 测试 API 端点
   - 示例:
     ```bash
     curl -X POST http://localhost:8188/ai/chat \
       -H "Content-Type: application/json" \
       -d '{"service":"g4f","message":"Hello","options":{"model":"gpt_35_turbo"}}'
     ```

## 贡献指南

欢迎通过以下方式贡献：

1. 提交 bug 报告或功能请求
2. 提交 PR 修复 bug 或添加新功能
3. 改进文档

## 许可证

MIT

## 作者

[Pan Qinjian](https://github.com/panqinjian)

DEFAULT_CONFIG = {
        "service": "g4f",
        "service_list": [
            "G4F(免费)",
            "通义千问"
            ],
        "service_ID_list": [
            "q4f",
            "qianwen"
            ],
        "ai_params": {
            "system_prompt": "你是一个AI助手，请帮助用户解决问题。",
            "temperature": 1,
            "max_tokens": 2000,
            "timeout": 300,
            "model": "",
            "proxy": "",
            "api_key": "",
            "api_base": "",
            "api_type": "",
            "api_version": ""
            }
    }

