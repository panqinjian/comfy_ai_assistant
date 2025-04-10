/**
 * 系统提示词选择器组件
 * 当用户在输入框中输入 # 时显示提示词列表
 */
import aiService from '../services/ai_Service.js';

class AiPromptSelector {
    constructor(inputElement, onSelect) {
        this.inputElement = inputElement;
        this.onSelect = onSelect;
        this.container = null;
        this.prompts = [];
        this.isVisible = false;
        this.selectedIndex = -1;
        
        this.init();
    }
    
    /**
     * 初始化选择器
     */
    init() {
        // 创建提示词选择器容器
        this.container = document.createElement('div');
        this.container.className = 'ai-prompt-selector';
        this.container.style.cssText = `
            position: absolute;
            bottom: 100%;
            left: 0;
            width: 100%;
            max-height: 200px;
            overflow-y: auto;
            background-color: #2a2a3a;
            border: 1px solid #3a3a4a;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            display: none;
        `;
        
        // 将容器添加到输入框旁边
        const inputParent = this.inputElement.parentNode;
        inputParent.style.position = 'relative'; // 确保父元素是相对定位的
        inputParent.appendChild(this.container);
        
        // 加载提示词
        this.loadPrompts();
        
        // 监听输入事件
        this.inputElement.addEventListener('input', (e) => this.handleInput(e));
        this.inputElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // 点击其他地方关闭选择器
        document.addEventListener('click', (e) => {
            if (e.target !== this.container && e.target !== this.inputElement && !this.container.contains(e.target)) {
                this.hide();
            }
        });
        
        // 添加调试日志
        console.log('提示词选择器已初始化');
    }
    
    /**
     * 加载系统提示词
     */
    async loadPrompts() {
        try {
            const result = await aiService.getPrompts();
            this.prompts = result.prompts;
            console.log('已加载提示词:', this.prompts);
        } catch (error) {
            console.error('加载提示词失败:', error);
        }
    }
    
    /**
     * 处理输入事件
     */
    handleInput(e) {
        const text = this.inputElement.value;
        const lastChar = text.charAt(text.length - 1);
        
        if (lastChar === '#') {
            // 显示提示词选择器
            console.log('检测到 # 字符，显示提示词选择器');
            this.show();
        } else if (!text.includes('#')) {
            // 如果输入框中没有 #，隐藏选择器
            this.hide();
        }
    }
    
    /**
     * 处理键盘事件
     */
    handleKeyDown(e) {
        if (!this.isVisible) return;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                this.selectCurrent();
                break;
            case 'Escape':
                e.preventDefault();
                this.hide();
                break;
        }
    }
    
    /**
     * 显示提示词选择器
     */
    show() {
        if (this.isVisible) return;
        
        console.log('显示提示词选择器');
        
        // 清空容器
        this.container.innerHTML = '';
        
        // 如果没有提示词，显示提示信息
        if (!this.prompts || this.prompts.length === 0) {
            const noPrompts = document.createElement('div');
            noPrompts.className = 'ai-prompt-item';
            noPrompts.textContent = '没有可用的提示词';
            noPrompts.style.cssText = `
                padding: 8px 12px;
                cursor: default;
                color: #999;
            `;
            this.container.appendChild(noPrompts);
        } else {
            // 添加提示词列表
            this.prompts.forEach((prompt, index) => {
                const item = document.createElement('div');
                item.className = 'ai-prompt-item';
                item.textContent = prompt.prompt_name;
                item.style.cssText = `
                    padding: 8px 12px;
                    cursor: pointer;
                    border-bottom: 1px solid #3a3a4a;
                    transition: background-color 0.2s;
                `;
                
                item.addEventListener('mouseover', () => {
                    this.selectedIndex = index;
                    this.highlightSelected();
                });
                
                item.addEventListener('click', () => {
                    this.selectPrompt(prompt);
                });
                
                this.container.appendChild(item);
            });
        }
        
        // 显示容器
        this.container.style.display = 'block';
        this.isVisible = true;
        
        // 重置选中索引
        this.selectedIndex = -1;
    }
    
    /**
     * 隐藏提示词选择器
     */
    hide() {
        if (!this.isVisible) return;
        
        console.log('隐藏提示词选择器');
        
        this.container.style.display = 'none';
        this.isVisible = false;
    }
    
    /**
     * 渲染提示词列表
     */
    renderPrompts() {
        this.container.innerHTML = '';
        
        if (this.prompts.length === 0) {
            const item = document.createElement('div');
            item.className = 'ai-prompt-item';
            item.textContent = '没有可用的提示词';
            item.style.padding = '8px 12px';
            item.style.cursor = 'default';
            this.container.appendChild(item);
            return;
        }
        
        this.prompts.forEach((prompt, index) => {
            const item = document.createElement('div');
            item.className = 'ai-prompt-item';
            item.textContent = prompt.prompt_name;
            item.dataset.id = prompt.prompt_id;
            item.style.padding = '8px 12px';
            item.style.cursor = 'pointer';
            item.style.borderBottom = '1px solid var(--ai-border-color)';
            
            item.addEventListener('click', () => {
                this.selectPrompt(prompt);
            });
            
            item.addEventListener('mouseover', () => {
                this.selectedIndex = index;
                this.highlightSelected();
            });
            
            this.container.appendChild(item);
        });
    }
    
    /**
     * 选择下一个提示词
     */
    selectNext() {
        if (this.selectedIndex < this.prompts.length - 1) {
            this.selectedIndex++;
            this.highlightSelected();
        }
    }
    
    /**
     * 选择上一个提示词
     */
    selectPrevious() {
        if (this.selectedIndex > 0) {
            this.selectedIndex--;
            this.highlightSelected();
        }
    }
    
    /**
     * 选择当前提示词
     */
    selectCurrent() {
        if (this.selectedIndex >= 0 && this.selectedIndex < this.prompts.length) {
            this.selectPrompt(this.prompts[this.selectedIndex]);
        }
    }
    
    /**
     * 高亮显示选中的提示词
     */
    highlightSelected() {
        const items = this.container.querySelectorAll('.ai-prompt-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.style.backgroundColor = 'var(--ai-primary-color)';
                item.style.color = 'white';
            } else {
                item.style.backgroundColor = '';
                item.style.color = '';
            }
        });
    }
    
    /**
     * 选择提示词
     */
    selectPrompt(prompt) {
        
        // 触发选择回调
        if (this.onSelect) {
            this.onSelect(prompt);
        }
        
        this.hide();
    }

    
    
}

export default AiPromptSelector; 