# ComfyUI AI 助手 v1.1

ComfyUI AI 助手是一个为 ComfyUI 设计的扩展，让您能够在图像生成工作流程中与多个AI大语言模型进行交互，助力您的创意过程和问题解决。

![ComfyUI AI 助手截图](https://示例截图链接.png)

## 功能特性

- **多服务支持**：支持多种AI服务提供商，包括G4F(免费)、通义千问等
- **丰富的交互方式**：
  - 文本聊天：向AI提问并获取回答
  - 图像理解：发送图像让AI分析和描述
  - 代码生成与解释：生成工作流相关代码或解释现有代码
- **上下文记忆**：AI能够记住对话上下文，提供连贯的交互体验
- **拖放支持**：支持拖拽上传图片和文本文件
- **会话管理**：保存和加载对话历史
- **UI集成**：无缝集成到ComfyUI界面中
- **代码格式化**：正确显示和导出代码块，保留格式和换行
- **图像上传与分享**：在对话中轻松共享ComfyUI生成的图像

## 安装方法

1. 将此仓库克隆到ComfyUI的`custom_nodes`目录中：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/panqinjian/comfy_ai_assistant.git
```

2. 安装必要的依赖：

```bash
cd comfy_ai_assistant
pip install -r requirements.txt
```

3. 重启ComfyUI

## 使用方法

### 基本使用

1. 启动ComfyUI后，AI助手按钮将出现在界面上
2. 点击按钮打开AI助手窗口
3. 在文本框中输入您的问题或指令
4. 点击发送按钮或按Enter键发送消息
5. AI将处理您的请求并显示回复

### 上传图片

- **方法1**：点击上传图片按钮选择本地图片
- **方法2**：从ComfyUI画布拖放图片到聊天窗口
- **方法3**：将本地图片文件直接拖放到输入框

### 导出代码块

1. 当AI回复包含代码块时，将显示"复制"和"保存"按钮
2. 点击"复制"将代码复制到剪贴板（保留完整格式）
3. 点击"保存"将代码保存为本地文件

### 配置AI服务

1. 在AI助手窗口中点击设置图标
2. 从下拉菜单中选择AI服务提供商
3. 填写相应的API密钥和其他必要参数
4. 点击保存应用设置

## 开发者指南

### 目录结构

```
comfy_ai_assistant/
├── __init__.py              # 扩展入口点
├── web/                     # 前端代码
│   ├── ai_index.js          # 前端主入口
│   ├── ai_ui.js             # UI管理
│   ├── components/          # UI组件
│   │   ├── ai_AssistantWindow.js  # 主窗口
│   │   ├── ai_ChatWindow.js       # 聊天组件
│   │   ├── ai_SettingsWindow.js   # 设置组件
│   │   └── ...
│   ├── services/            # 前端服务
│   │   └── ai_Service.js    # 与后端通信的服务
│   └── styles/              # CSS样式
│       └── main.css
└── ai_services/             # 后端代码
    ├── integrations/        # AI服务集成
    │   ├── base.py          # 基础服务类
    │   ├── g4f_service.py   # G4F服务实现
    │   ├── qianwen_service.py # 通义千问服务实现
    │   └── ...
    ├── configs/             # 配置文件
    ├── chat_api.py          # 聊天API
    ├── config_api.py        # 配置API
    └── history_api.py       # 历史记录API
```

### 添加新的AI服务提供商

要添加新的AI服务提供商，需要完成以下步骤：

1. **创建服务实现类**:
   - 在`ai_services/integrations/`目录下创建新的Python文件（例如：`new_service.py`）
   - 实现一个继承自`BaseService`的类，实现所有必要的方法：

```python
from .base import BaseService

class NewService(BaseService):
    def __init__(self):
        super().__init__()
        # 初始化特定服务参数

    @classmethod
    def get_service_info(cls):
        return {
            "id": "new_service_id",
            "name": "新服务名称",
            "description": "服务描述"
        }

    async def send_message(self, message, stream=False, images=None, host_url=None, history=None):
        # 实现发送消息的逻辑
        pass

    # 实现其他必要的方法...
```

2. **注册服务**:
   - 在`ai_services/__init__.py`中导入并注册新服务

3. **添加配置模板**:
   - 在`ai_services/configs/`目录中添加默认配置文件（例如：`new_service.json`）

4. **更新前端列表**:
   - 更新`ai_services/config_api.py`中的服务列表，添加新的服务ID和显示名称

5. **测试服务**:
   - 重启ComfyUI并测试新添加的服务

### 主要文件说明

- **基础服务类 (base.py)**: 定义了所有AI服务必须实现的接口
- **聊天API (chat_api.py)**: 处理聊天请求的API端点
- **配置API (config_api.py)**: 处理配置读写的API端点
- **历史API (history_api.py)**: 处理对话历史的API端点
- **前端服务 (ai_Service.js)**: 负责与后端API交互
- **聊天窗口 (ai_ChatWindow.js)**: 实现聊天界面和逻辑

## v1.1 版本更新

### 新功能

- **文件拖拽支持**：现在可以直接拖拽文件到聊天窗口
  - 支持本地图片文件上传
  - 支持ComfyUI图像的重用
  - 支持文本文件的导入

### 修复问题

- **发送图片功能**：修复了图片上传和发送到AI的问题
- **上下文管理**：改进了对话上下文的保存和加载机制
- **代码块导出**：修复了代码块复制和保存时格式丢失的问题
  - 代码复制现在能正确保留换行和缩进
  - 代码文件导出格式统一且正确

### 其他改进

- 优化了界面响应速度
- 提升了与ComfyUI的集成稳定性
- 改进错误处理和用户提示

## 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件。

## 贡献指南

欢迎提交问题报告和功能建议。如果您想贡献代码，请先创建issue讨论您的想法。

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [提交问题](https://github.com/panqinjian/comfy_ai_assistant/issues)
- 电子邮件: panzhoulin@gmail.com

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

