class MessageParser {
    constructor() {
        // 简化构造函数，不再需要绑定所有方法
        this.escapeHtml = this.escapeHtml.bind(this);
        this.processTextSegment = this.processTextSegment.bind(this);
        this.isCompleteHtml = this.isCompleteHtml.bind(this);
        this.extractHtmlBlocks = this.extractHtmlBlocks.bind(this);
        this.containsHtml = this.containsHtml.bind(this);
        
        // 添加复制代码功能
        window.copyCode = this.copyCode.bind(this);
    }

    /**
     * 解析消息内容
     * @param {string|object} content 消息内容
     * @returns {Object} 解析结果，按类型分组
     */
    parse(content) {
        // 初始化结果对象
        const result = {
            html: [],    // HTML内容
            code: [],    // 代码块
            text: []     // 普通文本
        };

        try {
            // 如果内容已经是HTML格式对象
            if (typeof content === 'object' && content.content_format === 'html') {
                result.html.push(content.content);
                return result;
            }

            const text = String(content || '');
            
            // 检查是否以<!DOCTYPE html>或<html开头
            if (/^\s*<!DOCTYPE\s+html\s*>/i.test(text) || text.toLowerCase().trim().startsWith('<html')) {
                result.html.push(text);
                return result;
            }
            
            // 首先检查整个内容是否是HTML
            if (this.isCompleteHtml(text)) {
                result.html.push(text);
                return result;
            }
            
                    // 处理代码块
            const codeBlockRegex = /```([\w]*)\n?([\s\S]*?)(?=\n```|$)/g;
            let lastIndex = 0;
            let match;

            while ((match = codeBlockRegex.exec(text)) !== null) {
                const textBefore = text.slice(lastIndex, match.index).trim();
                if (textBefore) {
                    this.processTextSegment(textBefore, result);
                }

                // 提取代码语言和内容
                const lang = match[1] || 'plaintext';
                const codeContent = match[2].trim();
                if (codeContent) {
                    result.code.push({ language: lang, content: codeContent });
                }

                // 更新索引到代码块结束位置
                lastIndex = match.index + match[0].length;
                
                // 如果没有明确的结束标记，手动调整正则表达式的lastIndex
                if (!text.slice(lastIndex).includes('```')) {
                    break;
                }
            }

            // 处理剩余文本
            const remainingText = text.slice(lastIndex).trim();
            if (remainingText) {
                this.processTextSegment(remainingText, result);
            }

            // 如果没有找到任何内容，将整个内容作为文本
            if (Object.values(result).every(arr => arr.length === 0)) {
                result.text.push(text);
            }
        } catch (error) {
            console.error('解析消息失败:', error);
            result.text.push(String(content || ''));
        }

        return result;
    }

    /**
     * 处理文本段落，检测是否包含HTML
     * @param {string} text 文本内容
     * @param {Object} result 结果对象
     */
    processTextSegment(text, result) {
        if (!text || !text.trim()) return;
        
        // 安全检查：如果文本太长，简单处理
        if (text.length > 20000) {
            if (this.containsHtml(text)) {
                result.html.push(text);
            } else {
                result.text.push(text);
            }
            return;
        }
        
        // 尝试提取HTML块
        const htmlBlocks = this.extractHtmlBlocks(text);
        htmlBlocks.forEach(block => {
            if (block.type === 'html') {
                result.html.push(block.content);
            } else {
                result.text.push(block.content);
            }
        });
    }

    /**
     * 检查文本是否包含HTML标签
     * @param {string} text 文本内容
     * @returns {boolean} 是否包含HTML标签
     */
    containsHtml(text) {
        return /<\w+/.test(text); // 简化检测是否存在HTML标签
    }

    /**
     * 检查文本是否是完整的HTML结构
     * @param {string} text 文本内容
     * @returns {boolean} 是否是完整的HTML
     */
    isCompleteHtml(text) {
        try {
            const trimmed = text.trim();
            
            // 安全检查：如果文本太长，简化检测
            if (trimmed.length > 50000) {
                return trimmed.startsWith('<html') && trimmed.endsWith('</html>');
            }

            // 检查是否是完整的HTML文档
            if (/^<!DOCTYPE\s+html/i.test(trimmed) || 
                (trimmed.startsWith('<html') && trimmed.endsWith('</html>'))) {
                return true;
            }
            
            // 检查是否包含完整的<head>和<body>标签
            if (/<head[\s>]/i.test(trimmed) && /<\/head>/i.test(trimmed) && 
                /<body[\s>]/i.test(trimmed) && /<\/body>/i.test(trimmed)) {
                return true;
            }
            
            // 检查HTML标签数量
            const tagCount = (trimmed.match(/<\w+/g) || []).length;
            if (tagCount >= 5 && trimmed.length > 100) {
                // 如果有足够多的标签，可能是HTML
                return true;
            }
            
            // 检查是否包含完整的<div>结构且占据大部分内容
            if (trimmed.startsWith('<div') && trimmed.endsWith('</div>') && trimmed.length > 50) {
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('检查HTML结构时出错:', error);
            return false;
        }
    }

    /**
     * 从文本中提取HTML块和普通文本块
     * @param {string} text 文本内容
     * @returns {Array} 提取的块数组，每个元素包含type和content
     */
    extractHtmlBlocks(text) {
        try {
            // 安全检查：如果文本太长，简单处理
            if (text.length > 10000) {
                return [{
                    type: this.containsHtml(text) ? 'html' : 'text',
                    content: text
                }];
            }
            
            const blocks = [];
            // 使用更简单的正则表达式匹配HTML标签对
            const htmlRegex = /<\w+[^>]*>[\s\S]*?<\/\w+>/gi;
            let lastIndex = 0;
            let match;
            
            // 设置最大匹配次数，防止无限循环
            let matchCount = 0;
            const MAX_MATCHES = 100;

            while ((match = htmlRegex.exec(text)) !== null && matchCount < MAX_MATCHES) {
                matchCount++;
                
                // 添加HTML标签之前的文本
                if (match.index > lastIndex) {
                    const textBefore = text.slice(lastIndex, match.index).trim();
                    if (textBefore) {
                        blocks.push({
                            type: 'text',
                            content: textBefore
                        });
                    }
                }

                // 添加HTML块
                blocks.push({
                    type: 'html',
                    content: match[0]
                });

                lastIndex = match.index + match[0].length;
            }

            // 添加剩余的文本
            if (lastIndex < text.length) {
                const remainingText = text.slice(lastIndex).trim();
                if (remainingText) {
                    blocks.push({
                        type: 'text',
                        content: remainingText
                    });
                }
            }
            
            // 如果没有找到任何块，返回整个文本
            if (blocks.length === 0) {
                blocks.push({
                    type: 'text',
                    content: text
                });
            }

            return blocks;
        } catch (error) {
            console.error('提取HTML块时出错:', error);
            return [{
                type: 'text',
                content: text
            }];
        }
    }

    /**
     * HTML转义
     * @param {string} text 需要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 解析消息内容
     * @param {string} content 消息内容
     * @param {string} type 内容类型
     * @returns {string} 解析后的HTML
     */
    parseMessage(content, type = 'text') {
        if (type === 'html') {
            // 检查是否是 ComfyUI 工作流容器
            if (this.isComfyWorkflow(content)) {
                return this.wrapWorkflowContent(content);
            }
            
            // 检查是否是安全的 HTML
            if (this.isCleanHtml(content)) {
                return this.wrapHtmlContent(content);
            }

            return this.parseMarkdown(content);
        }
        return this.escapeHtml(content);
    }

    /**
     * 解析用户消息内容
     * @param {string} content 消息内容
     * @param {string} prompt_name 提示词名称
     * @param {Array} images 图片数组
     * @returns {string} 解析后的HTML
     */
    parseMessage_user(content, prompt_name, images = []) {
        let result = '';
        
        // 添加提示词标题
        if (prompt_name) {
            result += `<div class="prompt-name" style="background-color: #ffeb3b; color: #000; font-weight: bold; padding: 2px 8px; border-radius: 4px; display: inline-block;">#${prompt_name}</div>`;
        }

        // 创建单一的消息容器
        result += `<div class="user-message-content">`;
        result += this.escapeHtml(content);

        // 添加图片，不再有额外的背景色
        if (images && images.length > 0) {
            result += `<div class="message-images">`;
            images.forEach(image => {
                result += `<img src="${image}" alt="上传的图片" onclick="document.querySelector('.ai-chat-window').__vue__.showImageViewer('${image}')"/>`;
            });
            result += `</div>`;
        }

        result += `</div>`;
        return result;
    }

    /**
     * 检查是否是后端清理过的 HTML
     */
    isCleanHtml(content) {
        try {
            const trimmed = content.trim();
            // 检查是否是完整的 HTML 元素
            if (!/^<[a-z][\s\S]*>$/i.test(trimmed)) {
                return false;
            }

            // 创建临时 DOM 解析器
            const parser = new DOMParser();
            const doc = parser.parseFromString(content, 'text/html');
            
            // 检查是否有解析错误
            if (doc.querySelector('parsererror')) {
                return false;
            }

            return true;
        } catch (e) {
            console.error('HTML检查失败:', e);
            return false;
        }
    }

    /**
     * 包装 HTML 内容，添加必要的样式和行为
     */
    wrapHtmlContent(content) {
        // 包装在安全容器中
        const wrapped = `<div class="ai-safe-html">${content}</div>`;

        // 处理按钮点击事件
        setTimeout(() => {
            const buttons = document.querySelectorAll('.ai-safe-html button');
            buttons.forEach(button => {
                if (button.onclick) {
                    const originalClick = button.onclick;
                    button.onclick = async (e) => {
                        e.preventDefault();
                        try {
                            button.disabled = true;
                            button.textContent = '处理中...';
                            await originalClick.call(button, e);
                            button.textContent = '完成';
                        } catch (error) {
                            console.error('按钮操作失败:', error);
                            button.textContent = '失败';
                        } finally {
                            setTimeout(() => {
                                button.disabled = false;
                                button.textContent = '去水印';
                            }, 2000);
                        }
                    };
                }
            });
        }, 0);

        return wrapped;
    }

    /**
     * 解析 Markdown 格式
     */
    parseMarkdown(content) {
        // 处理代码块
        content = content.replace(/```([\w-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const langClass = lang ? `language-${lang}` : '';
            const langDisplay = lang || 'text';
            
            return `<div class="code-block">
                <div class="code-header">
                    <span class="code-lang">${langDisplay}</span>
                    <button class="copy-button" onclick="this.textContent='已复制';setTimeout(() => this.textContent='复制', 1500);navigator.clipboard.writeText(\`${code.trim()}\`)">复制</button>
                </div>
                <pre><code class="${langClass}">${this.escapeHtml(code.trim())}</code></pre>
            </div>`;
        });
        
        // 处理内联代码
        content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        // 处理标题 (### 语法)
        content = content.replace(/^(#{1,6})\s+(.+)$/gm, (match, hashes, text) => {
            const level = hashes.length;
            return `<h${level} class="md-heading">${text.trim()}</h${level}>`;
        });
        
        // 处理有序和无序列表
        content = content.replace(/(?:^|\n)((?:\d+\.|\-)\s+[^\n]+)/g, (match, item) => {
            const isOrdered = /^\d+\./.test(item);
            const listClass = isOrdered ? 'ordered' : 'unordered';
            const text = item.replace(/^(?:\d+\.|\-)\s+/, '');
            return `\n<li class="${listClass}">${text}</li>`;
        });
        
        // 处理段落
        content = content.split(/\n\n+/).map(para => {
            if (para.trim()) {
                if (!/^<[hl]/.test(para)) { // 不是标题或列表
                    return `<p>${para.trim()}</p>`;
                }
            }
            return para;
        }).join('\n');
        
        // 处理单行换行
        content = content.replace(/\n(?![<\s])/g, '<br>');
        
        return content;
    }

    /**
     * 检查是否是 ComfyUI 工作流内容
     */
    isComfyWorkflow(content) {
        return content.includes('class="comfyui-workflow-container"');
    }

    /**
     * 包装工作流内容并添加交互功能
     */
    wrapWorkflowContent(content) {
        // 包装在安全容器中
        const wrapped = `<div class="ai-workflow-wrapper">${content}</div>`;

        // 添加工作流交互功能
        setTimeout(() => {
            const containers = document.querySelectorAll('.comfyui-workflow-container');
            containers.forEach(container => {
                const runBtn = container.querySelector('.run-workflow-btn');
                const viewBtn = container.querySelector('.view-json-btn');
                const jsonViewer = container.querySelector('.json-viewer');
                const jsonContent = container.querySelector('.comfyui-workflow-json');

                if (runBtn) {
                    runBtn.onclick = async () => {
                        try {
                            runBtn.disabled = true;
                            runBtn.textContent = '运行中...';
                            
                            const workflow = JSON.parse(jsonContent.textContent);
                            const response = await fetch('http://127.0.0.1:8188/queue', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(workflow)
                            });
                            
                            if (!response.ok) throw new Error('运行失败');
                            
                            runBtn.textContent = '运行成功';
                        } catch (error) {
                            console.error('运行工作流失败:', error);
                            runBtn.textContent = '运行失败';
                        } finally {
                            setTimeout(() => {
                                runBtn.disabled = false;
                                runBtn.textContent = '运行工作流';
                            }, 2000);
                        }
                    };
                }

                if (viewBtn && jsonViewer) {
                    viewBtn.onclick = () => {
                        if (jsonViewer.classList.contains('hidden')) {
                            try {
                                const workflow = JSON.parse(jsonContent.textContent);
                                jsonViewer.textContent = JSON.stringify(workflow, null, 2);
                                jsonViewer.classList.remove('hidden');
                                viewBtn.textContent = '隐藏 JSON';
                            } catch (error) {
                                console.error('解析 JSON 失败:', error);
                            }
                        } else {
                            jsonViewer.classList.add('hidden');
                            viewBtn.textContent = '查看 JSON';
                        }
                    };
                }
            });
        }, 0);

        return wrapped;
    }

    copyCode(button) {
        const codeBlock = button.closest('.code-block');
        const code = codeBlock.querySelector('code').textContent;
        
        navigator.clipboard.writeText(code).then(() => {
            button.textContent = '已复制';
            setTimeout(() => {
                button.textContent = '复制';
            }, 1500);
        }).catch(err => {
            console.error('复制失败:', err);
            button.textContent = '复制失败';
            setTimeout(() => {
                button.textContent = '复制';
            }, 1500);
        });
    }
}

// 添加消息样式
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .ai-message-content {
        line-height: 1.6;
        font-size: 14px;
        color: #e0e0e0;
    }

    .ai-message-content .code-block {
        background: #1a1a2a;
        border-radius: 6px;
        margin: 12px 0;
        overflow: hidden;
    }

    .ai-message-content .code-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background: #2a2a3a;
        border-bottom: 1px solid #3a3a4a;
    }

    .ai-message-content .code-lang {
        color: #8a8a9a;
        font-size: 12px;
        font-family: monospace;
    }

    .ai-message-content .copy-button {
        background: #4a5a8a;
        border: none;
        border-radius: 4px;
        color: white;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        transition: background 0.2s;
    }

    .ai-message-content .copy-button:hover {
        background: #5a6a9a;
    }

    .ai-message-content pre {
        margin: 0;
        padding: 12px;
        overflow-x: auto;
    }

    .ai-message-content code {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
    }

    .ai-message-content .inline-code {
        background: rgba(255,255,255,0.1);
        padding: 2px 4px;
        border-radius: 3px;
        color: #e0e0e0;
    }

    .ai-message-content .md-heading {
        margin: 20px 0 10px;
        color: #ffffff;
        font-weight: 600;
    }

    .ai-message-content h1 { font-size: 24px; }
    .ai-message-content h2 { font-size: 20px; }
    .ai-message-content h3 { font-size: 18px; }
    .ai-message-content h4 { font-size: 16px; }

    .ai-message-content li {
        margin: 6px 0;
        padding-left: 12px;
        position: relative;
    }

    .ai-message-content li.unordered::before {
        content: "•";
        position: absolute;
        left: 0;
        color: #6a7a9a;
    }

    .ai-message-content p {
        margin: 12px 0;
    }

    .ai-html-element {
        margin: 12px 0;
    }

    .ai-html-element button {
        background: #4a5a8a;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        transition: background 0.2s;
    }

    .ai-html-element button:hover {
        background: #5a6a9a;
    }

    .ai-safe-html {
        margin: 12px 0;
    }

    .ai-safe-html button {
        background: #4a5a8a;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .ai-safe-html button:hover {
        background: #5a6a9a;
    }

    .ai-safe-html button:disabled {
        background: #3a4a6a;
        cursor: not-allowed;
        opacity: 0.7;
    }

    .ai-safe-html pre {
        background: #1a1a2a;
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        margin: 12px 0;
    }

    .ai-safe-html code {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
    }

    .ai-workflow-wrapper {
        margin: 12px 0;
    }

    .comfyui-workflow-container {
        background: #1a1a2a;
        border-radius: 8px;
        padding: 16px;
    }

    .comfyui-workflow-json {
        display: none;  /* 隐藏原始 JSON */
    }

    .comfyui-workflow-explanation {
        color: #e0e0e0;
        margin: 12px 0;
        line-height: 1.5;
    }

    .workflow-buttons {
        display: flex;
        gap: 8px;
        margin-top: 12px;
    }

    .workflow-buttons button {
        background: #4a5a8a;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .workflow-buttons button:hover {
        background: #5a6a9a;
    }

    .workflow-buttons button:disabled {
        background: #3a4a6a;
        cursor: not-allowed;
        opacity: 0.7;
    }

    .json-viewer {
        background: #0a0a1a;
        border-radius: 6px;
        padding: 12px;
        margin-top: 12px;
        max-height: 400px;
        overflow: auto;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        white-space: pre;
        color: #e0e0e0;
    }

    .json-viewer.hidden {
        display: none;
    }

    .prompt-name {
        color: #6a7a9a;
        font-size: 12px;
        margin-bottom: 4px;
        font-family: monospace;
    }

    .text-content {
        background-color: #1e1e2e;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 8px;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .user-message-content {
        padding: 10px;
        border-radius: 4px;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .message-images {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }

    .message-images img {
        max-width: 200px;
        max-height: 200px;
        border-radius: 4px;
        cursor: pointer;
        object-fit: contain;
        transition: transform 0.2s;
    }

    .message-images img:hover {
        transform: scale(1.05);
    }
`;

document.head.appendChild(styleSheet);

export default new MessageParser(); 