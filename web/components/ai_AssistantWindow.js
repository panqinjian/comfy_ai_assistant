/**
 * AI助手窗口组件
 */
import AiUi from '../ai_ui.js';

class AiAssistantWindow {
    constructor() {
        this.menuItems = null;
        this.visible = false;
        this.currentMenu = 'chat';
        this.aiUi = AiUi;
        this.windowContainers = {}; // 存储不同菜单对应的窗口容器
        this.minWidth = 500; // 最小宽度
        this.minHeight = 400; // 最小高度
        this.initialized = this.init();
    }

    init() {
        // 创建主窗口容器
        this.container = document.createElement('div');
        this.container.className = 'ai-assistant-container';
        this.container.style.cssText = `
            position: fixed;
            display: none;
            width: 800px;
            height: 600px;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: #1e1e2e;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            z-index: 9999;
            overflow: hidden;
            flex-direction: column;
            border: 1px solid #2a2a3a;
        `;

        // 创建标题栏
        const titleBar = document.createElement('div');
        titleBar.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background-color: #2a2a3a;
            cursor: move;
            user-select: none;
            height: 40px;
            border-bottom: 1px solid #3a3a4a;
        `;

        // 创建标题文本
        const titleText = document.createElement('div');
        titleText.style.cssText = `
            color: #ffffff;
            font-weight: bold;
            flex: 1;
        `;
        titleText.textContent = 'AI 助手';

        // 创建控制按钮区域
        const controls = document.createElement('div');
        controls.style.cssText = `
            display: flex;
            align-items: center;
        `;

        // 创建关闭按钮
        const closeButton = document.createElement('button');
        closeButton.style.cssText = `
            background: none;
            border: none;
            color: #ffffff;
            font-size: 20px;
            cursor: pointer;
            padding: 0 8px;
            line-height: 1;
            transition: color 0.3s;
        `;
        closeButton.innerHTML = '×';
        closeButton.addEventListener('mouseover', () => {
            closeButton.style.color = '#ff5555';
        });
        closeButton.addEventListener('mouseout', () => {
            closeButton.style.color = '#ffffff';
        });

        // 组装标题栏
        controls.appendChild(closeButton);
        titleBar.appendChild(titleText);
        titleBar.appendChild(controls);

        // 创建主内容区域
        const mainContent = document.createElement('div');
        mainContent.style.cssText = `
            display: flex;
            height: calc(100% - 40px);
            overflow: hidden;
            background-color: #1e1e2e;
        `;

        // 创建左侧菜单
        const menu = document.createElement('div');
        menu.style.cssText = `
            width: 48px;
            background: #2a2a3a;
            border-right: 1px solid #3a3a4a;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 10px 0;
            gap: 10px;
        `;

        // 创建菜单项
        const menuItems = [
            { id: 'chat', icon: '💬', tooltip: '聊天', color: '#2a3f5f' },
            { id: 'workflow', icon: '📋', tooltip: '工作流', color: '#2a5f3f' },
            { id: 'settings', icon: '⚙️', tooltip: '设置', color: '#5f2a3f' }
        ];

        menuItems.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.style.cssText = `
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                border-radius: 4px;
                transition: background 0.3s;
                ${this.currentMenu === item.id ? 'background: #3a3a4a;' : ''}
            `;
            menuItem.dataset.menu = item.id;
            menuItem.innerHTML = item.icon;
            menuItem.title = item.tooltip;

            menuItem.addEventListener('mouseover', () => {
                if (this.currentMenu !== item.id) {
                    menuItem.style.background = '#3a3a4a';
                }
            });

            menuItem.addEventListener('mouseout', () => {
                if (this.currentMenu !== item.id) {
                    menuItem.style.background = 'none';
                }
            });

            menuItem.addEventListener('click', () => this.switchMenu(item.id));
            menu.appendChild(menuItem);
        });

        // 添加一个分隔线
        const separator = document.createElement('div');
        separator.style.cssText = `
            width: 32px;
            height: 1px;
            background: #3a3a4a;
            margin: auto 0 10px 0;
        `;
        menu.appendChild(separator);

        // 添加清除历史记录按钮
        const clearButton = document.createElement('div');
        clearButton.style.cssText = `
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s;
            margin-bottom: 10px;
            color: #ff5555;
        `;
        clearButton.innerHTML = '🗑️';
        clearButton.title = '清除聊天记录';

        clearButton.addEventListener('mouseover', () => {
            clearButton.style.background = '#3a3a4a';
            clearButton.style.transform = 'scale(1.1)';
        });

        clearButton.addEventListener('mouseout', () => {
            clearButton.style.background = 'none';
            clearButton.style.transform = 'scale(1)';
        });

        clearButton.addEventListener('click', async () => {
            if (this.aiUi && this.aiUi.aiChatWindow) {
                try {
                    // 发送清除历史记录的请求
                    const response = await fetch('/comfy_ai_assistant/clear_history', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            service: this.aiUi.aiService.service
                        })
                    });

                    if (!response.ok) {
                        throw new Error('清除历史记录失败');
                    }

                    // 重新加载聊天窗口
                    await this.aiUi.aiChatWindow.loadHistory();
                } catch (error) {
                    console.error('清除历史记录失败:', error);
                }
            }
        });

        menu.appendChild(clearButton);

        this.menuItems = menuItems;

        // 创建右侧内容区域
        const contentArea = document.createElement('div');
        contentArea.style.cssText = `
            flex: 1;
            overflow: hidden;
            position: relative;
            background: #1e1e2e;
        `;

        // 创建三个窗口容器
        menuItems.forEach(item => {
            const container = document.createElement('div');
            container.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: ${item.id === this.currentMenu ? 'block' : 'none'};
                overflow: auto;
                background-color: #1e1e2e;
                box-sizing: border-box;
            `;

            // 添加测试文本
            const testText = document.createElement('div');
            testText.style.cssText = `
                color: #ffffff;
                font-size: 16px;
                margin: 10px;
            `;
            testText.textContent = `${item.tooltip} 窗口`;
            container.appendChild(testText);

            this.windowContainers[item.id] = container;
            contentArea.appendChild(container);
        });

        // 创建调整大小的手柄
        const resizeHandle = document.createElement('div');
        resizeHandle.style.cssText = `
            position: absolute;
            right: 0;
            bottom: 0;
            width: 15px;
            height: 15px;
            cursor: nw-resize;
            z-index: 10000;
        `;

        // 添加一个视觉指示器
        const resizeIndicator = document.createElement('div');
        resizeIndicator.style.cssText = `
            position: absolute;
            right: 4px;
            bottom: 4px;
            width: 6px;
            height: 6px;
            border-right: 2px solid #3a3a4a;
            border-bottom: 2px solid #3a3a4a;
            opacity: 0.7;
            transition: opacity 0.3s;
        `;

        resizeHandle.appendChild(resizeIndicator);
        resizeHandle.addEventListener('mouseover', () => {
            resizeIndicator.style.opacity = '1';
        });
        resizeHandle.addEventListener('mouseout', () => {
            resizeIndicator.style.opacity = '0.7';
        });

        // 设置调整大小的功能
        this.setupResizable(resizeHandle);

        // 组装组件
        mainContent.appendChild(menu);
        mainContent.appendChild(contentArea);
        this.container.appendChild(titleBar);
        this.container.appendChild(mainContent);
        this.container.appendChild(resizeHandle);

        // 添加到文档
        document.body.appendChild(this.container);

        // 保存引用
        this.contentArea = contentArea;
        this.menu = menu;
        this.titleBar = titleBar;
        this.resizeHandle = resizeHandle;

        // 添加事件监听
        closeButton.addEventListener('click', () => this.hide());
        this.setupDraggable(titleBar);
        
        // 设置为全局变量，方便其他组件访问
        window.aiAssistantWindow = this;
    }

    setupDraggable(element) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        let isDragging = false;
        let isFirstDrag = true;

        element.onmousedown = dragMouseDown;

        function dragMouseDown(e) {
            e.preventDefault();
            isDragging = true;
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        const container = this.container;
        function elementDrag(e) {
            if (!isDragging) return;
            e.preventDefault();

            // 如果是第一次拖动，需要转换定位方式
            if (isFirstDrag) {
                isFirstDrag = false;
                // 获取当前实际位置
                const rect = container.getBoundingClientRect();
                // 移除 transform，设置为实际位置
                container.style.transform = 'none';
                container.style.top = rect.top + 'px';
                container.style.left = rect.left + 'px';
                // 更新初始位置
                pos3 = e.clientX;
                pos4 = e.clientY;
                return;
            }

            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;

            container.style.top = (container.offsetTop - pos2) + "px";
            container.style.left = (container.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            isDragging = false;
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    setupResizable(element) {
        let isResizing = false;
        let originalWidth;
        let originalHeight;
        let originalX;
        let originalY;

        element.addEventListener('mousedown', initResize);

        const container = this.container;

        function initResize(e) {
            e.preventDefault();
            isResizing = true;

            // 记录初始尺寸和位置
            originalWidth = container.offsetWidth;
            originalHeight = container.offsetHeight;
            originalX = e.clientX;
            originalY = e.clientY;

            // 添加事件监听
            document.addEventListener('mousemove', resize);
            document.addEventListener('mouseup', stopResize);
        }

        const minWidth = this.minWidth;
        const minHeight = this.minHeight;

        const resize = (e) => {
            if (!isResizing) return;

            // 计算新的尺寸
            const newWidth = Math.max(originalWidth + (e.clientX - originalX), minWidth);
            const newHeight = Math.max(originalHeight + (e.clientY - originalY), minHeight);

            // 应用新尺寸
            container.style.width = newWidth + 'px';
            container.style.height = newHeight + 'px';

            // 通知外部组件大小已改变
            if (this.aiUi && typeof this.aiUi.resize === 'function') {
                this.aiUi.resize(this.currentMenu);
            }
        };

        const stopResize = () => {
            isResizing = false;
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        };
    }

    switchMenu(menuId) {
        // 检查菜单ID是否有效
        if (!menuId || !this.windowContainers[menuId]) {
            console.warn(`无效的菜单ID: ${menuId}`);
            return;
        }
        
        // 更新当前菜单
        this.currentMenu = menuId;
        
        // 更新菜单项样式
        const menuItems = this.menu.children;
        Array.from(menuItems).forEach(item => {
            if (item.dataset.menu === menuId) {
                item.style.background = '#3a3a4a';
            } else {
                item.style.background = 'none';
            }
        });
        
        // 切换窗口显示
        Object.entries(this.windowContainers).forEach(([id, container]) => {
            container.style.display = id === menuId ? 'block' : 'none';
        });
        
        // 保存当前菜单到本地存储
        localStorage.setItem('ai-assistant-current-menu', menuId);

        // 通知外部组件菜单已切换
        if (this.aiUi && typeof this.aiUi.show_hide === 'function') {
            this.aiUi.show_hide(menuId);
        }
    }

    show() {
        this.visible = true;
        this.container.style.display = 'flex';
        // 重置拖动状态
        this.container.style.transform = 'translate(-50%, -50%)';
        this.container.style.top = '50%';
        this.container.style.left = '50%';
        // 通知外部组件窗口显示
        if (this.aiUi && typeof this.aiUi.show_hide === 'function') {
            this.aiUi.show_hide(this.currentMenu);
        }
    }

    hide() {
        this.visible = false;
        this.container.style.display = 'none';
    }

    toggle() {
        if (this.visible) {
            this.hide();
        } else {
            this.show();
        }
    }

    // 获取指定菜单的窗口容器
    getWindowContainer(menuId) {
        return this.windowContainers[menuId];
    }
}

export default AiAssistantWindow;