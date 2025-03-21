/**
 * ComfyUI AI Assistant 基础服务类
 */
import AiCircleButton from './components/ai_CircleButton.js';
import AiAssistantWindow from './components/ai_AssistantWindow.js';
import AiSettingsWindow from './components/ai_SettingsWindow.js';
import AiWorkflowWindow from './components/ai_WorkflowWindow.js';
import AiChatWindow from './components/ai_ChatWindow.js';
import AiDialog from './components/ai_Dialog.js';
import aiService from './services/ai_Service.js';

class AiUi {
    constructor() {
        // 使用完整的API路径
        this.aiCircleButton = null;
        this.aiAssistantWindow = null;
        this.aiSettingsWindow = null;
        this.aiWorkflowWindow = null;
        this.aiChatWindow = null;
        this.aiService = aiService;
        this.old_window_id = null;
    }

    async loadui() {
        this.aiCircleButton = new AiCircleButton();
        this.aiAssistantWindow = new AiAssistantWindow();
        await this.aiAssistantWindow.initialized; // 等待初始化完成
        this.aiCircleButton.setbutton_click();
        
        // 初始化工作流窗口
        const workflowContainer = this.aiAssistantWindow.getWindowContainer('workflow');
        this.aiWorkflowWindow = new AiWorkflowWindow(workflowContainer);
        await this.aiWorkflowWindow.initialized; // 等待初始化完成
        
        // 初始化设置窗口
        const settingsContainer = this.aiAssistantWindow.getWindowContainer('settings');
        this.aiSettingsWindow = new AiSettingsWindow(settingsContainer);
        await this.aiSettingsWindow.initialized; // 等待初始化完成

        // 初始化聊天窗口
        const chatContainer = this.aiAssistantWindow.getWindowContainer('chat');
        this.aiChatWindow = new AiChatWindow(chatContainer);
        await this.aiChatWindow.initialized; // 等待初始化完成

        // 默认显示聊天窗口
        this.show_hide('chat');
    }

    resize(type_id) {
        console.log("resize", type_id);
        if (type_id == 'workflow') {
            this.aiWorkflowWindow.handleResize();
        }
        else if (type_id == 'chat') {
            if (this.aiChatWindow) {
                this.aiChatWindow.handleResize();
            }
        }
        else if (type_id == 'settings') {
            if (this.aiSettingsWindow) {
                this.aiSettingsWindow.handleResize();
            }
        }
    }

    show_hide(type_id) {
        // 如果从设置页面切换且有未保存的更改
        const hasUnsavedChanges = (settingsWindow) => {
            try {
              // 使用原生JavaScript深度比较对象，替代lodash的isEqual
              const isEqual = (obj1, obj2) => {
                // 检查基本类型或null/undefined
                if (obj1 === obj2) return true;
                
                // 检查一个是对象而另一个不是
                if (typeof obj1 !== 'object' || typeof obj2 !== 'object') return false;
                if (obj1 === null || obj2 === null) return false;
                
                // 检查类型不同
                const obj1Keys = Object.keys(obj1);
                const obj2Keys = Object.keys(obj2);
                
                if (obj1Keys.length !== obj2Keys.length) return false;
                
                // 递归检查所有属性
                return obj1Keys.every(key => {
                  return obj2.hasOwnProperty(key) && isEqual(obj1[key], obj2[key]);
                });
              };
              
              // 比较两个配置对象
              return !isEqual(
                settingsWindow.getConfig_value().ai_params,
                settingsWindow.old_config.ai_params
              );
            } catch (e) {
              console.error('Config compare error:', e);
              return true; // 出错时保守认为有修改
            }
          };
          
        // 修改后的条件判断
        if (
            this.old_window_id == "settings" &&
            this.old_window_id != type_id &&
            !this.aiSettingsWindow.issave &&
            hasUnsavedChanges(this.aiSettingsWindow)
          ) {
            // 显示确认对话框并等待用户选择
            AiDialog.show('是否保存当前配置？', 
                () => {
                    // 点击确定时保存配置
                    if (this.aiSettingsWindow) {
                        this.aiSettingsWindow.handleSave();
                    }
                    // 保存后再执行窗口切换
                    this.switchWindow(type_id);
                },
                () => {
                    // 点击取消时直接切换窗口
                    this.switchWindow(type_id);
                }
            );
        } else {
            // 没有未保存的更改，直接切换窗口
            this.switchWindow(type_id);
        }
    }

    // 抽取窗口切换逻辑到单独的方法
    switchWindow(type_id) {
        this.old_window_id = type_id;
        // 隐藏所有窗口
        if (this.aiWorkflowWindow) {
            this.aiWorkflowWindow.show_hide(false);
        }
        if (this.aiSettingsWindow) {
            this.aiSettingsWindow.show_hide(false);
        }
        if (this.aiChatWindow) {
            this.aiChatWindow.show_hide(false);
        }
        
        // 显示当前选中的窗口
        switch(type_id) {
            case 'workflow':
                if (this.aiWorkflowWindow) {
                    this.aiWorkflowWindow.show_hide(true);
                }
                break;
            case 'settings':
                if (this.aiSettingsWindow) {
                    this.aiSettingsWindow.show_hide(true);
                }
                break;
            case 'chat':
                if (this.aiChatWindow) {
                    this.aiChatWindow.loadHistory();
                    this.aiChatWindow.show_hide(true);
                }
                break;
        }
    }
}

// 导出服务实例
export default new AiUi(); 