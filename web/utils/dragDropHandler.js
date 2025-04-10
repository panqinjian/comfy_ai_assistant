class DragDropHandler {
    constructor(inputContainer, { 
        onFilesUploaded, // 新增上传完成回调
        onUploadError // 新增错误处理回调
    }) {
        this.inputContainer = inputContainer;
        this.onFilesUploaded = onFilesUploaded;
        this.onUploadError = onUploadError;
        this.initEventListeners();
    }

    /**
     * 处理图片上传到输入区域
     * @param {Object} inputArea - 输入区域组件
     * @param {Array} images - 图片数据数组
     */
    static handleImageUpload(inputArea, images) {
        if (!inputArea || !images || images.length === 0) {
            console.warn('输入区域或图片不存在，无法添加图片');
            return;
        }
        
        // 检查 inputArea 是否有 addSelectedImage 方法
        if (typeof inputArea.addSelectedImage !== 'function') {
            console.warn('输入区域没有 addSelectedImage 方法，无法添加图片');
            return;
        }
        
        // 处理图片
        images.forEach(img => {
            if (img && img.name && img.path) {
                inputArea.addSelectedImage(img.name, img.path);
            }
        });
    }
    
    /**
     * 处理文本添加到输入框
     * @param {HTMLTextAreaElement} inputElement - 输入框元素
     * @param {Array} texts - 文本数组
     */
    static handleTextInput(inputElement, texts) {
        if (!inputElement || !texts || texts.length === 0) {
            console.warn('输入元素或文本不存在，无法添加文本');
            return;
        }
        
        // 处理文本
        const currentText = inputElement.value;
        inputElement.value = currentText + (currentText ? '\n\n' : '') + texts.join('\n\n');
        
        // 自动调整高度
        inputElement.style.height = 'auto';
        inputElement.style.height = Math.min(inputElement.scrollHeight, 120) + 'px';
    }

    /**
     * 打开本地图片选择器
     * @param {Function} onImagesSelected - 图片选择后的回调函数
     */
    static openLocalImageSelector(onImagesSelected) {
        // 使用原生文件选择器
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.multiple = true;
        fileInput.style.display = 'none';
        
        fileInput.addEventListener('change', async (e) => {
            if (e.target.files.length > 0) {
                const files = Array.from(e.target.files);
                const uploadedFiles = [];
                
                for (const file of files) {
                    try {
                        // 创建 FormData 对象
                        const formData = new FormData();
                        formData.append('image', file);
                        
                        // 发送上传请求到 ComfyUI
                        const response = await fetch('/upload/image', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error(`上传失败: ${response.statusText}`);
                        }
                        
                        const result = await response.json();
                        if (result.name) {
                            uploadedFiles.push({
                                name: file.name,
                                path: `/api/view?filename=${result.name}&type=input&subfolder=&rand=${Math.random()}`,
                            });
                        }
                    } catch (error) {
                        console.error('上传图片失败:', error);
                        // 如果有错误回调，通知错误
                        if (typeof onError === 'function') {
                            onError({
                                fileName: file.name,
                                message: error.message
                            });
                        }
                    }
                }
                
                if (uploadedFiles.length > 0 && typeof onImagesSelected === 'function') {
                    onImagesSelected(uploadedFiles);
                }
            }
            document.body.removeChild(fileInput);
        });
        
        document.body.appendChild(fileInput);
        fileInput.click();
    }
    
    /**
     * 处理ComfyUI图片URL
     * @param {string} url - 图片URL
     * @returns {Object} 处理后的图片对象
     */
    static handleComfyUIImage(url) {
        // 清理URL，确保格式正确
        let imagePath = url.trim();
        
        // 检查是否已经包含完整URL
        if (!imagePath.startsWith('/api/view') && !imagePath.startsWith('http')) {
            // 尝试提取文件名
            const match = imagePath.match(/filename=([^&]+)/);
            if (match && match[1]) {
                imagePath = `/api/view?filename=${match[1]}&type=input&subfolder=&rand=${Math.random()}`;
            }
        }
        
        // 返回处理后的图片对象
        return {
            name: 'ComfyUI图片',
            path: imagePath
        };
    }
    
    /**
     * 处理文本文件
     * @param {File} file - 文本文件
     * @param {HTMLTextAreaElement} inputElement - 输入框元素
     * @param {Function} onSuccess - 成功回调
     * @param {Function} onError - 错误回调
     */
    static handleTextFile(file, inputElement, onSuccess, onError) {
        if (!file || !inputElement) {
            console.warn('文件或输入元素不存在，无法处理文本文件');
            if (typeof onError === 'function') {
                onError('文件或输入元素不存在，无法处理文本文件');
            }
            return;
        }
        
        try {
            // 使用FileReader读取文本内容
            const reader = new FileReader();
            
            reader.onload = (event) => {
                const fileContent = event.target.result;
                
                // 将文本内容添加到输入框
                const currentText = inputElement.value;
                const cursorPos = inputElement.selectionStart;
                inputElement.value = currentText.substring(0, cursorPos) + fileContent + currentText.substring(inputElement.selectionEnd);
                
                // 调整输入框高度
                inputElement.style.height = 'auto';
                inputElement.style.height = Math.min(inputElement.scrollHeight, 120) + 'px';
                
                // 调用成功回调
                if (typeof onSuccess === 'function') {
                    onSuccess(`已成功导入文件 "${file.name}"`);
                }
            };
            
            reader.onerror = (error) => {
                console.error('读取文件失败:', error);
                // 调用错误回调
                if (typeof onError === 'function') {
                    onError(`读取文件 "${file.name}" 失败: ${error.message || '未知错误'}`);
                }
            };
            
            // 开始读取文件
            console.log('开始读取文本文件:', file.name);
            reader.readAsText(file);
        } catch (error) {
            console.error('读取文本文件失败:', error);
            // 调用错误回调
            if (typeof onError === 'function') {
                onError(`读取文件 "${file.name}" 失败: ${error.message}`);
            }
        }
    }

    /**
     * 处理拖拽的文本文件
     * @param {File} file - 文本文件
     * @returns {Promise<string>} 文件内容
     */
    static async readTextFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                resolve(event.target.result);
            };
            
            reader.onerror = (error) => {
                console.error('读取文件失败:', error);
                reject(new Error(`读取文件 "${file.name}" 失败: ${error.message || '未知错误'}`));
            };
            
            console.log('开始读取文本文件:', file.name);
            reader.readAsText(file);
        });
    }

    async handleFileUpload(imageFiles, textFiles, callbacks) {
        try {
            // 处理图片文件上传
            const imageResults = await Promise.all(imageFiles.map(async (file) => {
                try {
                    const formData = new FormData();
                    formData.append('image', file);
                    
                    const response = await fetch('/upload/image', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) throw Object.assign(new Error(`上传失败: ${response.statusText}`), { file });
                    
                    const result = await response.json();
                    return {
                        name: file.name,
                        path: `/api/view?filename=${result.name}&type=input&subfolder=&rand=${Math.random()}`
                    };
                } catch (error) {
                    throw Object.assign(error, { file });
                }
            }));
            
            // 处理文本文件内容
            const textContents = await Promise.all(
                textFiles.map(async (file) => {
                    try {
                        return await file.text();
                    } catch (error) {
                        throw Object.assign(new Error(`文件读取失败: ${file.name}`), { file: file });
                    }
                })
            );
            
            console.log('文本文件内容:', textContents);
            
            // 执行统一回调
            if (typeof callbacks.onComplete === 'function') {
                callbacks.onComplete({
                    images: imageResults,
                    texts: textContents
                });
            }
        } catch (error) {
            console.error('文件处理失败:', error);
            
            if (typeof callbacks.onError === 'function') {
                callbacks.onError({
                    fileName: error.file ? error.file.name : '未知文件',
                    message: error.message || '处理失败'
                });
            }
        }
    }

    // 新增文件分类处理方法
    async processDroppedFiles(files) {
        const imageFiles = [];
        const textFiles = [];

        for (const file of files) {
            // 更精确地检测文件类型
            const fileType = file.type.toLowerCase();
            const fileName = file.name.toLowerCase();
            
            console.log('处理文件:', file.name, '类型:', fileType);
            
            if (fileType.startsWith('image/')) {
                imageFiles.push(file);
                console.log('图片文件已添加:', file.name);
            } else if (fileType === 'text/plain' || 
                      fileType === 'application/json' || 
                      fileType === 'text/html' || 
                      fileType === 'text/css' || 
                      fileType === 'text/javascript' || 
                      fileType === 'application/xml' || 
                      fileType === 'text/markdown' ||
                      fileName.endsWith('.txt') || 
                      fileName.endsWith('.md') || 
                      fileName.endsWith('.py') || 
                      fileName.endsWith('.js') || 
                      fileName.endsWith('.jsx') || 
                      fileName.endsWith('.ts') || 
                      fileName.endsWith('.tsx') || 
                      fileName.endsWith('.html') || 
                      fileName.endsWith('.css') || 
                      fileName.endsWith('.json') || 
                      fileName.endsWith('.xml') || 
                      fileName.endsWith('.yaml') || 
                      fileName.endsWith('.yml')) {
                textFiles.push(file);
                console.log('文本文件已添加:', file.name);
            } else {
                // 如果文件类型未知，尝试作为文本文件处理
                console.log('未知文件类型，尝试作为文本文件处理:', file.name);
                textFiles.push(file);
            }
        }

        console.log('处理文件结果:', { imageFiles, textFiles });
        return { imageFiles, textFiles };
    }

    initEventListeners() {
        this.inputContainer.addEventListener('dragover', this.handleDragOver.bind(this));
        this.inputContainer.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.inputContainer.addEventListener('drop', this.handleDrop.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputContainer.style.borderColor = '#6a8eff';
        this.inputContainer.style.backgroundColor = '#2a2a40';
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputContainer.style.borderColor = '#3a3a4a';
        this.inputContainer.style.backgroundColor = '#1e1e2e';
    }

    async handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.inputContainer.style.borderColor = '#3a3a4a';
        this.inputContainer.style.backgroundColor = '#1e1e2e';

        console.log('文件拖放事件触发');
        if (e.dataTransfer.items) {
            const files = Array.from(e.dataTransfer.items)
                .filter(item => item.kind === 'file')
                .map(item => item.getAsFile());

            console.log('拖放的文件数量:', files.length);
            if (files.length > 0) {
                // 调用文件分类处理方法
                const { imageFiles, textFiles } = await this.processDroppedFiles(files);
                
                // 直接处理文本文件
                if (textFiles.length > 0) {
                    try {
                        const textContents = await Promise.all(
                            textFiles.map(file => DragDropHandler.readTextFile(file))
                        );
                        
                        console.log('读取到的文本内容:', textContents);
                        
                        if (this.onFilesUploaded) {
                            this.onFilesUploaded({
                                images: [],
                                texts: textContents
                            });
                        }
                    } catch (error) {
                        console.error('处理文本文件失败:', error);
                        if (this.onUploadError) {
                            this.onUploadError({
                                fileName: error.file ? error.file.name : '文本文件',
                                message: error.message || '处理失败'
                            });
                        }
                    }
                }
                
                // 处理图片文件上传
                if (imageFiles.length > 0) {
                await this.handleFileUpload(imageFiles, textFiles, {
                    onComplete: this.onFilesUploaded,
                    onError: this.onUploadError
                });
            }
            }
            // 处理拖拽的文本
            else if (e.dataTransfer.getData('text')) {
                const text = e.dataTransfer.getData('text');
                
                // 检查文本是否是图片URL
                if (this.isImageUrl(text)) {
                    // 如果是图片URL，作为图片处理
                    if (this.onFilesUploaded) {
                        this.onFilesUploaded({
                            images: [DragDropHandler.handleComfyUIImage(text)],
                            texts: []
                        });
                    }
                } else {
                    // 如果有文本拖拽回调，执行它
                    if (this.onFilesUploaded) {
                        this.onFilesUploaded({
                            images: [],
                            texts: [text]
                        });
                    }
                }
            }
        }
        // 直接处理文本拖拽（某些浏览器可能不支持items）
        else if (e.dataTransfer.getData('text')) {
            const text = e.dataTransfer.getData('text');
            
            // 检查文本是否是图片URL
            if (this.isImageUrl(text)) {
                // 如果是图片URL，作为图片处理
                if (this.onFilesUploaded) {
                    this.onFilesUploaded({
                        images: [DragDropHandler.handleComfyUIImage(text)],
                        texts: []
                    });
                }
            } else {
                // 如果有文本拖拽回调，执行它
                if (this.onFilesUploaded) {
                    this.onFilesUploaded({
                        images: [],
                        texts: [text]
                    });
                }
            }
        }
    }

    // 检查文本是否是图片URL
    isImageUrl(text) {
        // 检查是否是ComfyUI图片URL
        if (text.includes('/api/view') || 
            text.includes('filename=') || 
            text.match(/\.(jpg|jpeg|png|gif|webp|bmp)($|\?)/i)) {
            return true;
        }
        
        // 检查是否是普通图片URL
        try {
            const url = new URL(text);
            const path = url.pathname.toLowerCase();
            return path.endsWith('.jpg') || 
                   path.endsWith('.jpeg') || 
                   path.endsWith('.png') || 
                   path.endsWith('.gif') || 
                   path.endsWith('.webp') || 
                   path.endsWith('.bmp');
        } catch (e) {
            // 如果不是有效URL，返回false
            return false;
        }
    }

    /**
     * 处理拖放的文件上传
     * @param {Array} files - 文件数组
     * @param {Function} onSuccess - 成功回调
     * @param {Function} onError - 错误回调
     * @returns {Promise<Array>} 上传成功的文件数组
     */
    static async handleDroppedFiles(files, onSuccess, onError) {
        const uploadedFiles = [];
        
        for (const file of files) {
            try {
                // 创建 FormData 对象
                const formData = new FormData();
                formData.append('image', file);
                
                // 发送上传请求到 ComfyUI
                const response = await fetch('/upload/image', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`上传失败: ${response.statusText}`);
                }
                
                const result = await response.json();
                if (result.name) {
                    uploadedFiles.push({
                        name: file.name,
                        path: `/api/view?filename=${result.name}&type=input&subfolder=&rand=${Math.random()}`,
                    });
                }
            } catch (error) {
                console.error('上传图片失败:', error);
                // 显示上传错误通知
                if (typeof onError === 'function') {
                    onError(file.name, error.message);
                }
            }
        }
        
        if (uploadedFiles.length > 0 && typeof onSuccess === 'function') {
            onSuccess(uploadedFiles);
        }
        
        return uploadedFiles;
    }

    /**
     * 处理选择的图片并添加到预览区域
     * @param {Array} files - 图片文件数组
     * @param {Object} container - 预览容器
     * @param {Array} selectedImages - 已选择的图片数组
     * @param {Function} onRemove - 移除图片的回调函数
     */
    static handleSelectedImages(files, container, selectedImages, onRemove) {
        if (!files || files.length === 0 || !container) return;
        
        // 限制图片数量
        const maxImages = 5;
        if (selectedImages.length + files.length > maxImages) {
            alert(`最多只能添加${maxImages}张图片`);
            files = files.slice(0, maxImages - selectedImages.length);
        }
        
        // 添加图片到预览区域
        files.forEach(file => {
            const imagePath = file.path || file;
            selectedImages.push(imagePath);
            
            const thumbnail = document.createElement('div');
            thumbnail.className = 'ai-attachment-thumbnail';
            
            const img = document.createElement('img');
            img.src = imagePath;
            img.alt = file.name || '图片';
            
            const removeButton = document.createElement('div');
            removeButton.className = 'remove-image';
            removeButton.innerHTML = '×';
            removeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                if (typeof onRemove === 'function') {
                    onRemove(imagePath, thumbnail);
                }
            });
            
            thumbnail.appendChild(img);
            thumbnail.appendChild(removeButton);
            container.appendChild(thumbnail);
        });
        
        // 显示附件预览区域
        if (selectedImages.length > 0) {
            container.style.display = 'flex';
        }
    }
}

export default DragDropHandler;