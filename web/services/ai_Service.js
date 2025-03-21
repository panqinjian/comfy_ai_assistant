/**
 * ComfyUI AI Assistant 基础服务类
 */
class AiService {
    constructor() {
        // 使用完整的API路径
        this.baseUrl = '/comfy_ai_assistant';
        this.currentServiceId = null;
        this.service = null;
        this.service_ID_list = [];
        this.service_list = [];
        this.ai_params = {};
        this.config = null;
    }

    /**
     * 获取配置
     * @param {string|boolean} serviceOrLoop - 服务ID或循环标志
     * @returns {Promise<Object>} 配置对象
     */
    async getConfig(serviceOrLoop = false) {
        // 检查参数是否为布尔值（表示循环加载）或字符串（表示服务ID）
        const isLoop = typeof serviceOrLoop === 'boolean' && serviceOrLoop;
        const serviceId = typeof serviceOrLoop === 'string' ? serviceOrLoop : '';
        
        const fetchConfig = async () => {
            try {
                // 构建URL，如果有服务ID则添加到查询参数
                let url = `${this.baseUrl}/config`;
                if (serviceId) {
                    url += `?service=${encodeURIComponent(serviceId)}`;
                    console.log(`请求特定服务配置，服务ID: ${serviceId}`);
                }
                
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Unknown error');
                }
                
                // 确保返回的配置已设置了正确的服务ID
                if (serviceId && data.config && data.config.service !== serviceId) {
                    console.warn(`服务ID不匹配! 请求: ${serviceId}, 返回: ${data.config.service}, 已更正`);
                    data.config.service = serviceId;
                }
                this.setConfig(data.config);
                return data.config;
            } catch (error) {
                console.error('获取配置失败:', error);
                throw error;
            }
        };

        if (isLoop) {
            // 循环获取直到成功
            while (true) {
                try {
                    const config = await fetchConfig();
                    return config;
                } catch (error) {
                    console.log('获取配置失败，1秒后重试...');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
        } else {
            // 直接获取
            return await fetchConfig();
        }
    }

    /**
     * 获取历史记录
     * @returns {Promise<Array>} 历史记录数组
     */
    async getHistory() {
        try {
            // 先获取当前配置以获取服务ID
            const config = await this.getConfig();
            const serviceId = config.service || '';
            
            // 请求历史记录
            const response = await fetch(`${this.baseUrl}/history?service=${serviceId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '获取历史记录失败');
            }
            
            return data.history || [];
        } catch (error) {
            console.error('获取历史记录失败:', error);
            throw error;
        }
    }

    /**
     * 清除历史记录
     * @returns {Promise<Object>} 结果
     */
    async clearHistory() {
        try {
            // 先获取当前配置以获取服务ID
            const config = await this.getConfig();
            const serviceId = config.service || '';
            
            // 请求清除历史记录
            const response = await fetch(`${this.baseUrl}/clear_history`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    service: serviceId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '清除历史记录失败');
            }
            
            return data;
        } catch (error) {
            console.error('清除历史记录失败:', error);
            throw error;
        }
    }

    /**
     * 发送消息
     * @param {string} message - 消息内容
     * @param {Array} images - 图片列表（可选）
     * @returns {Promise<Object>} 响应结果
     */
    async sendMessage(message, images = []) {
        try {
            // 获取当前服务ID
            const serviceId = this.service || '';
            
            // 构建请求数据 - 只发送消息内容和服务ID，让后端处理参数
            const requestData = {
                message: message,
                service: serviceId
            };
            
            // 如果有图片，添加到请求数据中
            if (images && images.length > 0) {
                requestData.images = images;
            }
            
            // 发送消息
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '发送消息失败');
            }
            
            return data;
        } catch (error) {
            console.error('发送消息失败:', error);
            throw error;
        }
    }

    /**
     * 保存配置
     * @param {Object} config - 配置对象 
     * @returns {Promise<boolean>} 是否保存成功
     */
    async saveConfig(config) {
        try {
            // 确保服务ID在日志中
            console.log(`保存配置，服务ID: ${config.service}`);
            
            // 发送保存配置请求
            const response = await fetch(`${this.baseUrl}/save_config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '保存配置失败');
            }
            
            // 保存后刷新当前服务ID
            this.currentServiceId = config.service;
            this.setConfig(config);
            
            return true;
        } catch (error) {
            console.error('保存配置失败:', error);
            throw error;
        }
    }


    setConfig(config) {
        this.config = config;
        this.service = config.service;
        this.service_list = config.service_list;
        this.service_ID_list = config.service_ID_list;
        this.ai_params = config.ai_params;
    }

    /**
     * 获取可用模型列表
     * @returns {Promise<Array>} 模型列表
     */
    async getModels(selectedService) {
        try {
            // 先获取当前配置以获取服务ID
            let serviceId = null;
            if (selectedService==null) {
                const config = this.Config;
                serviceId = this.service;
            } else {
                serviceId = selectedService;
            }
            
            // 请求模型列表
            const response = await fetch(`${this.baseUrl}/models?service=${serviceId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '获取模型列表失败');
            }
            
            return data.models || [];
        } catch (error) {
            console.error('获取模型列表失败:', error);
            throw error;
        }
    }

    /**
     * 获取可用服务列表
     * @returns {Promise<Array>} 服务列表
     */
    async getServices() {
            return this.service_list;
    }

    /**
     * 保存历史记录
     * @param {Array} history - 历史记录数组
     * @returns {Promise<boolean>} 是否保存成功
     */
    async saveHistory(history) {
        try {
            // 获取当前服务ID
            const serviceId = this.service || '';
            
            // 构建请求数据
            const requestData = {
                service: serviceId,
                history: history
            };
            
            // 发送保存历史请求
            const response = await fetch(`${this.baseUrl}/save_history`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '保存历史记录失败');
            }
            
            console.log('历史记录保存成功');
            return true;
        } catch (error) {
            console.error('保存历史记录失败:', error);
            return false;
        }
    }
}

// 导出服务实例
export default new AiService(); 