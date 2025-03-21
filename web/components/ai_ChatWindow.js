/**
 * AI助手聊天窗口组件
 */
import AiUi from '../ai_ui.js';
import aiService from '../services/ai_Service.js';

class AiChatWindow {
    constructor(container) {
        this.aiUi = AiUi;
        this.container = container;
        this.aiService = aiService;
        this.element = document.createElement('div');
        this.element.className = 'ai-chat-window';
        this.parentContainer = null;
        this.visible = false;
        this.selectedImages = [];  // 存储已选择的图片
        this.initialized = this.init();
    }

    async init() {
        // 获取父容器
        this.parentContainer = this.aiUi.aiAssistantWindow.getWindowContainer('chat');
        if (!this.parentContainer) {
            console.error('找不到聊天窗口的父容器');
            return;
        }

        // 设置基本样式
        this.element.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: none;
            flex-direction: column;
            color: #ffffff;
            box-sizing: border-box;
            background-color: #1e1e2e;
            overflow: hidden;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // 创建消息区域
        const messagesArea = document.createElement('div');
        messagesArea.className = 'ai-chat-messages';
        messagesArea.style.cssText = `
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
        `;
        
        // 创建输入区域
        const inputArea = document.createElement('div');
        inputArea.className = 'ai-input-area';
        inputArea.style.cssText = `
            padding: 15px;
            border-top: 1px solid #3a3a4a;
            display: flex;
            flex-direction: column;
            background-color: #2a2a3a;
        `;
        
        // 创建附件预览区域
        const attachmentPreview = document.createElement('div');
        attachmentPreview.className = 'ai-attachment-preview';
        attachmentPreview.style.cssText = `
            display: none;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
            padding: 5px;
            border-radius: 4px;
            background-color: #1e1e2e;
        `;
        
        // 创建输入控制区域
        const inputControls = document.createElement('div');
        inputControls.className = 'ai-input-controls';
        inputControls.style.cssText = `
            display: flex;
            align-items: center;
        `;
        
        // 创建输入框
        const input = document.createElement('textarea');
        input.className = 'ai-input';
        input.placeholder = '输入消息...';
        input.rows = 1;
        input.style.cssText = `
            flex: 1;
            padding: 10px;
            border: 1px solid #3a3a4a;
            border-radius: 4px;
            background-color: #1e1e2e;
            color: #ffffff;
            resize: none;
            font-family: inherit;
            font-size: 14px;
            margin-right: 10px;
        `;
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
            
            // 自动调整高度
            setTimeout(() => {
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            }, 0);
        });
        
        // 创建图片上传按钮
        const imageButton = document.createElement('button');
        imageButton.className = 'ai-image-button';
        imageButton.title = '选择图片';
        imageButton.style.cssText = `
            padding: 8px;
            margin-right: 10px;
            background-color: #5a5a6a;
            border: none;
            border-radius: 4px;
            color: #ffffff;
            cursor: pointer;
            transition: background-color 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // 图片图标
        imageButton.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM19 19H5V5H19V19ZM9.5 13.5L7 17H17L13.5 12L11 15.5L9.5 13.5Z" fill="white"/>
            </svg>
        `;
        
        imageButton.addEventListener('mouseover', () => {
            imageButton.style.backgroundColor = '#6a6a7a';
        });
        imageButton.addEventListener('mouseout', () => {
            imageButton.style.backgroundColor = '#5a5a6a';
        });
        
        imageButton.addEventListener('click', () => {
            // 触发ComfyUI的图片选择器
            this.openComfyImageSelector();
        });
        
        // 创建发送按钮
        const sendButton = document.createElement('button');
        sendButton.className = 'ai-send-button';
        sendButton.textContent = '发送';
        sendButton.style.cssText = `
            padding: 8px 16px;
            background-color: #5a5a6a;
            border: none;
            border-radius: 4px;
            color: #ffffff;
            cursor: pointer;
            transition: background-color 0.3s;
        `;
        sendButton.addEventListener('mouseover', () => {
            sendButton.style.backgroundColor = '#6a6a7a';
        });
        sendButton.addEventListener('mouseout', () => {
            sendButton.style.backgroundColor = '#5a5a6a';
        });
        sendButton.addEventListener('click', () => this.sendMessage());
        
        // 组装输入控制区域
        inputControls.appendChild(input);
        inputControls.appendChild(imageButton);
        inputControls.appendChild(sendButton);
        
        // 组装输入区域
        inputArea.appendChild(attachmentPreview);
        inputArea.appendChild(inputControls);
        
        // 组装聊天窗口
        this.element.appendChild(messagesArea);
        this.element.appendChild(inputArea);
        
        // 保存引用
        this.messagesArea = messagesArea;
        this.input = input;
        this.sendButton = sendButton;
        this.attachmentPreview = attachmentPreview;
        this.imageButton = imageButton;
        
        // 添加到父容器
        this.parentContainer.innerHTML = ''; // 清除原有内容
        this.parentContainer.appendChild(this.element);
        
        // 创建样式表添加动画
        const styleSheet = document.createElement('style');
        styleSheet.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .ai-message-user {
                background-color: #4a5a8a !important;
                border-radius: 18px 18px 0 18px !important;
            }
            
            .ai-message-assistant {
                background-color: #2a3a4a !important;
                border-radius: 18px 18px 18px 0 !important;
            }
            
            .ai-message-content {
                line-height: 1.5;
            }
            
            .ai-message-content pre {
                background-color: #1a1a2a;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 8px 0;
            }
            
            .ai-message-content code {
                background-color: #1a1a2a;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: monospace;
            }
            
            .ai-message-content img {
                max-width: 100%;
                max-height: 300px;
                border-radius: 5px;
                margin: 5px 0;
            }
            
            .ai-attachment-thumbnail {
                position: relative;
                width: 80px;
                height: 80px;
                border-radius: 5px;
                overflow: hidden;
                border: 1px solid #3a3a4a;
            }
            
            .ai-attachment-thumbnail img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .ai-attachment-thumbnail .remove-image {
                position: absolute;
                top: 2px;
                right: 2px;
                width: 20px;
                height: 20px;
                background-color: rgba(0, 0, 0, 0.5);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: white;
                font-size: 12px;
            }
        `;
        document.head.appendChild(styleSheet);
        
        // 默认隐藏
        this.hide();
        
        // 立即加载历史记录
        //await this.loadHistory();
    }

    // 处理显示/隐藏状态
    show_hide(show) {
        if (show) {
            this.show();
        } else {
            this.hide();
        }
    }

    // 显示窗口
    show() {
        if (!this.visible) {
            this.element.style.display = 'flex';
            // 使用 requestAnimationFrame 来确保 display 更改已经生效
            requestAnimationFrame(() => {
                this.element.style.opacity = '1';
            });
            this.visible = true;
        }
    }

    // 隐藏窗口
    hide() {
        if (this.visible) {
            this.element.style.opacity = '0';
            // 等待过渡效果完成后隐藏元素
            setTimeout(() => {
                if (!this.visible) { // 再次检查状态，避免在过渡期间被重新显示
                    this.element.style.display = 'none';
                }
            }, 300); // 与 CSS 过渡时间匹配
            this.visible = false;
        }
    }

    addMessage(role, content, images = []) {
        const message = document.createElement('div');
        message.className = `ai-message ${role === 'user' ? 'ai-message-user' : 'ai-message-assistant'}`;
        message.style.cssText = `
            margin-bottom: 15px;
            align-self: ${role === 'user' ? 'flex-end' : 'flex-start'};
            max-width: 85%;
        `;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'ai-message-content';
        messageContent.style.cssText = `
            padding: 12px 15px;
            border-radius: 18px;
        `;
        messageContent.innerHTML = this.formatMessage(content);
        
        // 添加图片到消息内容
        if (images && images.length > 0) {
            images.forEach(imageUrl => {
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = '附件图片';
                img.style.cursor = 'pointer';
                img.addEventListener('click', () => {
                    // 点击图片放大查看
                    this.showImageViewer(imageUrl);
                });
                messageContent.appendChild(img);
            });
        }
        
        message.appendChild(messageContent);
        this.messagesArea.appendChild(message);
        
        // 滚动到底部
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
    }
    
    showImageViewer(imageUrl) {
        // 创建图片查看器
        const viewer = document.createElement('div');
        viewer.className = 'ai-image-viewer';
        viewer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            cursor: zoom-out;
        `;
        
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = '查看图片';
        img.style.cssText = `
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        `;
        
        viewer.appendChild(img);
        document.body.appendChild(viewer);
        
        // 点击关闭
        viewer.addEventListener('click', () => {
            document.body.removeChild(viewer);
        });
    }
    
    clearMessages() {
        this.messagesArea.innerHTML = '';
    }
    
    async loadHistory() {
        try {
            // 清空消息区域
            this.clearMessages();
            
            // 显示加载中
            const loadingElement = document.createElement('div');
            loadingElement.className = 'ai-loading';
            loadingElement.style.cssText = `
                align-self: center;
                margin: 20px 0;
            `;
            const spinner = document.createElement('div');
            spinner.className = 'ai-spinner';
            spinner.style.cssText = `
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: #ffffff;
                animation: spin 1s infinite linear;
            `;
            loadingElement.appendChild(spinner);
            this.messagesArea.appendChild(loadingElement);
            
            // 获取历史记录
            const history = await this.aiService.getHistory();
            
            // 移除加载中
            this.messagesArea.removeChild(loadingElement);
            
            // 如果没有历史记录
            if (!history || history.length === 0) {
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'ai-message';
                emptyMessage.style.cssText = `
                    align-self: center;
                    margin: 20px 0;
                    color: rgba(255, 255, 255, 0.7);
                `;
                emptyMessage.innerHTML = '<div class="ai-message-content">开始一个新的对话吧！</div>';
                this.messagesArea.appendChild(emptyMessage);
                return;
            }
            
            // 添加历史消息
            history.forEach(msg => {
                const images = msg.images || [];
                this.addMessage(msg.role, msg.content, images);
            });
        } catch (error) {
            console.error('加载历史记录失败:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'ai-error';
            errorMessage.style.cssText = `
                align-self: center;
                margin: 20px 0;
                padding: 10px 15px;
                background-color: rgba(255, 0, 0, 0.2);
                border-left: 3px solid #ff5555;
                border-radius: 3px;
                color: #ff5555;
            `;
            errorMessage.textContent = `加载历史记录失败: ${error.message}`;
            this.messagesArea.appendChild(errorMessage);
        }
    }
    
    async updateService(serviceId) {
        try {
            // 清空消息区域
            this.clearMessages();
            
            // 显示服务切换通知
            const noticeElement = document.createElement('div');
            noticeElement.className = 'ai-message';
            noticeElement.style.cssText = `
                align-self: center;
                margin: 20px 0;
                color: rgba(255, 255, 255, 0.7);
            `;
            noticeElement.innerHTML = `<div class="ai-message-content">已切换到 ${serviceId} 服务</div>`;
            this.messagesArea.appendChild(noticeElement);
            
            // 加载新服务的历史记录
            await this.loadHistory();
        } catch (error) {
            console.error('更新服务失败:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'ai-error';
            errorMessage.style.cssText = `
                align-self: center;
                margin: 20px 0;
                padding: 10px 15px;
                background-color: rgba(255, 0, 0, 0.2);
                border-left: 3px solid #ff5555;
                border-radius: 3px;
                color: #ff5555;
            `;
            errorMessage.textContent = `更新服务失败: ${error.message}`;
            this.messagesArea.appendChild(errorMessage);
        }
    }

    async sendMessage() {
        const message = this.input.value.trim();
        
        if (!message && this.selectedImages.length === 0) return;
        
        // 清空输入框
        this.input.value = '';
        this.input.style.height = 'auto';
        
        // 禁用按钮防止重复发送
        this.sendButton.disabled = true;
        this.sendButton.style.opacity = '0.7';
        this.sendButton.textContent = '发送中...';
        
        // 获取所有已选择的图片
        const imagesToSend = [...this.selectedImages];
        
        // 清空附件预览
        this.attachmentPreview.innerHTML = '';
        this.attachmentPreview.style.display = 'none';
        this.selectedImages = [];
        
        // 添加用户消息
        this.addMessage('user', message, imagesToSend);
        
        // 显示加载中
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'ai-message ai-message-assistant';
        loadingMessage.style.cssText = `
            margin-bottom: 15px;
            align-self: flex-start;
            max-width: 85%;
        `;
        
        const loadingContent = document.createElement('div');
        loadingContent.className = 'ai-message-content';
        loadingContent.style.cssText = `
            padding: 12px 15px;
            border-radius: 18px;
            display: flex;
            align-items: center;
        `;
        
        const loadingElement = document.createElement('div');
        loadingElement.className = 'ai-loading';
        loadingElement.style.cssText = `
            margin-right: 10px;
        `;
        
        const spinner = document.createElement('div');
        spinner.className = 'ai-spinner';
        spinner.style.cssText = `
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #ffffff;
            animation: spin 1s infinite linear;
        `;
        
        loadingElement.appendChild(spinner);
        loadingContent.appendChild(loadingElement);
        loadingContent.appendChild(document.createTextNode('AI正在思考...'));
        loadingMessage.appendChild(loadingContent);
        this.messagesArea.appendChild(loadingMessage);
        
        // 滚动到底部
        this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        
        // 发送消息
        try {
            // 发送消息与图片
            const data = await this.aiService.sendMessage(message, imagesToSend);
            
            // 移除加载中消息
            this.messagesArea.removeChild(loadingMessage);
            
            // 添加助手响应
            if (data.success) {
                this.addMessage('assistant', data.response, data.images || []);
            } else {
                throw new Error(data.error || '发送消息失败');
            }
        } catch (error) {
            // 移除加载中消息
            this.messagesArea.removeChild(loadingMessage);
            
            // 显示错误消息
            console.error('发送消息失败:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'ai-error';
            errorMessage.style.cssText = `
                align-self: center;
                margin: 20px 0;
                padding: 10px 15px;
                background-color: rgba(255, 0, 0, 0.2);
                border-left: 3px solid #ff5555;
                border-radius: 3px;
                color: #ff5555;
            `;
            errorMessage.textContent = `发送消息失败: ${error.message}`;
            this.messagesArea.appendChild(errorMessage);
        } finally {
            // 恢复按钮状态
            this.sendButton.disabled = false;
            this.sendButton.style.opacity = '1';
            this.sendButton.textContent = '发送';
            this.saveHistory();
        }
    }
    
    // 打开图片选择器
    openComfyImageSelector() {
        // 使用原生文件选择器
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.multiple = true;
        fileInput.style.display = 'none';
        
        fileInput.addEventListener('change', async (e) => {
            if (e.target.files.length > 0) {
                const files = Array.from(e.target.files);
                const uploadedFiles = [];
                
                for (const file of files) {
                    try {
                        // 创建 FormData 对象
                        const formData = new FormData();
                        formData.append('image', file);
                        
                        // 发送上传请求到 ComfyUI
                        const response = await fetch('/upload/image', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error(`上传失败: ${response.statusText}`);
                        }
                        
                        const result = await response.json();
                        if (result.name) {
                            uploadedFiles.push({
                                path: `/api/view?filename=${result.name}&type=input&subfolder=&rand=${Math.random()}`,
                            });
                        }
                    } catch (error) {
                        console.error('上传图片失败:', error);
                    }
                }
                
                if (uploadedFiles.length > 0) {
                    this.handleSelectedImages(uploadedFiles);
                }
            }
            document.body.removeChild(fileInput);
        });
        
        document.body.appendChild(fileInput);
        fileInput.click();
    }
    
    // 处理选择的图片
    handleSelectedImages(files) {
        if (!files || files.length === 0) return;
        
        // 限制图片数量
        const maxImages = 5;
        if (this.selectedImages.length + files.length > maxImages) {
            alert(`最多只能添加${maxImages}张图片`);
            files = files.slice(0, maxImages - this.selectedImages.length);
        }
        
        // 添加图片到预览区域
        files.forEach(file => {
            const imagePath = file.path || file;
            this.selectedImages.push(imagePath);
            
            const thumbnail = document.createElement('div');
            thumbnail.className = 'ai-attachment-thumbnail';
            
            const img = document.createElement('img');
            img.src = imagePath;
            img.alt = file.name || '图片';
            
            const removeButton = document.createElement('div');
            removeButton.className = 'remove-image';
            removeButton.innerHTML = '×';
            removeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeImage(imagePath, thumbnail);
            });
            
            thumbnail.appendChild(img);
            thumbnail.appendChild(removeButton);
            this.attachmentPreview.appendChild(thumbnail);
        });
        
        // 显示附件预览区域
        if (this.selectedImages.length > 0) {
            this.attachmentPreview.style.display = 'flex';
        }
    }
    
    // 移除选择的图片
    removeImage(imagePath, thumbnail) {
        const index = this.selectedImages.indexOf(imagePath);
        if (index !== -1) {
            this.selectedImages.splice(index, 1);
        }
        
        this.attachmentPreview.removeChild(thumbnail);
        
        // 如果没有图片了，隐藏预览区域
        if (this.selectedImages.length === 0) {
            this.attachmentPreview.style.display = 'none';
        }
    }
    
    // 处理窗口大小变化
    handleResize() {
        // 聊天窗口大小变化时的处理逻辑
        // 比如可以重新滚动到底部
        if (this.visible) {
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }
    }
    
    formatMessage(content) {
        if (!content) return '';
        
        // 转义HTML
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // 格式化代码块
        formatted = formatted.replace(/```([\s\S]*?)```/g, (match, code) => {
            return `<pre><code>${code}</code></pre>`;
        });
        
        // 格式化内联代码
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // 转换换行符
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    async saveHistory() {
        // 如果正在加载历史记录，不执行保存操作
        if (this.isLoading) {
            return;
        }
        
        try {
            // 收集所有消息
            const messages = [];
            const messageElements = this.messagesArea.querySelectorAll('.ai-message');
            
            // 如果没有消息，不进行保存
            if (messageElements.length === 0) {
                console.log('无消息可保存');
                return;
            }
            
            messageElements.forEach(messageEl => {
                // 跳过系统消息（中心对齐的消息，如"开始一个新的对话吧！"）
                if (messageEl.style.alignSelf === 'center') {
                    return;
                }
                
                // 确定消息类型
                const isUser = messageEl.classList.contains('ai-message-user');
                const role = isUser ? 'user' : 'assistant';
                
                // 获取消息内容
                const contentEl = messageEl.querySelector('.ai-message-content');
                if (!contentEl) return;
                
                // 获取纯文本内容（去除HTML标签）
                let content = contentEl.innerText || '';
                
                // 收集图片
                const images = [];
                const imgElements = contentEl.querySelectorAll('img');
                imgElements.forEach(img => {
                    if (img.src) {
                        images.push(img.src);
                    }
                });
                
                // 添加到消息列表
                if (content.trim() || images.length > 0) {
                    messages.push({
                        role,
                        content,
                        images
                    });
                }
            });
            
            // 如果有消息，通过服务对象发送到服务器保存
            if (messages.length > 0 && messages != []) {
                // 使用aiService保存历史记录
                const success = await this.aiService.saveHistory(messages);
                
                if (success) {
                    console.log('聊天历史记录已保存');
                } else {
                    throw new Error('保存历史记录失败');
                }
            }
        } catch (error) {
            console.error('保存历史记录失败:', error);
            // 这里只记录错误，不显示给用户，避免干扰用户体验
        }
    }
}

export default AiChatWindow;
