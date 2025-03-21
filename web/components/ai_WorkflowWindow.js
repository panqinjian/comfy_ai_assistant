/**
 * AI助手工作流窗口组件
 */
import AiUi from '../ai_ui.js';

class AiWorkflowWindow {
    constructor(container) {
        this.aiUi = AiUi;
        this.container = container;
        this.element = document.createElement('div');
        this.element.className = 'ai-workflow-window';
        this.parentContainer = null;
        this.visible = false;
        this.initialized = this.init();
    }

    async init() {
        // 获取父容器
        this.parentContainer = this.aiUi.aiAssistantWindow.getWindowContainer('workflow');
        if (!this.parentContainer) {
            console.error('找不到工作流窗口的父容器');
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
            align-items: center;
            justify-content: center;
            color: #ffffff;
            box-sizing: border-box;
            background-color: #1e1e2e;
            overflow: hidden;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // 创建内容容器（用于控制滚动）
        const contentContainer = document.createElement('div');
        contentContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow-y: auto;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-sizing: border-box;
            background-color: #1e1e2e;
        `;
        
        // 创建内容
        const message = document.createElement('div');
        message.className = 'ai-workflow-message';
        message.style.cssText = `
            font-size: 18px;
            margin-bottom: 20px;
            text-align: center;
        `;
        message.textContent = '工作流功能正在开发中...';
        
        // 创建一个尺寸显示器（用于测试窗口大小变化）
        this.sizeDisplay = document.createElement('div');
        this.sizeDisplay.style.cssText = `
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 10px;
        `;
        this.updateSizeDisplay();

        // 组装组件
        contentContainer.appendChild(message);
        contentContainer.appendChild(this.sizeDisplay);
        this.element.appendChild(contentContainer);
        
        // 添加到父容器
        this.parentContainer.innerHTML = ''; // 清除原有内容
        this.parentContainer.appendChild(this.element);
        this.hide();
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
            this.handleResize(); // 更新尺寸显示
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

    // 更新尺寸显示
    updateSizeDisplay() {
        if (this.sizeDisplay && this.parentContainer) {
            const width = this.parentContainer.offsetWidth;
            const height = this.parentContainer.offsetHeight;
            this.sizeDisplay.textContent = `窗口尺寸: ${width}px × ${height}px`;
        }
    }

    // 处理窗口大小变化
    handleResize() {
        if (this.visible) {
            this.updateSizeDisplay();
        }
    }
}

export default AiWorkflowWindow;
