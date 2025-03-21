/**
 * ComfyUI AI 助手扩展
 * 模块化入口文件
 * 
 * 本文件替代了原有的 comfy_ai_assistant.js
 * 采用模块化架构，提高了代码的可维护性和扩展性
 */


import aiService from './services/ai_Service.js';
import aiUi from './ai_ui.js';


// 记录加载时间

const startTime = Date.now();
console.log('ComfyUI AI Assistant 模块化版本: 开始加载...');

class AiAssistant {
    constructor() {
        this.init();
    }

    async init() {
        try {
            // 获取配置
            this.aiService =aiService;
            this.aiService.getConfig(true);
            console.log('配置加载成功:', this.aiService.config);

            this.aiUi =aiUi;
            this.aiUi.loadui();
            console.log(`ComfyUI AI Assistant 模块化版本: 加载完成，耗时 ${Date.now() - startTime}ms`);
        } catch (error) {
            console.error('初始化失败:', error);
            if (error.stack) {
                console.error('错误堆栈:', error.stack);
            }
        }
    }
}

// 自动初始化应用程序
document.addEventListener('DOMContentLoaded', AiAssistant);

// 如果DOM已经加载，立即初始化
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    new AiAssistant();
} 

// 导出应用实例供 ComfyUI 使用
export { AiAssistant as app }; 