/**
 * AI助手聊天窗口组件
 */
import AiUi from '../ai_ui.js';
import aiService from '../services/ai_Service.js';
import MessageParser from '../utils/messageParser.js';
import AiPromptSelector from './ai_PromptSelector.js';

class AiChatWindow {
    constructor(container) {
        // 基础属性初始化
        this.aiUi = AiUi;
        this.container = container;
        this.aiService = aiService;
        this.element = document.createElement('div');
        this.element.className = 'ai-chat-window';
        
        // 状态相关属性
        this.visible = false;
        this.parentContainer = null;
        this.history_list = 1;
        
        // 消息相关属性
        this.selectedImages = [];
        this.messageParser = null;
        this.Prompt = null;
        
        // UI 组件初始化
        this.inputArea = null;
        this.promptSelector = null;
        this.messagesArea = null;
        
        // Vue 相关
        this.element.__vue__ = this;
        
        // 初始化
        this.initialized = this.init();
    }

    async init() {
        try {
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
                gap: 10px;  // 添加消息间距
        `;
        
        // 创建输入区域
        const inputArea = document.createElement('div');
        inputArea.className = 'ai-input-area';
        inputArea.style.cssText = `
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
                margin: 10px;
            `;
            
            // 创建新的输入区域容器
            const inputContainer = document.createElement('div');
            inputContainer.className = 'ai-input-container';
            inputContainer.style.cssText = `
                position: relative;
                width: 100%;
                height: 100%;
                border: 1px solid #3a3a4a;
                border-width: 0;
                background-color: #1e1e2e;
            display: flex;
                flex-direction: column;
            `;
            
            // 创建提示词标签容器
            const promptTagContainer = document.createElement('div');
            promptTagContainer.className = 'ai-prompt-tag-container';
            promptTagContainer.style.cssText = `
                position: absolute;
                top: 5px;
                left: 5px;
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                z-index: 2;
                pointer-events: auto;
            `;
            
            // 创建输入框容器
            const textareaContainer = document.createElement('div');
            textareaContainer.className = 'ai-textarea-container';
            textareaContainer.style.cssText = `
                position: relative;
                flex: 1;
                min-height: 60px;
        `;
        
        // 创建输入框
        const input = document.createElement('textarea');
        input.className = 'ai-input';
            input.placeholder = '按 # 选择系统提示词，然后输入您的请求...';
        input.rows = 1;
        input.style.cssText = `
                width: 100%;
                box-sizing: border-box;
            padding: 10px;
                border: none;
            background-color: #1e1e2e;
            color: #ffffff;
            resize: none;
            font-family: inherit;
            font-size: 14px;
                height: 100%;
                min-height: 60px;
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
        
            // 初始化拖拽处理器
            import('../utils/dragDropHandler.js').then(module => {
                const DragDropHandler = module.default;
                new DragDropHandler(inputContainer, {
                    onFilesUploaded: ({ images, texts }) => {
                        // 使用静态方法处理图片和文本
                        if (images && images.length > 0) {
                            // 确保 this.inputArea 存在
                            if (this.inputArea) {
                                // 如果 inputArea 有 addSelectedImage 方法，使用它
                                if (typeof this.inputArea.addSelectedImage === 'function') {
                                    images.forEach(img => {
                                        if (img && img.name && img.path) {
                                            this.inputArea.addSelectedImage(img.name, img.path);
                                        }
                                    });
                                } else {
                                    // 否则使用 handleSelectedImages 方法
                                    this.handleSelectedImages(images);
                                }
                            } else {
                                // 如果 inputArea 不存在，直接使用 handleSelectedImages
                                this.handleSelectedImages(images);
                            }
                        }
                        if (texts && texts.length > 0) {
                            // 确保 input 元素存在
                            const inputElement = this.input || (this.inputArea && this.inputArea.input);
                            if (inputElement) {
                                DragDropHandler.handleTextInput(inputElement, texts);
                            } else {
                                console.warn('无法找到输入元素，无法添加文本');
                            }
                        }
                    },
                    onUploadError: ({ fileName, message }) => {
                        this.showNotification(`文件 ${fileName} 处理失败: ${message}`, 'error');
                    }
                });
            });

            
            // 创建底部工具栏
            const toolbarContainer = document.createElement('div');
            toolbarContainer.className = 'ai-toolbar-container';
            toolbarContainer.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 5px 10px;
                background-color: #1e1e2e;
            `;
            
            // 创建历史记录选项
            const historyCheckboxContainer = document.createElement('div');
            historyCheckboxContainer.className = 'ai-history-checkbox-container';
            historyCheckboxContainer.style.cssText = `
                display: flex;
                align-items: center;
            `;
            
            const historyCheckbox = document.createElement('input');
            historyCheckbox.type = 'checkbox';
            historyCheckbox.id = 'ai-history-checkbox';
            historyCheckbox.className = 'ai-history-checkbox';
            historyCheckbox.checked = true;
            historyCheckbox.style.cssText = `
                margin-right: 5px;
            `;
            
            const historyLabel = document.createElement('label');
            historyLabel.htmlFor = 'ai-history-checkbox';
            historyLabel.textContent = '发送历史记录';
            historyLabel.style.cssText = `
                font-size: 12px;
                color: #ffffff;
                margin-right: 10px;
            `;
            
            // 创建历史记录轮数选择框
            const historySelect = document.createElement('select');
            historySelect.className = 'ai-history-select';
            historySelect.style.cssText = `
                padding: 2px 5px;
                background-color: #2a2a40;
                border: 1px solid #3a3a4a;
                border-radius: 4px;
                color: #ffffff;
                font-size: 12px;
                cursor: pointer;
                display: ${historyCheckbox.checked ? 'block' : 'none'};
            `;
            
            // 添加选项
            [1,2,3,4, 5, 6,7,8,9,10,20,100].forEach(num => {
                const option = document.createElement('option');
                option.value = num;
                option.text = `${num}轮`;
                option.selected = num === this.history_list;
                historySelect.appendChild(option);
            });
            
            // 监听选择框变化
            historySelect.addEventListener('change', (e) => {
                this.history_list = parseInt(e.target.value);
            });
            
            // 监听复选框变化
            historyCheckbox.addEventListener('change', (e) => {
                historySelect.style.display = e.target.checked ? 'block' : 'none';
                this.history_list = e.target.checked ? parseInt(historySelect.value) : 0;
            });
            
            historyCheckboxContainer.appendChild(historyCheckbox);
            historyCheckboxContainer.appendChild(historyLabel);
            historyCheckboxContainer.appendChild(historySelect);
            
            // 创建按钮容器
            const buttonsContainer = document.createElement('div');
            buttonsContainer.className = 'ai-buttons-container';
            buttonsContainer.style.cssText = `
                display: flex;
                align-items: center
            `;
            
            // 创建添加当前工作流按钮
            const workflowButton = document.createElement('button');
            workflowButton.className = 'ai-workflow-button';
            workflowButton.title = '添加当前工作流';
            workflowButton.style.cssText = `
                padding: 8px;
                margin-right: 10px;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                cursor: pointer;
                transition: background-color 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
            
            // 工作流图标
            workflowButton.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5z" stroke="white" stroke-width="2"/>
                    <path d="M4 9h16M8 4v16M12 10v8M16 13v5" stroke="white" stroke-width="2"/>
                </svg>
            `;
            
            workflowButton.addEventListener('mouseover', () => {
                workflowButton.style.backgroundColor = '#6a6a7a';
            });
            workflowButton.addEventListener('mouseout', () => {
                workflowButton.style.backgroundColor = '#5a5a6a';
            });
            
            workflowButton.addEventListener('click', () => {
                try {
                    // 检查 ComfyUI 的 app 和 graph 对象是否可用
                    if (typeof app !== 'undefined' && app.graph && typeof app.graph.serialize === 'function') {
                        const workflowData = app.graph.serialize();
                        const jsonString = JSON.stringify(workflowData);
                        
                        // 将工作流JSON添加到输入框中（去除换行符）
                        const currentValue = this.input.value;
                        const cleanJSON = jsonString.replace(/\n/g, ' ');
                        this.input.value = currentValue + (currentValue ? '\n\n' : '') + cleanJSON;
                        
                        // 调整输入框高度
                        this.input.style.height = 'auto';
                        this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
                        
                        // 显示成功提示
                        this.showNotification('当前工作流已添加到输入框', 'success');
                    } else {
                        throw new Error('无法访问ComfyUI工作流，请确保在ComfyUI环境中使用');
                    }
                } catch (error) {
                    console.error('获取工作流失败:', error);
                    this.showNotification('获取工作流失败: ' + error.message, 'error');
                }
            });
            
            // 创建图片按钮
        const imageButton = document.createElement('button');
        imageButton.className = 'ai-image-button';
        imageButton.title = '选择图片';
        imageButton.style.cssText = `
            padding: 8px;
            margin-right: 10px;
                background-color: transparent;
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
                // 使用DragDropHandler的静态方法打开图片选择器
                import('../utils/dragDropHandler.js').then(module => {
                    const DragDropHandler = module.default;
                    DragDropHandler.openLocalImageSelector(images => {
                        if (images && images.length > 0) {
                            this.handleSelectedImages(images);
                        }
                    });
                });
        });
        
        // 创建发送按钮
        const sendButton = document.createElement('button');
        sendButton.className = 'ai-send-button';
            sendButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z"/></svg>';
        sendButton.style.cssText = `
                padding: 8px;
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
        sendButton.addEventListener('mouseover', () => {
            sendButton.style.backgroundColor = '#6a6a7a';
        });
        sendButton.addEventListener('mouseout', () => {
            sendButton.style.backgroundColor = '#5a5a6a';
        });
        sendButton.addEventListener('click', () => this.sendMessage());
        
            // 添加输入框和提示词标签到输入容器
            textareaContainer.appendChild(input);
            textareaContainer.appendChild(promptTagContainer);
            
            // 添加按钮到按钮容器
            buttonsContainer.appendChild(workflowButton);
            buttonsContainer.appendChild(imageButton);
            buttonsContainer.appendChild(sendButton);
            
            // 添加历史记录选项和按钮到工具栏
            toolbarContainer.appendChild(historyCheckboxContainer);
            toolbarContainer.appendChild(buttonsContainer);
            
            // 组装输入容器的各个部分
            inputContainer.appendChild(textareaContainer);
            inputContainer.appendChild(toolbarContainer);
            
            // 添加所有组件到输入区域
        inputArea.appendChild(attachmentPreview);
            inputArea.appendChild(inputContainer);
        
        this.element.appendChild(messagesArea);
        this.element.appendChild(inputArea);
            this.parentContainer.appendChild(this.element);
        
        // 保存引用
        this.messagesArea = messagesArea;
        this.input = input;
        this.sendButton = sendButton;
        this.attachmentPreview = attachmentPreview;
            this.promptTagContainer = promptTagContainer;
            //--this.currentPromptId = ""; // 保存当前选中的提示词ID
            //--this.historyCheckbox = historyCheckbox; // 保存历史记录选项引用
        
        // 创建样式表添加动画
        const styleSheet = document.createElement('style');
        styleSheet.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
                
                .ai-message {
                    max-width: 85%;
                    padding: 10px 15px;
                    margin: 5px 0;
                    border-radius: 12px;
                    word-wrap: break-word;
                    font-size: 14px;
                    line-height: 1.5;
            }
            
            .ai-message-user {
                    background-color: #4a5a8a;
                    border-radius: 12px 12px 2px 12px;
                    align-self: flex-end;
                    color: #ffffff;
            }
            
            .ai-message-assistant {
                    background-color: #2a3a4a;
                    border-radius: 12px 12px 12px 2px;
                    align-self: flex-start;
                    color: #e0e0e0;
            }
            
            .ai-message-content {
                    white-space: pre-wrap;
            }
            
            .ai-message-content pre {
                background-color: #1a1a2a;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 8px 0;
            }
            
            .ai-message-content code {
                font-family: monospace;
                    background-color: rgba(0,0,0,0.2);
                    padding: 2px 4px;
                    border-radius: 3px;
            }
            
            .ai-message-content img {
                max-width: 100%;
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

                /* 优化文本渲染 */
                .ai-chat-window,
                .ai-chat-messages,
                .ai-message,
                .ai-message-content,
                .ai-message-content pre,
                .ai-message-content code,
                .ai-input-area,
                .ai-input {
                    text-rendering: optimizeLegibility;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    font-smooth: always;
                }

                .ai-error-message {
                    color: #ff6b6b;
                    padding: 10px;
                    border-radius: 4px;
                    background-color: rgba(255, 107, 107, 0.1);
                    border: 1px solid rgba(255, 107, 107, 0.2);
                }

                .code-block {
                    background: #1e1e2e;
                    border-radius: 4px;
                    margin: 1em 0;
                    overflow: hidden;
                }

                .code-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background: #2a2a3a;
                    border-bottom: 1px solid #3a3a4a;
                }

                .code-lang {
                    color: #7f849c;
                    font-size: 0.9em;
                }

                .copy-button {
                    background: #3a3a4a;
                    border: none;
                    color: #cdd6f4;
                    padding: 4px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: background 0.2s;
                }

                .copy-button:hover {
                    background: #45475a;
                }

                .code-block pre {
                    margin: 0;
                    padding: 1em;
                    overflow-x: auto;
                }

                .code-block code {
                    font-family: 'Fira Code', monospace;
                    font-size: 0.9em;
                    line-height: 1.5;
                }

                /* 自定义滚动条 */
                .code-block pre::-webkit-scrollbar {
                    height: 8px;
                }

                .code-block pre::-webkit-scrollbar-track {
                    background: #2a2a3a;
                }

                .code-block pre::-webkit-scrollbar-thumb {
                    background: #4a4a5a;
                    border-radius: 4px;
            }
        `;
        document.head.appendChild(styleSheet);
        
        // 默认隐藏
        this.hide();
        
        // 立即加载历史记录
        //await this.loadHistory();

            // 添加窗口大小变化监听器
            window.addEventListener('resize', () => this.handleResize());

            // 初始化提示词选择器
            this.promptSelector = new AiPromptSelector(this.input, (prompt) => {
                console.log('选择了提示词:', prompt.prompt_name);
                this.Prompt = prompt;
                this.setPromptTag(prompt);
            });

            // 确保消息区域有正确的样式
            if (this.messagesArea) {
                Object.assign(this.messagesArea.style, {
                    overflow: 'auto',
                    maxHeight: '100%',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    scrollBehavior: 'smooth'  // 添加平滑滚动
                });
            }
        } catch (error) {
            console.error('初始化聊天窗口失败:', error);
        }
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
            this.handleResize();
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

    /**
     * 添加消息到聊天窗口
     * @param {string|number} message_id - 消息ID，用于历史记录分页
     * @param {string} role - 消息角色 (user/assistant)
     * @param {string|object} content - 消息内容
     * @param {Array} images - 图片数组
     */
    addMessage(role, content, images = [], promptName = null, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ai-message-${role}`;
        
        // 设置消息ID属性
        if (messageId) {
            messageDiv.setAttribute('data-message-id', messageId);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'ai-message-content';
        
        // 使用 MessageParser 处理内容
        let parsedContent;
        if (role === "user") {
            parsedContent = this.messageParser.parseMessage_user(
                content, 
                promptName || (this.Prompt ? this.Prompt.prompt_name : null),
                images
            );
                    } else {
            parsedContent = this.messageParser.parseMessage(content, "html");
            parsedContent=content
        }
            
        contentDiv.innerHTML = parsedContent;
        messageDiv.appendChild(contentDiv);

        // 根据 messageId 确定插入位置
        if (messageId) {
            // 获取所有消息元素
            const messages = this.messagesArea.querySelectorAll('.ai-message[data-message-id]');
            let insertPosition = null;

            // 找到合适的插入位置
            for (const msg of messages) {
                const currentId = parseInt(msg.getAttribute('data-message-id'));
                if (currentId > messageId) {
                    insertPosition = msg;
                    break;
                }
            }

            // 插入消息
            if (insertPosition) {
                // 如果找到了插入位置，在该位置之前插入
                this.messagesArea.insertBefore(messageDiv, insertPosition);
            } else {
                // 如果没找到，说明是最新的消息，追加到末尾
                this.messagesArea.appendChild(messageDiv);
            }
        } else {
            // 如果没有 messageId，直接追加到末尾（新消息）
            this.messagesArea.appendChild(messageDiv);
            this.scrollToBottom();
        }

        return messageDiv;
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
            const result = await this.aiService.getHistory();
            this.messagesArea.innerHTML = '';

            if (result.records && result.records.length > 0) {
                console.log('历史记录数据:', {
                    hasMore: result.hasMore,
                    nextId: result.nextId,
                    recordCount: result.records.length
                });

                // 如果有更多记录可用，先添加加载更多按钮
                if (result.hasMore && result.nextId) {
                    console.log('添加加载更多按钮，下一页ID:', result.nextId);
                    this.addLoadMoreButton(result.nextId);
                }

                // 添加历史记录消息
                result.records
                    .slice()
                    .sort((a, b) => a.message_id - b.message_id)
                    .forEach(record => {
                        this.addMessage(
                            'user',
                            record.user.content,
                            record.user.images || [],
                            record.user.prompt_name,
                            record.message_id  // 传递消息ID
                        );
                        
                        this.addMessage(
                            'assistant',
                            record.assistant.content,
                            record.assistant.images || [],
                            null,
                            record.message_id  // 使用相同的消息ID
                        );
                    });
                
                console.log('历史记录加载完成');
                this.scrollToBottom();
            } else {
                this.showWelcomeMessage();
                this.scrollToBottom();
            }

        } catch (error) {
            console.error('加载历史记录失败:', error);
            this.showErrorMessage(error);
            this.scrollToBottom();
        }
    }
    

    showWelcomeMessage() {
        const welcomeMessage = document.createElement('div');
        welcomeMessage.className = 'ai-message ai-welcome-message';  // 添加特定类名
        welcomeMessage.style.cssText = `
                    align-self: center;
                    margin: 20px 0;
                    color: rgba(255, 255, 255, 0.7);
                `;
        welcomeMessage.innerHTML = '<div class="ai-message-content">开始一个新的对话吧！</div>';
        this.messagesArea.appendChild(welcomeMessage);
    }

    showErrorMessage(error) {
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
    
    async updateService1(serviceId) {
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
        try {
            // 隐藏欢迎消息
            this.hideWelcomeMessage();
        
            const message = this.input.value.trim();
        if (!message && this.selectedImages.length === 0) return;
        
            this.disableInput(true);
            
            // 显示用户消息
            this.addMessage('user', message, this.selectedImages);
            
            // 显示思考消息
            const aiMessageDiv = this.addMessage('ai', '<div class="ai-thinking">AI 正在思考...</div>');
            aiMessageDiv.classList.add('ai-thinking-message');
            
            // 发送消息
            const response = await this.aiService.sendMessage(message, this.selectedImages, this.history_list,
                this.Prompt ? this.Prompt.prompt_id : ""
            );

            if (response.success) {
                this.clearAttachmentPreview();
                this.addMessage('assistant', response.response, response.images || []);
            } else {
                // 显示错误消息
                this.addMessage('assistant', `<div class="ai-error-message">😔 抱歉，发生了错误：${response.error || '未知错误'}</div>`);
            }
            
            // 隐藏思考消息
            this.hideThinkingMessage();
            
        } catch (error) {
            this.hideThinkingMessage();
            
            // 显示错误消息
            let errorMessage = error.message;
            if (errorMessage.includes('G4F 服务错误')) {
                errorMessage = errorMessage.replace('G4F 服务错误:', '').trim();
            }
            this.addMessage('assistant', `<div class="ai-error-message">😔 抱歉，服务出现问题：${errorMessage}</div>`);
            
        } finally {
            this.disableInput(false);
            this.clearInput();
        this.selectedImages = [];
        }
    }

    // 辅助方法
    disableInput(disabled) {
        this.input.disabled = disabled;
        this.sendButton.disabled = disabled;
    }


    handleError(error, aiMessageDiv) {
        this.messagesArea.removeChild(aiMessageDiv);
        
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
    }

    clearInput() {
        this.input.value = '';
        this.input.style.height = 'auto';
    }
    
    // 处理选择的图片
    handleSelectedImages(files) {
        import('../utils/dragDropHandler.js').then(module => {
            const DragDropHandler = module.default;
            DragDropHandler.handleSelectedImages(
                files,
                this.attachmentPreview,
                this.selectedImages,
                (imagePath, thumbnail) => this.removeImage(imagePath, thumbnail)
            );
        });
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
        if (this.visible) {
            this.adjustMessageWidth();
            this.fixTextRendering();
        }
    }
    
    // 调整消息宽度
    adjustMessageWidth() {
        const containerWidth = this.messagesArea.clientWidth;
        const messages = this.messagesArea.querySelectorAll('.ai-message');

        messages.forEach(message => {
            // 根据容器宽度设置消息的最大宽度
            // 可以根据实际情况调整这里的阈值和百分比
            if (containerWidth > 800) {
                message.style.maxWidth = '90%';
            } else {
                message.style.maxWidth = '80%';
            }
        });
    }
    
    // 强制文本重绘
    fixTextRendering() {
        // 通过改变 opacity 触发重绘
        this.element.style.opacity = 0.99;
        setTimeout(() => {
            this.element.style.opacity = 1;
        }, 10);
    }
    

    // 处理拖放的文件
    async handleDroppedFiles(files) {
        // 使用DragDropHandler的静态方法处理拖放的文件
        import('../utils/dragDropHandler.js').then(module => {
            const DragDropHandler = module.default;
            DragDropHandler.handleDroppedFiles(
                files,
                (uploadedFiles) => {
        if (uploadedFiles.length > 0) {
            this.handleSelectedImages(uploadedFiles);
        }
                },
                (fileName, errorMessage) => {
                    this.showUploadErrorNotification(fileName, errorMessage);
                }
            );
        });
    }
    
    // 处理ComfyUI图片URL
    handleComfyUIImage(url) {
        // 使用DragDropHandler的静态方法处理ComfyUI图片URL
        import('../utils/dragDropHandler.js').then(module => {
            const DragDropHandler = module.default;
            const imageObj = DragDropHandler.handleComfyUIImage(url);
            this.handleSelectedImages([imageObj]);
        });
    }
    
    // 显示上传错误通知
    showUploadErrorNotification(fileName, errorMessage) {
        const notification = document.createElement('div');
        notification.textContent = `上传图片 "${fileName}" 失败: ${errorMessage}`;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: #333;
            color: #fff;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            border-left: 4px solid #ff5555;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = "0";
            notification.style.transition = "opacity 0.5s ease";
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }
    
    // 处理文本文件，读取内容到输入框
    async handleTextFiles(files, inputElement) {
        if (!files || files.length === 0) return;
        
        // 使用DragDropHandler的静态方法处理文本文件
        import('../utils/dragDropHandler.js').then(module => {
            const DragDropHandler = module.default;
            // 如果有多个文件，只处理第一个
            const file = files[0];
            console.log('准备处理文本文件:', file.name);
            DragDropHandler.handleTextFile(
                file, 
                inputElement || this.input, // 确保有输入元素
                (successMsg) => this.showNotification(successMsg, 'success'),
                (errorMsg) => this.showNotification(errorMsg, 'error')
            );
        });
    }
    
    // 通用通知方法
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.textContent = message;
        
        let borderColor = '#3498db'; // 默认信息蓝色
        
        if (type === 'success') {
            borderColor = '#2ecc71'; // 成功绿色
        } else if (type === 'error') {
            borderColor = '#e74c3c'; // 错误红色
        } else if (type === 'warning') {
            borderColor = '#f39c12'; // 警告黄色
        }
        
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: #333;
            color: #fff;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            border-left: 4px solid ${borderColor};
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = "0";
            notification.style.transition = "opacity 0.5s ease";
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }


    // 添加滚动到底部方法
    scrollToBottom() {
    try {
        // 使用 IntersectionObserver 检查滚动
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) {
                    this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
                }
            });
            // 断开观察器以避免不必要的性能消耗
            observer.disconnect();
        });

        // 观察最后一条消息
        const lastMessage = this.messagesArea.lastElementChild;
        if (lastMessage) {
            observer.observe(lastMessage);
        } else {
            // 如果没有消息，直接滚动到最底部
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }
    } catch (error) {
        console.error('滚动到页面底部时出现错误:', error);
    }
    }    

/**
     * 设置提示词标签
     */

    setPromptTag(prompt) {
    // 清空现有标签
    this.promptTagContainer.innerHTML = '';
    
    // 创建新标签
    const tag = document.createElement('div');
    tag.className = 'ai-prompt-tag';
    tag.style.cssText = `        background-color: #4a5a8a;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        font-size: 12px;
        margin-bottom: 5px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    `;
    
    // 标签文本
    const tagText = document.createElement('span');
    tagText.textContent = prompt.prompt_name;
    
    // 删除按钮
    const removeButton = document.createElement('span');
    removeButton.innerHTML = '&times;';
    removeButton.style.cssText = `
        margin-left: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
    `;
    
    // 点击删除按钮移除标签
    removeButton.addEventListener('click', () => {
        this.promptTagContainer.innerHTML = '';     
        this.Prompt =null;
        // 添加一个方法来重置输入框的内边距
        this.input.style.paddingTop = '10px';
    });
    
    // 组装标签
    tag.appendChild(tagText);
    tag.appendChild(removeButton);
    this.promptTagContainer.appendChild(tag);
    
    // 保存当前提示词ID
    //this.PromptId = prompt.prompt_id;
    // 清空输入框中的 # 字符
    this.input.value = this.input.value.replace(/#[^#]*$/, '').trim();
    
    // 调整输入框的内边距，为标签腾出空间
    this.input.style.paddingTop = '30px';
    
    // 聚焦输入框
    this.input.focus();
    }
   

    /**
     * 清理附件预览区域
     */
    clearAttachmentPreview() {
        if (this.attachmentPreview) {
            this.attachmentPreview.innerHTML = '';
            this.attachmentPreview.style.display = 'none';
        }
    }

    // 添加"加载更多"按钮
    addLoadMoreButton(nextId) {
        const loadMoreDiv = document.createElement('div');
        loadMoreDiv.className = 'ai-load-more';
        loadMoreDiv.style.cssText = `
            align-self: center;
            margin: 10px 0;
            padding: 8px 15px;
            background-color: #2a2a3a;
            border-radius: 4px;
            color: #ffffff;
            cursor: pointer;
            transition: background-color 0.3s;
        `;
        loadMoreDiv.textContent = '加载更多历史记录';
        
        // 添加悬停效果
        loadMoreDiv.addEventListener('mouseover', () => {
            loadMoreDiv.style.backgroundColor = '#3a3a4a';
        });
        loadMoreDiv.addEventListener('mouseout', () => {
            loadMoreDiv.style.backgroundColor = '#2a2a3a';
        });
        
        // 点击加载更多
        loadMoreDiv.addEventListener('click', async () => {
            try {
                loadMoreDiv.textContent = '加载中...';
                loadMoreDiv.style.cursor = 'wait';
                
                const moreHistory = await this.aiService.getHistory(10,nextId);
                if (moreHistory.records && moreHistory.records.length > 0) {
                    // 移除当前的加载更多按钮
                    this.messagesArea.removeChild(loadMoreDiv);
                    
                    // 如果还有更多记录，添加新的加载更多按钮
                    if (moreHistory.hasMore && moreHistory.nextId) {
                        this.addLoadMoreButton(moreHistory.nextId);
                    }

                    // 添加新的历史记录
                    moreHistory.records
                        .slice()
                        .sort((a, b) => a.message_id - b.message_id)
                        .forEach(record => {
                            this.addMessage(
                                'user',
                                record.user.content,
                                record.user.images || [],
                                record.user.prompt_name,
                                record.message_id  // 传递消息ID
                            );
                            
                            this.addMessage(
                                'assistant',
                                record.assistant.content,
                                record.assistant.images || [],
                                null,
                                record.message_id  // 使用相同的消息ID
                            );
                        });
                }
            } catch (error) {
                console.error('加载更多历史记录失败:', error);
                loadMoreDiv.textContent = '加载失败，点击重试';
                loadMoreDiv.style.backgroundColor = '#ff5555';
            } finally {
                loadMoreDiv.style.cursor = 'pointer';
            }
        });
        
        // 插入到消息区域的开头
        this.messagesArea.insertBefore(loadMoreDiv, this.messagesArea.firstChild);
    }

    // 添加新方法来隐藏欢迎消息
    hideWelcomeMessage() {
        const welcomeMessage = this.messagesArea.querySelector('.ai-welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }

    // 添加新方法来隐藏思考消息
    hideThinkingMessage() {
        const thinkingMessage = this.messagesArea.querySelector('.ai-thinking-message');
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
    }
}

export default AiChatWindow;
