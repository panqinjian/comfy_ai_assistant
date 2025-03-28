# ComfyUI AI Assistant 使用指南

## 简介

ComfyUI AI Assistant 是一个集成于 ComfyUI 的智能助手扩展，允许您在 ComfyUI 界面中直接与多种 AI 大语言模型进行交互。无论您需要解答问题、协助创建工作流，还是处理图像，AI 助手都能为您提供帮助。

## 安装方法

### 方法一：Git 克隆（推荐）

1. 打开命令行，进入 ComfyUI 的 custom_nodes 目录：
   ```bash
   cd /path/to/ComfyUI/custom_nodes
   ```

2. 克隆仓库：
   ```bash
   git clone https://github.com/panqinjian/comfy_ai_assistant.git
   ```

3. 进入项目目录并安装依赖：
   ```bash
   cd comfy_ai_assistant
   pip install -r requirements.txt
   ```

### 方法二：下载 ZIP 文件

1. 下载仓库的 ZIP 文件
2. 解压到 ComfyUI 的 `custom_nodes` 目录
3. 进入解压后的目录，运行 `pip install -r requirements.txt`

## 启动助手

1. 启动 ComfyUI
2. 等待界面完全加载
3. 在 ComfyUI 界面右下角，您会看到一个浮动的 AI 助手图标 (🤖)
4. 点击图标打开 AI 助手窗口

## 界面介绍

AI 助手界面主要包含以下几个部分：

### 主窗口

- **标题栏**：显示当前服务和模型名称，包含最小化、设置和关闭按钮
- **聊天区域**：显示对话历史
- **输入区域**：输入文字信息和上传图片
- **发送按钮**：发送消息

### 设置窗口

- **服务选择**：选择要使用的 AI 服务（如 G4F）
- **模型选择**：选择特定服务下的 AI 模型
- **参数设置**：调整 AI 行为的参数（温度、最大tokens等）
- **保存按钮**：保存当前设置

## 基本操作

### 发送文本消息

1. 在输入框中输入您的问题或指令
2. 点击发送按钮或按下 Enter 键
3. 等待 AI 回复（回复将实时流式显示）

### 发送图片

1. 点击输入框旁边的图片按钮
2. 选择要上传的图片
3. 图片将显示在输入框下方的预览区
4. 输入相关文字（可选）
5. 点击发送按钮
6. AI 将分析图片并回复

### 清除聊天记录

1. 点击聊天窗口中的清除按钮
2. 确认清除操作
3. 所有聊天记录将被删除

### 切换服务或模型

1. 点击窗口右上角的设置图标
2. 在服务下拉菜单中选择所需服务
3. 在模型下拉菜单中选择相应模型
4. 调整其他参数（如需要）
5. 点击保存按钮应用更改

## 支持的服务和模型

ComfyUI AI Assistant 支持多种 AI 服务，包括但不限于：

### G4F (Free AI Models)

G4F 服务提供免费访问多种模型，包括：

- GPT-3.5-Turbo - 适合大多数日常任务
- GPT-4 - 更强大的推理和创意能力
- Claude - Anthropic 的对话模型
- 以及更多...

### 本地模型（未来支持）

计划未来支持运行本地模型，如：

- Llama
- Mistral
- Phi-2

## 使用技巧

### 1. 协助创建工作流

您可以要求 AI 助手帮助您创建 ComfyUI 工作流：

```
请帮我创建一个生成风景照片的工作流，我想要使用 SDXL 模型
```

### 2. 图像分析

上传图片并询问关于图片的问题：

```
这张图片中有什么问题？如何改进构图？
```

### 3. 获取节点使用帮助

询问如何使用特定的 ComfyUI 节点：

```
KSampler 节点的参数有什么作用？如何调整以获得更好的结果？
```

### 4. 创意灵感

获取创作灵感：

```
请给我 5 个使用 ComfyUI 创建科幻插画的提示词
```

### 5. 故障排除

遇到问题时寻求帮助：

```
我的 ComfyUI 在加载模型时报错，显示 "CUDA out of memory"，如何解决？
```

## 常见问题解答

### Q: AI 助手响应很慢，如何改善？

A: 尝试以下方法：
- 选择响应更快的模型（如 GPT-3.5 代替 GPT-4）
- 减少历史消息长度
- 降低生成的最大 tokens 数量

### Q: 为什么我上传的图片没有被正确分析？

A: 确保：
- 图片格式受支持（JPG、PNG、WebP）
- 图片大小适中（不超过 10MB）
- 所选模型支持图像分析能力（如 GPT-4 Vision）

### Q: 如何保存我的聊天记录？

A: 聊天历史会自动保存。关闭并重新打开助手后，您之前的对话内容会自动加载。

### Q: 是否需要 API 密钥？

A: 使用 G4F 服务不需要 API 密钥，它是免费的。但功能和稳定性可能有限。

### Q: 为什么有时会收到错误消息？

A: 可能原因包括：
- 网络连接问题
- 所选服务暂时不可用
- 请求超时
- 模型超出容量限制

尝试切换到不同的模型或稍后再试。

## 高级设置

### 温度（Temperature）

控制回答的随机性：
- 较低值（如 0.3）：更确定、一致的回答
- 较高值（如 0.8）：更多样化、创意的回答

### 最大 Tokens

控制回答的最大长度：
- 较低值：简短回答
- 较高值：详细回答（但可能增加响应时间）

### Top-P

控制词汇选择的多样性：
- 较低值：使用更可预测的词汇
- 较高值：使用更多样化的词汇

## 更新和维护

### 更新 AI 助手

通过 Git 更新：
```bash
cd /path/to/ComfyUI/custom_nodes/comfy_ai_assistant
git pull
pip install -r requirements.txt
```

### 更新模型列表

如需刷新可用模型列表：
1. 删除 `models_cache` 目录中的缓存文件
2. 重启 ComfyUI
3. 系统将自动获取最新模型列表

## 故障排除

### 助手无法启动

1. 检查 ComfyUI 控制台是否有错误消息
2. 确认所有依赖都已正确安装
3. 检查 Python 版本是否兼容（推荐 Python 3.8+）

### 无法连接到 AI 服务

1. 检查网络连接
2. 确认防火墙没有阻止连接
3. 尝试切换到不同的服务或模型

### 助手界面显示异常

1. 刷新 ComfyUI 页面
2. 清除浏览器缓存
3. 尝试不同的浏览器

## 联系与支持

如果您遇到任何问题或有功能建议，请通过以下方式联系我们：

- 提交 GitHub Issue
- 加入我们的 Discord 社区

感谢您使用 ComfyUI AI Assistant！