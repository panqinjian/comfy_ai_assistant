/**
 * 可移动的悬浮按钮组件
 */
import AiUi from '../ai_ui.js';

class AiCircleButton {
    constructor() {
        this.button = null;
        // 等待 DOM 加载完成后再初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        // 创建按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'ai-assistant-floating-button';
        buttonContainer.style.cssText = `
            position: fixed;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 1000;
            cursor: move;
            user-select: none;
        `;

        // 创建按钮元素
        const button = document.createElement('button');
        button.className = 'p-button p-component p-button-icon-only p-button-rounded p-button-text';
        button.setAttribute('type', 'button');
        button.setAttribute('aria-label', 'AI 助手');
        button.setAttribute('data-pd-tooltip', 'true');

        // 创建图标
        const icon = document.createElement('i');
        icon.className = 'pi pi-comments';

        // 创建标签
        const label = document.createElement('span');
        label.className = 'p-button-label';
        label.innerHTML = '&nbsp;';

        // 组装按钮
        button.appendChild(icon);
        button.appendChild(label);
        buttonContainer.appendChild(button);

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .ai-assistant-floating-button {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 50%;
                padding: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            .ai-assistant-floating-button:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: translateY(-50%) scale(1.1);
            }
            .ai-assistant-floating-button button {
                width: 40px;
                height: 40px;
                border: none;
                background: transparent;
                color: var(--text-color);
                cursor: pointer;
            }
            .ai-assistant-floating-button button:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            .ai-assistant-floating-button i {
                font-size: 1.5rem;
            }
        `;

        // 将样式和按钮添加到文档中
        document.head.appendChild(style);
        document.body.appendChild(buttonContainer);

        // 添加拖拽功能
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;

        buttonContainer.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        function dragStart(e) {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;

            if (e.target === buttonContainer || e.target === button || e.target === icon) {
                isDragging = true;
            }
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                xOffset = currentX;
                yOffset = currentY;

                setTranslate(currentX, currentY, buttonContainer);
            }
        }

        function setTranslate(xPos, yPos, el) {
            el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
        }

        function dragEnd() {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }

        this.button = button;
    }

    setbutton_click(){
        try {
            // 添加点击事件
            this.aiUi =AiUi;
            this.button.addEventListener('click', () => {
                this.aiUi.aiAssistantWindow.toggle();
            });
        } catch (error) {
            console.error('加载AI助手窗口失败:', error);
        }
    }

}

export default AiCircleButton; 