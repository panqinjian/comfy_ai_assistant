/**
 * AI助手设置窗口组件
 */
import AiUi from '../ai_ui.js';
import aiService from '../services/ai_Service.js';

class AiSettingsWindow {
    constructor() {
        this.aiUi = AiUi;
        this.aiService = aiService;
        this.element = document.createElement('div');
        this.element.className = 'ai-settings-window';
        this.parentContainer = null;
        this.visible = false;
        this.config = null;
        this.old_config = null;
        this.issave = false;
        this.modelList = [];
        // 添加参数中文映射作为类属性
        this.paramLabels = {
            'model': '模型',
            'temperature': '温度',
            'max_tokens': '最大生成长度',
            'timeout': '超时时间(秒)',
            'proxy': '代理地址',
            'api_key': 'API密钥',
            'api_base': 'API地址',
            'api_type': 'API类型',
            'api_version': 'API版本'
        };
        this.initialized = this.init();
    }

    async init() {
        // 获取父容器
        this.parentContainer = this.aiUi.aiAssistantWindow.getWindowContainer('settings');
        if (!this.parentContainer) {
            console.error('找不到设置窗口的父容器');
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
            padding: 20px;
            box-sizing: border-box;
        `;

        // 创建服务选择区域
        const serviceSection = document.createElement('div');
        serviceSection.className = 'ai-settings-section';
        serviceSection.style.cssText = `
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        `;

        // 创建服务选择标签和下拉框容器
        const serviceSelectContainer = document.createElement('div');
        serviceSelectContainer.style.cssText = `
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        `;

        // 创建服务选择标签
        const serviceLabel = document.createElement('label');
        serviceLabel.textContent = 'AI 服务商';
        serviceLabel.className = 'ai-settings-label';
        serviceLabel.style.cssText = `
            color: #ffffff;
            white-space: nowrap;
        `;

        // 创建服务选择下拉框
        const serviceSelect = document.createElement('select');
        serviceSelect.className = 'ai-settings-select';
        serviceSelect.style.cssText = `
            width: 200px;
            padding: 8px;
            background: #2a2a3a;
            border: 1px solid #3a3a4a;
            border-radius: 4px;
            color: #ffffff;
        `;

        // 创建参数配置区域
        const paramsForm = document.createElement('div');
        paramsForm.className = 'ai-settings-form';

        // 创建按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'ai-settings-buttons';
        buttonContainer.style.cssText = `
            display: flex;
            gap: 10px;
        `;

        // 创建保存按钮
        const saveButton = document.createElement('button');
        saveButton.textContent = '保存';
        saveButton.className = 'ai-settings-button ai-settings-save';
        saveButton.style.cssText = `
            padding: 8px 16px;
            background: #2a5298;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        `;

        // 创建取消按钮
        const cancelButton = document.createElement('button');
        cancelButton.textContent = '取消';
        cancelButton.className = 'ai-settings-button ai-settings-cancel';
        cancelButton.style.cssText = `
            padding: 8px 16px;
            background: #2a2a3a;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        `;

        // 组装组件
        serviceSelectContainer.appendChild(serviceLabel);
        serviceSelectContainer.appendChild(serviceSelect);
        buttonContainer.appendChild(cancelButton);
        buttonContainer.appendChild(saveButton);
        serviceSection.appendChild(serviceSelectContainer);
        serviceSection.appendChild(buttonContainer);
        contentContainer.appendChild(serviceSection);
        contentContainer.appendChild(paramsForm);
        this.element.appendChild(contentContainer);

        // 保存引用
        this.serviceSelect = serviceSelect;
        this.paramsForm = paramsForm;
        this.saveButton = saveButton;
        this.cancelButton = cancelButton;

        // 添加事件监听
        serviceSelect.addEventListener('change', () => this.handleServiceChange());
        saveButton.addEventListener('click', () => this.handleSave());
        cancelButton.addEventListener('click', () => this.handleCancel());

        // 添加到父容器
        this.parentContainer.innerHTML = ''; // 清除原有内容
        this.parentContainer.appendChild(this.element);

 
        this.hide();
    }

    // 加载配置
    async loadConfig() {
        try {
            // 获取配置
            this.config = await this.aiService.config;
            
            // 更新服务选择下拉框
            this.updateServiceSelect();
            
            // 更新参数表单
            this.updateParamsForm();
            
            // 加载模型列表
            await this.loadModelList();

            if(this.old_config==null){
                this.old_config = this.config;
                this.old_config.ai_params = this.getConfig_value().ai_params;
            }
        } catch (error) {
            console.error('加载配置失败:', error);
            this.showError('加载配置失败: ' + error.message);
        }
    }

    // 更新服务选择下拉框
    updateServiceSelect() {
        if (!this.config || !this.config.service_list) return;

        this.serviceSelect.innerHTML = '';
        this.config.service_list.forEach((service, index) => {
            const option = document.createElement('option');
            option.value = this.config.service_ID_list[index];
            option.textContent = service;
            option.selected = this.config.service_ID_list[index] === this.config.service;
            this.serviceSelect.appendChild(option);
        });
    }

    // 更新参数表单
    updateParamsForm() {
        if (!this.config || !this.config.ai_params) return;

        this.paramsForm.innerHTML = '';
        const params = this.config.ai_params;

        // 定义参数顺序
        const paramOrder = [
            'model',
            'temperature',
            'max_tokens',
            'timeout',
            'proxy',
            'api_key',
            'api_base',
            'api_type',
            'api_version'
        ];

        // 按顺序创建表单项
        paramOrder.forEach(key => {
            if (!params.hasOwnProperty(key)) return;
            const value = params[key];

            const formGroup = document.createElement('div');
            formGroup.className = 'ai-settings-form-group';
            formGroup.style.marginBottom = '15px';

            const label = document.createElement('label');
            label.textContent = this.paramLabels[key] || key;
            label.style.cssText = `
                display: block;
                margin-bottom: 5px;
                color: #ffffff;
            `;

            let input;
            if (key === 'model' && this.modelList.length > 0) {
                input = document.createElement('select');
                let modelFound = false;
                
                this.modelList.forEach((model, index) => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name || model.id;
                    
                    // 检查是否是当前配置的模型
                    if (model.id === value || model.name === value) {
                        option.selected = true;
                        modelFound = true;
                    } else if (index === 0 && !modelFound) {
                        // 如果是第一个选项，并且还没有找到匹配的模型，设为默认选中
                        option.selected = true;
                    }
                    
                    input.appendChild(option);
                });
            } else {
                input = document.createElement('input');
                input.type = key === 'temperature' ? 'number' : 'text';
                if (key === 'temperature') {
                    input.step = '0.1';
                    input.min = '0';
                    input.max = '2';
                }
            }

            input.className = `ai-settings-input ${key}-input`;  // 添加特定的类名
            input.value = value === 'disabled' ? '' : value;
            input.disabled = value === 'disabled';
            input.style.cssText = `
                width: 100%;
                padding: 8px;
                background: #2a2a3a;
                border: 1px solid #3a3a4a;
                border-radius: 4px;
                color: #ffffff;
                box-sizing: border-box;
            `;

            formGroup.appendChild(label);
            formGroup.appendChild(input);
            this.paramsForm.appendChild(formGroup);
        });
    }

    // 加载模型列表
    async loadModelList() {
        try {
            this.modelList = await this.aiService.getModels();
            this.updateParamsForm(); // 重新更新表单以显示模型列表
        } catch (error) {
            console.error('加载模型列表失败:', error);
            this.showError('加载模型列表失败: ' + error.message);
        }
    }

    // 处理服务变更
    async handleServiceChange() {
        const selectedService = this.serviceSelect.value;
        try {
            // 获取新服务的配置
            this.config = await this.aiService.getConfig(selectedService);
            
            // 加载新服务的模型列表
            this.modelList = await this.aiService.getModels(selectedService);
            
            // 更新参数表单
            this.updateParamsForm();
        } catch (error) {
            console.error('切换服务失败:', error);
            this.showError('切换服务失败: ' + error.message);
        }
    }

    // 处理保存
    async handleSave() {
        try {
            // 收集表单数据
            this.issave = true;
            const formData = {
                service: this.serviceSelect.value,
                ai_params: {}
            };

            // 获取所有输入值
            const paramEntries = Object.entries(this.paramLabels);
            this.paramsForm.querySelectorAll('.ai-settings-input').forEach(input => {
                const key = input.className.split(' ')[1].replace('-input', '');
                if (!input.disabled) {
                    formData.ai_params[key] = input.value;
                }
            });

            // 保存配置
            await this.aiService.saveConfig(formData);
            this.showSuccess('保存成功');
            
            // 重新加载配置
            //await this.loadConfig();
        } catch (error) {
            console.error('保存配置失败:', error);
            this.showError('保存配置失败: ' + error.message);
        }
    }


    getConfig_value(){
        const formData = {
            service: this.serviceSelect.value,
            ai_params: {}
        };

        // 获取所有输入值
        const paramEntries = Object.entries(this.paramLabels);
        this.paramsForm.querySelectorAll('.ai-settings-input').forEach(input => {
            const key = input.className.split(' ')[1].replace('-input', '');
            if (!input.disabled) {
                formData.ai_params[key] = input.value;
            }
        });
        return formData;
    }

    // 处理取消
    handleCancel() {
        this.aiService.setConfig(this.old_config);
        this.loadConfig(); // 重新加载配置，恢复原始值
    }

    // 显示错误消息
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'ai-error';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            color: #ff5555;
            padding: 10px;
            margin: 10px 0;
            background: rgba(255, 85, 85, 0.1);
            border-radius: 4px;
        `;
        this.element.insertBefore(errorDiv, this.element.firstChild);
        setTimeout(() => errorDiv.remove(), 3000);
    }

    // 显示成功消息
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'ai-success';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            color: #50fa7b;
            padding: 10px;
            margin: 10px 0;
            background: rgba(80, 250, 123, 0.1);
            border-radius: 4px;
        `;
        this.element.insertBefore(successDiv, this.element.firstChild);
        setTimeout(() => successDiv.remove(), 3000);
    }

    // 处理显示/隐藏状态
    show_hide(show) {
        if (show) {
            this.issave = false;
            this.show();
        } else {
            this.hide();
        }
    }

    // 显示窗口
    show() {
        this.old_config=null;
        if (!this.visible) {
            this.element.style.display = 'flex';
            requestAnimationFrame(() => {
                this.element.style.opacity = '1';
            });
            this.visible = true;
            this.loadConfig(); // 每次显示时重新加载配置
        }
    }

    // 隐藏窗口
    hide() {
        if (this.visible) {
            this.element.style.opacity = '0';
            setTimeout(() => {
                if (!this.visible) {
                    this.element.style.display = 'none';
                }
            }, 300);
            this.visible = false;
        }
    }

    // 处理窗口大小变化
    handleResize() {
        // 可以在这里添加窗口大小变化时的处理逻辑
    }
}

export default AiSettingsWindow; 