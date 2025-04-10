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
        this.isProcessing = false; // 添加处理状态标志
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
    async getHistory(pageSize = 10, lastMessageId = null) {
        try {
            let url = `${this.baseUrl}/history?limit=${pageSize}`;
            if (lastMessageId) {
                url += `&message_id=${lastMessageId}`;
            }
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('获取历史记录成功:', data);
            
            if (!data.success) {
                throw new Error(data.error || '获取历史记录失败');
            }
            
            // 确保返回的数据结构正确
            return {
                records: data.data || [],
                hasMore: Boolean(data.has_more),  // 确保是布尔值
                nextId: Number(data.next_id) || null  // 确保是数字或 null
            };
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
            const response = await fetch(`${this.baseUrl}/clear_history`, {
                method: 'GET'  // 改为 GET 请求
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('清除历史记录成功:', data);
            
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
    async sendMessage(message, images = [], history_list = 0, currentPromptId = "") {
        try {
            // 获取当前服务ID
            const serviceId = this.service || '';
            
            // 构建请求数据
            const requestData = {
                message: message,
                service: serviceId,
                history: history_list,
                currentPromptId: currentPromptId
            };
            console.error('发送消息:', requestData);
            
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
            console.error('发送消息成功:', data);
            
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
                const config = this.config;
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
     * @param {Object} historyData - 历史记录数据
     * @returns {Promise<Object>} 保存结果
     */
    async saveHistory(historyData) {
        try {
            const response = await fetch(`${this.baseUrl}/save_history`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(historyData)  // 直接使用传入的数据结构
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || '保存历史记录失败');
            }
            
            return result;
        } catch (error) {
            console.error('保存历史记录失败:', error);
            throw error;
        }
    }

    /**
     * 重置服务状态
     * 用于清除可能导致AI卡住的状态
     */
    resetState() {
        console.log("重置AI服务状态...");
        
        // 重置处理状态标志
        this.isProcessing = false;
        
        // 重置临时缓存但保留基本配置
        const serviceId = this.service;
        
        // 记录当前服务ID，重置后恢复
        this.currentServiceId = null;
        this.service = null;
        
        // 暂存并清除当前配置
        const savedConfig = this.config;
        this.config = null;
        
        // 清除临时数据，但保留基本服务列表
        const savedServiceList = this.service_list;
        const savedServiceIdList = this.service_ID_list;
        
        this.service_list = [];
        this.service_ID_list = [];
        this.ai_params = {};
        
        // 恢复服务列表
        this.service_list = savedServiceList;
        this.service_ID_list = savedServiceIdList;
        
        // 如果有配置，恢复服务ID
        if (savedConfig) {
            this.service = serviceId;
        }
        
        console.log("AI服务状态已重置");
    }

    /**
     * 获取所有系统提示词
     */
    async getPrompts() {
        try {
            const response = await fetch('/comfy_ai_assistant/get_prompts');
            const data = await response.json();
            if (data.success) {
                return data.prompts;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('获取提示词列表失败:', error);
            throw error;
        }
    }

    /**
     * 获取当前或指定的系统提示词
     */
    async getPrompt(promptId) {
        try {
            const response = await fetch(`/comfy_ai_assistant/get_prompt?prompt_id=${promptId}`);
            const data = await response.json();
            if (data.success) {
                // 解码 base64 内容
                const content = atob(data.content);
                return content;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('获取提示词内容失败:', error);
            throw error;
        }
    }

    /**
     * 保存系统提示词
     * @param {Object} promptData - 提示词数据
     * @param {string} promptData.prompt_id - 提示词ID
     * @param {string} promptData.prompt_name - 提示词名称
     * @param {string} promptData.prompt_content_path - 提示词文件路径
     * @param {string} promptData.prompt_content - 提示词内容
     */
    async savePrompt(promptData) {
        try {
            const { prompt_id, prompt_name, prompt_content_path, prompt_content } = promptData;
            
            // 对内容进行 base64 编码
            const content_base64 = btoa(prompt_content);
            
            const response = await fetch('/comfy_ai_assistant/set_prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt_id,
                    prompt_name,
                    prompt_content_path,
                    prompt_content: content_base64
                })
            });
            
            const data = await response.json();
            if (data.success) {
                return true;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('保存提示词失败:', error);
            throw error;
        }
    }

    /**
     * 删除系统提示词
     */
    async deletePrompt(promptId) {
        try {
            const response = await fetch('/comfy_ai_assistant/delete_prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt_id: promptId
                })
            });
            
            const data = await response.json();
            if (data.success) {
                return true;
            } else {
                console.error('删除提示词失败:', data.error);
                return false;
            }
        } catch (error) {
            console.error('删除提示词失败:', error);
            return false;
        }
    }

    /**
     * 获取会话信息
     * @returns {Promise<Object>} 会话信息
     */
    async getSessionInfo() {
        try {
            const response = await fetch(`${this.baseUrl}/sessions`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || '获取会话信息失败');
            }
            
            return data.data;
        } catch (error) {
            console.error('获取会话信息失败:', error);
            throw error;
        }
    }

}

// 导出服务实例
export default new AiService();