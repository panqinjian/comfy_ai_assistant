/**
 * 简单的对话框组件
 */
class AiDialog {
    constructor() {
        this.dialog = null;
        this.init();
    }

    init() {
        // 创建对话框容器
        this.dialog = document.createElement('div');
        this.dialog.className = 'ai-dialog';
        this.dialog.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #2a2a3a;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: none;
            color: #ffffff;
            min-width: 300px;
            border: 1px solid #3a3a4a;
        `;

        // 添加到文档
        document.body.appendChild(this.dialog);
    }

    show(message, onConfirm, onCancel) {
        // 设置内容
        this.dialog.innerHTML = `
            <div style="margin-bottom: 20px;">${message}</div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="ai-dialog-cancel" style="
                    padding: 8px 16px;
                    background: #383838;
                    border: none;
                    border-radius: 4px;
                    color: #ffffff;
                    cursor: pointer;
                ">取消</button>
                <button class="ai-dialog-confirm" style="
                    padding: 8px 16px;
                    background: #2a5298;
                    border: none;
                    border-radius: 4px;
                    color: #ffffff;
                    cursor: pointer;
                ">确定</button>
            </div>
        `;

        // 添加事件监听
        const confirmBtn = this.dialog.querySelector('.ai-dialog-confirm');
        const cancelBtn = this.dialog.querySelector('.ai-dialog-cancel');

        confirmBtn.onclick = () => {
            if (onConfirm) onConfirm();
            this.hide();
        };

        cancelBtn.onclick = () => {
            if (onCancel) onCancel();
            this.hide();
        };

        // 显示对话框
        this.dialog.style.display = 'block';
    }

    hide() {
        this.dialog.style.display = 'none';
    }
}

export default new AiDialog(); 