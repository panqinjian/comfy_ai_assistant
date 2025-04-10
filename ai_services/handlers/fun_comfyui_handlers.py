from decimal import Decimal
import json
import re
import time
import html
import unicodedata
from ..utils.html_parser import HtmlParser
from jsonfinder import jsonfinder
import base64
import os
from nodes import NODE_CLASS_MAPPINGS
import folder_paths
# 尝试导入 demjson3，如果不可用则提供备用方案
try:
    import demjson3
    HAS_DEMJSON = True
except ImportError:
    HAS_DEMJSON = False
    print("警告: demjson3 库未安装，JSON 修复功能将受限。建议安装: pip install demjson3")


def fix_json(json_str):
    """
    尝试修复不完整或格式不正确的 JSON
    
    Args:
        json_str: 可能有问题的 JSON 字符串
        
    Returns:
        修复后的 JSON 对象，如果无法修复则返回原始字符串
    """
    # 如果输入不是字符串，直接返回
    if not isinstance(json_str, str):
        return json_str

    # 转换全角字符为半角字符
    half_width = unicodedata.normalize('NFKC', json_str)

    # 如果有 demjson3，使用它来修复
    try:
        if HAS_DEMJSON:
            import demjson3
            data = demjson3.decode(half_width)
            return data
    except Exception as e:
        print(f"demjson3 修复失败: {str(e)}")

    # 手动修复常见问题
    try:
        # 计算左右大括号的数量
        left_braces = half_width.count('{')
        right_braces = half_width.count('}')

        # 添加缺失的右大括号
        if left_braces > right_braces:
            fixed = half_width + "}" * (left_braces - right_braces)
            try:
                data = json.loads(fixed)
                return data
            except json.JSONDecodeError:
                pass

        # 尝试使用正则表达式修复常见问题
        # 修复缺少引号的键
        fixed = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', half_width)
        # 修复尾随逗号
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)

        try:
            data = json.loads(fixed)
            return data
        except json.JSONDecodeError:
            pass

        # 尝试提取任何可能的 JSON 对象
        json_match = re.search(r'{.*}', half_width, re.DOTALL)
        if json_match:
            json_obj = json_match.group(0)  # 提取匹配到的 JSON 对象
            try:
                data = json.loads(json_obj)
                return data
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"手动 JSON 修复失败: {str(e)}")

    # 如果所有尝试都失败，返回原始字符串
    return json_str

def check_workflow(workflow_json):
    """
    检查ComfyUI工作流的基本结构和连接是否正确
    :param workflow_json: 工作流的JSON数据
    :return: True 表示基本结构和连接正确，False 表示存在问题
    """
    try:
        # 解析JSON数据
        workflow = json.loads(workflow_json)

        # 检查每个节点
        for node_id, node in workflow.items():
            class_type = node.get("class_type")
            if not class_type:
                print(f"节点 {node_id} 缺少 class_type")
                return False

            inputs = node.get("inputs", {})
            for input_name, input_value in inputs.items():
                if isinstance(input_value, dict) and "node_id" in input_value:
                    target_node_id = input_value["node_id"]
                    if target_node_id not in workflow:
                        print(f"节点 {node_id} 的输入 {input_name} 指向了不存在的节点 {target_node_id}")
                        return False

        return True
    except json.JSONDecodeError:
        print("工作流JSON数据解析失败")
        return False

def fun_process_workflow_response(ai_response):
    """
    处理 ComfyUI 工作流响应，生成 HTML 显示模块
    
    Args:
        ai_response: AI 返回的响应文本
        
    Returns:
        str: 包含工作流显示和操作按钮的 HTML
    """
    groups, content = HtmlParser.parse_content_tag(ai_response)
    
    # 提取并统一转换为字符串
    type = str(groups.get('type', [])[0]) if groups.get('type', []) else None
    title = str(groups.get('title', [])[0]) if groups.get('title', []) else None
    workflow = str(groups.get('workflow', [])[0]) if groups.get('workflow', []) else None
    explanation = str(groups.get('explanation', [])[0]) if groups.get('explanation', []) else None
    nodes = str(groups.get('nodes', [])[0]) if groups.get('nodes', []) else None
    model = str(groups.get('model', [])[0]) if groups.get('model', []) else None

    # 检查 JSON 是否闭合
    if  is_json_closed(workflow):
        print(f"JSON 闭合检查成功")
        try:
            workflow_content = fix_json(workflow)  # 解析 JSON 字符串
            print(f"JSON 解析成功")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            return generate_html_response(
                    ai_response, None, f"JSON 解析错误: {str(e)}", "error"
                )
    else:
        print(f"JSON 未闭合1")
        for json_obj in jsonfinder(workflow):
            for json_obj2 in json_obj:
                workflow_content_str=json.dumps(json_obj2)
                if  is_json_closed(workflow_content_str) and len(workflow_content_str) > 100:
                   workflow_content=workflow_content_str
                   break
        # 检查 JSON 是否闭合
        if  is_json_closed(workflow_content):
            print(f"JSON 闭合检查成功")
            try:
                workflow_content = fix_json(workflow_content)  # 解析 JSON 字符串
                print(f"JSON 解析成功")
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                return generate_html_response(
                    ai_response, None, f"JSON 解析错误: {str(e)}", "error"
                )
        else:
            print(f"JSON 未闭合2")
            return generate_html_response(
                ai_response, None, f"JSON 未闭合", "error"
                )
    

    timestamp = int(time.time())
    if title:
        # 将标题转换为有效的文件名
        print(f"成功生成 filename1: {title}")
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        filename = f"{safe_title}_{timestamp}.json"
        print(f"成功生成 filename2: {filename}")
    else:
        filename = f"workflow_{timestamp}.json"
        print(f"成功生成 filename3: {filename}")

    workflow_content = convert_decimals(workflow_content) 
    try:
        # 生成base64
        workflow_json_str = json.dumps(workflow_content)
        print(f"workflow_json_str 解析成功")
        # 进行 Base64 编码
        base64_content = base64.b64encode(workflow_json_str.encode('utf-8')).decode('utf-8')
        #base64_content = base64.b64encode(str(workflow_content).encode()).decode()
        print(f"成功生成 base64_content: {len(base64_content)} 字符")
    except Exception as e:
        print(f"生成 base64_content 失败: {str(e)}")
        # 最后的备用方案
        return generate_html_response(
                    ai_response, None, f"生成 base64_content 失败: {str(e)}", "error"
                )
    
    return generate_html_response(
        explanation or ai_response,  # 使用解释文本或原始响应
        workflow_content,
        f"工作流已正确解析",
        "success",
        title=title,
        nodes=nodes,
        model=model,
        filename=filename,
        workflow_content_base64=base64_content
    )

# 遍历数据，将 Decimal 类型转换为 float 类型
from decimal import Decimal

def convert_decimals(data):
    if isinstance(data, list):
        return [convert_decimals(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_decimals(value) for key, value in data.items()}
    elif isinstance(data, Decimal):
        return float(data)
    return data

        

def json_serialize(obj):
    """
    将对象序列化为 JSON 安全的数据结构
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        JSON 安全的数据结构
    """
    try:
        if obj is None:
            return None
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):  # 处理日期和时间对象
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # 处理自定义对象
            return obj.__dict__
        elif isinstance(obj, (list, tuple)):
            return [json_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: json_serialize(value) for key, value in obj.items()}
        elif isinstance(obj, (int, float, str, bool)):
            return obj
        else:
            # 对于其他类型，尝试转换为字符串
            return str(obj)
    except Exception as e:
        print(f"序列化错误: {type(obj)} - {str(e)}")
        return str(obj)  # 失败时返回字符串表示


def is_json_closed(json_str):
    """检查 JSON 是否闭合"""
    # 如果不是字符串，直接返回False
    if not isinstance(json_str, str):
        return False
    
    # 使用简单的括号匹配
    left_curly = json_str.count('{')
    right_curly = json_str.count('}')
    left_square = json_str.count('[')
    right_square = json_str.count(']')
    return left_curly == right_curly and left_square == right_square

def generate_html_response(ai_response, workflow_json, message, status, nodes=None, model=None, **kwargs):
    """
    生成包含工作流显示和操作按钮的 HTML
    
    Args:
        ai_response: 原始 AI 响应
        workflow_json: 工作流 JSON 字符串或对象
        message: 处理结果消息
        status: 状态 (success/error)
        nodes: 节点信息
        model: 模型信息
        **kwargs: 其他参数
        
    Returns:
        str: HTML 响应
    """
    if status == "error":
        return ai_response
    # 生成唯一的时间戳，避免函数名冲突
    timestamp = int(time.time() * 1000)
    
    # 提取 AI 解释部分 (JSON 之前的文本)
    explanation = ""
    if ai_response and isinstance(ai_response, str):
        json_start = ai_response.find('{')
        if json_start > 0:
            explanation = ai_response[:json_start].strip()
        else:
            explanation = ai_response
    
    # 将工作流 JSON 转换为字符串 (如果是对象)
    if workflow_json and not isinstance(workflow_json, str):
        workflow_json = json.dumps(workflow_json, ensure_ascii=False, indent=2)
    
    # 构建 HTML
    html_parts = []
    
    # 开始一个隔离容器，避免外部样式影响
    html_parts.append('<div class="comfyui-workflow-isolated-container" style="all:initial; font-family:Arial,sans-serif; display:block; color:#e0e0e0;">')
    
    # 添加 CSS 样式
    html_parts.append("""
    <style>
        /* 全局重置，确保不受外部影响 */
        .comfyui-workflow-isolated-container * {
            box-sizing: border-box !important;
            font-family: Arial, sans-serif !important;
        }
        
        /* 确保不受外部pre样式影响 */
        .comfyui-workflow-isolated-container pre {
            margin: 0 !important;
            padding: 0 !important;
            white-space: pre-wrap !important;
            font-family: monospace !important;
            background: none !important;
            border: none !important;
        }
        
        .comfyui-workflow-isolated-container code {
            font-family: monospace !important;
            background: none !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* 工作流容器样式 */
        .workflow-container {
            font-family: Arial, sans-serif !important;
            margin: 8px 0 !important;
            border: 1px solid #444 !important;
            border-radius: 4px !important;
            overflow: hidden !important;
            background-color: #2a2a3a !important;
            color: #e0e0e0 !important;
            line-height: normal !important;
            display: block !important;
        }
        
        /* 标题区域 */
        .workflow-header {
            background-color: #3a3a4a !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid #555 !important;
            margin: 0 !important;
            display: block !important;
        }
        
        .workflow-title {
            margin: 0 !important;
            font-size: 15px !important;
            color: #ffffff !important;
            padding: 0 !important;
            font-weight: normal !important;
            line-height: 1.3 !important;
        }
        
        /* 消息区域 */
        .workflow-message {
            padding: 6px 10px !important;
            font-size: 14px !important;
            border-bottom: 1px solid #555 !important;
            margin: 0 !important;
            display: block !important;
            line-height: 1.3 !important;
        }
        
        /* 成功/错误状态 */
        .workflow-message.success {
            background-color: #2e7d32 !important;
            color: #e8f5e9 !important;
        }
        
        .workflow-message.error {
            background-color: #c62828 !important;
            color: #ffebee !important;
        }
        
        /* 解释文本 */
        .workflow-explanation {
            padding: 6px 10px !important;
            font-size: 14px !important;
            border-bottom: 1px solid #555 !important;
            white-space: pre-wrap !important;
            color: #e0e0e0 !important;
            margin: 0 !important;
            display: block !important;
            line-height: 1.3 !important;
        }
        
        /* 代码区域 */
        .workflow-code {
            margin: 0 !important;
            padding: 6px 10px !important;
            position: relative !important;
            display: block !important;
        }
        
        .workflow-code pre {
            background-color: #1e1e2e !important;
            border: 1px solid #555 !important;
            border-radius: 2px !important;
            padding: 8px !important;
            overflow: auto !important;
            max-height: 400px !important;
            font-family: monospace !important;
            font-size: 13px !important;
            white-space: pre-wrap !important;
            color: #e0e0e0 !important;
            margin: 0 !important;
            line-height: 1.3 !important;
        }
        
        /* 按钮区域 */
        .workflow-actions {
            margin: 0 !important;
            padding: 6px 10px !important;
            display: flex !important;
            gap: 8px !important;
        }
        
        .workflow-button {
            padding: 6px 12px !important;
            border: none !important;
            border-radius: 2px !important;
            cursor: pointer !important;
            font-weight: normal !important;
            font-size: 14px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 4px !important;
            height: 56px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }
        
        /* 按钮颜色 */
        .load-button {
            background-color: #4caf50 !important;
            color: white !important;
        }
        
        .load-button:hover {
            background-color: #388e3c !important;
        }
        
        .copy-button {
            background-color: #2196f3 !important;
            color: white !important;
        }
        
        .copy-button:hover {
            background-color: #1976d2 !important;
        }
        
        .download-button {
            background-color: #ff9800 !important;
            color: white !important;
        }
        
        .download-button:hover {
            background-color: #f57c00 !important;
        }
        
        /* 语法高亮 */
        .json-key { color: #9cdcfe !important; }
        .json-string { color: #ce9178 !important; }
        .json-number { color: #b5cea8 !important; }
        .json-boolean { color: #569cd6 !important; }
        .json-null { color: #569cd6 !important; }
        
        /* 依赖区域 */
        .workflow-dependencies {
            margin: 0 !important;
            padding: 0 10px 6px 10px !important;
            border-top: none !important;
            display: block !important;
        }
        
        .node-status, .model-status {
            background-color: #1e1e2e !important;
            border: 1px solid #555 !important;
            border-radius: 2px !important;
            padding: 6px 8px !important;
            margin: 4px 0 !important;
            color: #e0e0e0 !important;
            display: block !important;
        }
        
        .node-status h4, .model-status h4 {
            margin: 0 0 2px 0 !important;
            padding: 0 !important;
            color: #9cdcfe !important;
            font-size: 14px !important;
            font-weight: normal !important;
            line-height: 1.3 !important;
            display: block !important;
        }
        
        .node-status p, .model-status p {
            margin: 0 0 2px 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
            display: block !important;
        }
        
        .node-status ul, .model-status ul {
            margin: 2px 0 !important;
            padding-left: 20px !important;
            list-style-position: outside !important;
            display: block !important;
        }
        
        .node-status li, .model-status li {
            margin: 0 0 1px 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
            display: list-item !important;
        }
        
        /* 按钮样式 */
        .node-status button, .model-status button {
            background-color: #4caf50 !important;
            color: white !important;
            border: none !important;
            padding: 0px 4px !important;
            border-radius: 2px !important;
            cursor: pointer !important;
            font-size: 12px !important;
            height: 16px !important;
            margin: 0 2px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 24px !important;
            text-align: center !important;
            vertical-align: middle !important;
            line-height: 1 !important;
        }
    </style>
    """)
    
    # 添加容器开始
    html_parts.append('<div class="workflow-container">')
        
    # 添加 AI 解释 (如果有)
    if explanation:
        html_parts.append(f'<div class="workflow-explanation">{html.escape(explanation)}</div>')
    
    # 添加标题
    title = kwargs.get('title', '工作流')
    html_parts.append(f'<div class="workflow-header"><h3 class="workflow-title">{html.escape(title)}</h3></div>')
    
    # 添加消息
    html_parts.append(f'<div class="workflow-message {status}">{html.escape(message)}</div>')
    

    
    # 添加工作流代码 (如果有)
    if workflow_json:
        # 简单的语法高亮处理
        highlighted_json = workflow_json
        # 高亮键名
        highlighted_json = re.sub(r'"([^"]+)":', r'<span class="json-key">"\1"</span>:', highlighted_json)
        # 高亮字符串值
        highlighted_json = re.sub(r':\s*"([^"]*)"', r': <span class="json-string">"\1"</span>', highlighted_json)
        # 高亮数字
        highlighted_json = re.sub(r':\s*(-?\d+(\.\d+)?)', r': <span class="json-number">\1</span>', highlighted_json)
        # 高亮布尔值和null
        highlighted_json = re.sub(r':\s*(true|false|null)', r': <span class="json-boolean">\1</span>', highlighted_json)
        
        # 添加一个隐藏的纯文本区域，用于复制和下载
        html_parts.append(f'<textarea id="workflow_json_{timestamp}" style="display:none;">{html.escape(workflow_json)}</textarea>')
        
        html_parts.append('<div class="workflow-code">')
        html_parts.append(f'<pre><code id="json_display_{timestamp}" class="language-json">{highlighted_json}</code></pre>')
        html_parts.append('</div>')
    
    # 添加操作按钮
    html_parts.append('<div class="workflow-actions">')
    
    # 只有在成功时才添加加载按钮
    if status == "success" and kwargs.get('workflow_content_base64'):
        workflow_content_base64 = kwargs.get('workflow_content_base64')
        html_parts.append(f'''
        <button class="workflow-button load-button" onclick="(function() {{
            try {{
                const jsonContent = JSON.parse(atob('{workflow_content_base64}'));
                
                // 检查是否在 ComfyUI 环境中
                if (typeof app !== 'undefined' && app.loadGraphData) {{
                    // 直接使用 ComfyUI 的 API 加载工作流
                    app.loadGraphData(jsonContent);
                    alert('工作流已成功加载到 ComfyUI');
                }} else {{
                    // 使用 postMessage 尝试加载
                    window.parent.postMessage({{ type: 'loadComfyUIWorkflow', workflow: jsonContent }}, '*');
                    alert('已尝试加载工作流，如果您在 ComfyUI 环境中，工作流应该已加载');
                }}
            }} catch (error) {{
                alert('加载工作流失败: ' + error.message);
            }}
        }})()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12H19M19 12L13 6M19 12L13 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            加载工作流
        </button>
        ''')
    
    # 复制按钮 (如果有工作流 JSON)
    if workflow_json:
        html_parts.append(f'''
        <button class="workflow-button copy-button" onclick="(function() {{
            try {{
                // 获取隐藏的文本区域
                const textArea = document.getElementById('workflow_json_{timestamp}');
                if (!textArea) throw new Error('找不到工作流 JSON');
                
                // 选择文本并复制
                textArea.style.display = 'block';
                textArea.select();
                const success = document.execCommand('copy');
                textArea.style.display = 'none';
                
                if (success) {{
                    alert('工作流 JSON 已复制到剪贴板');
                }} else {{
                    throw new Error('复制命令失败');
                }}
            }} catch (err) {{
                console.error('复制失败:', err);
                
                // 备选方案：提示用户手动复制
                alert('自动复制失败，请手动选择并复制 JSON 内容');
                
                // 显示 JSON 内容以便手动复制
                const codeElement = document.getElementById('json_display_{timestamp}');
                if (codeElement) {{
                    const range = document.createRange();
                    range.selectNode(codeElement);
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                }}
            }}
        }})()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 5H6C4.89543 5 4 5.89543 4 7V19C4 20.1046 4.89543 21 6 21H16C17.1046 21 18 20.1046 18 19V17M8 5C8 6.10457 8.89543 7 10 7H14C15.1046 7 16 6.10457 16 5M8 5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5M16 5V7C16 8.10457 16.8954 9 18 9H20C21.1046 9 22 9.89543 22 11V17C22 18.1046 21.1046 19 20 19H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            复制 JSON
        </button>
        ''')
    
    # 下载按钮 (如果有文件名)
    if kwargs.get('filename') and workflow_json:
        filename = kwargs.get('filename')
        html_parts.append(f'''
        <button class="workflow-button download-button" onclick="(function() {{
            try {{
                // 获取隐藏的文本区域内容
                const textArea = document.getElementById('workflow_json_{timestamp}');
                if (!textArea) throw new Error('找不到工作流 JSON');
                
                // 获取 JSON 内容
                const jsonContent = textArea.value;
                
                // 使用 Data URL 方法下载（最兼容的方法）
                const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(jsonContent);
                const a = document.createElement('a');
                a.href = dataUrl;
                a.download = '{filename}';
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                setTimeout(function() {{
                    document.body.removeChild(a);
                }}, 100);
            }} catch (error) {{
                console.error('下载工作流失败:', error);
                alert('下载工作流失败: ' + error.message);
            }}
        }})()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 17V19C4 20.1046 4.89543 21 6 21H18C19.1046 21 20 20.1046 20 19V17M7 11L12 16M12 16L17 11M12 16V4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            下载工作流
        </button>
        ''')
    
    # 关闭 actions div
    html_parts.append('</div>')  # 关闭 actions div

    # 添加节点和模型状态显示
    html_parts.append('<div class="workflow-dependencies" style="margin:0; padding:4px 10px 6px 10px; border-top:none;">')  # 包含节点和模型状态的容器
    
    if nodes:
        try:
            nodes_data = fix_json(nodes)
            node_status_html = generate_node_status_html(nodes_data)
            html_parts.append(node_status_html)
        except Exception as e:
            print(f"解析节点信息失败: {e}")
            html_parts.append(f"<div class='node-status' style='margin:2px 0;'><p style='color: #f44336; margin:0; padding:0;'>解析节点信息失败: {e}</p></div>")

    if model:
        try:
            model_data = fix_json(rf'{model}')
            model_status_html = generate_model_status_html(rf'{model_data}')
            html_parts.append(model_status_html)
        except Exception as e:
            print(f"解析模型信息失败: {e}")
            html_parts.append(f"<div class='model-status' style='margin:2px 0;'><p style='color: #f44336; margin:0; padding:0;'>解析模型信息失败: {e}</p></div>")
    
    html_parts.append('</div>')  # 关闭 workflow-dependencies div
    
    # 关闭容器
    html_parts.append('</div>')
    
    # 关闭隔离容器
    html_parts.append('</div>')
    
    # 返回完整的 HTML
    return ''.join(html_parts)




def generate_node_status_html(nodes_data):
    """生成节点状态 HTML"""
    if not nodes_data or not isinstance(nodes_data, dict) or len(nodes_data) == 0:
        nodes_data = json.loads(nodes_data)
        
    html_parts = ["<div class='node-status' style='margin:2px 0; padding:6px 8px;'>"]
    
    # 统计数量
    total_nodes = len(nodes_data)
    available_nodes = sum(1 for node_name in nodes_data if check_node_exists(node_name))
    
    html_parts.append(f"<h4 style='margin:0 0 2px 0; padding:0; line-height:1.3;'>工作流所需节点 <span style='font-weight:normal;font-size:13px;color:#e0e0e0;'>(共 {total_nodes} 个节点，已安装 {available_nodes} 个，缺少 {total_nodes - available_nodes} 个)</span></h4>")
    
    # 节点列表
    html_parts.append("<ul style='margin:2px 0; padding-left:20px; list-style-position:outside;'>")
    missing_nodes_html = []
    installed_nodes_html = []
    
    for node_name, node_info in nodes_data.items():
        if isinstance(node_info, dict):
            download_url = node_info.get("downloadurl", "")
            version = node_info.get("version", "")
        else:
            # 如果node_info不是字典，使用空值
            download_url = ""
            version = ""
        
        # 检查节点是否存在于本地
        is_node_available = check_node_exists(node_name)
        
        node_html = f"<li style='margin-bottom:1px;line-height:1.3;'><span style='color: {'#4caf50' if is_node_available else '#f44336'};'>"
        node_html += "✅ " if is_node_available else "❌ "
        node_html += f"{node_name}</span>"
        
        if version:
            node_html += f" <span style='color: #9e9e9e; font-size: 0.9em;'>(版本: {version})</span>"
            
        if not is_node_available and download_url:
            node_html += f" <a href='{download_url}' target='_blank'>下载</a>"
            # 添加安装按钮
            node_html += f''' <button onclick="installNode('{node_name}', '{download_url}')" 
                style='background-color: #4caf50; color: white; border: none; padding: 0px 4px; 
                border-radius: 2px; cursor: pointer; font-size: 0.8em; height: 16px; line-height: 1; 
                margin: 0 2px; vertical-align: middle; display: inline-flex; align-items: center; justify-content: center;
                min-width: 24px; text-align: center;'>
                安装
            </button>'''
        
        node_html += "</li>"
        
        if is_node_available:
            installed_nodes_html.append(node_html)
        else:
            missing_nodes_html.append(node_html)
    
    # 优先显示缺失的节点
    html_parts.extend(missing_nodes_html)
    html_parts.extend(installed_nodes_html)
    html_parts.append("</ul>")
    
    # 添加全部下载按钮
    missing_nodes = [(name, info.get("downloadurl", "")) for name, info in nodes_data.items() 
                     if not check_node_exists(name) and isinstance(info, dict) and info.get("downloadurl")]
    
    if missing_nodes:
        html_parts.append("<div style='margin-top: 6px; display: flex; gap: 8px;'>")
        # 下载按钮
        html_parts.append("""<button onclick="(function() {
          if (confirm('是否下载所有缺失节点？')) {""")
        for node_name, url in missing_nodes:
            if url:
                html_parts.append(f"    window.open('{url}', '_blank');")
        html_parts.append("""  }
        })()" style='background-color: #2196f3; color: white; border: none; padding: 4px 8px; 
        border-radius: 2px; cursor: pointer; font-size: 13px; height: 26px; display: inline-flex; 
        align-items: center; justify-content: center;'>
        下载所有缺失节点
        </button>""")
        
        # 添加批量安装按钮
        html_parts.append("""<button onclick="installAllNodes()" 
        style='background-color: #4caf50; color: white; border: none; padding: 4px 8px; 
        border-radius: 2px; cursor: pointer; font-size: 13px; height: 26px; display: inline-flex; 
        align-items: center; justify-content: center;'>
        安装所有缺失节点
        </button>""")
        html_parts.append("</div>")
    
    html_parts.append("</div>")
    
    # 在HTML头部添加JavaScript函数
    html_parts.insert(1, """
    <script>
        async function installNode(nodeName, url) {
            if (confirm('是否安装节点 ' + nodeName + '?')) {
                try {
                    // 调用ComfyUI的安装API
                    const response = await fetch('/manager/install', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            type: "custom-node",  
                            url: "download_url", 
                            restart: false         
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        alert('节点 ' + nodeName + ' 安装成功！请重启ComfyUI以加载新节点。');
                        // 刷新页面
                        window.location.reload();
                    } else {
                        alert('安装失败: ' + (data.error || '未知错误'));
                    }
                } catch (error) {
                    console.error('安装失败:', error);
                    alert('安装失败: ' + error.message);
                }
            }
        }

        // 批量安装所有节点的函数
        async function installAllNodes() {
            if (confirm('是否安装所有缺失节点？')) {
                let failed = [];
                for (const node of document.querySelectorAll('[data-install]')) {
                    try {
                        const response = await fetch('/customnode/install', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: node.getAttribute('data-install')
                        });
                        const data = await response.json();
                        if (!data.success) {
                            failed.push(node.getAttribute('data-name'));
                        }
                    } catch (error) {
                        failed.push(node.getAttribute('data-name'));
                    }
                }
                
                if (failed.length === 0) {
                    alert('所有节点安装成功！请重启ComfyUI以加载新节点。');
                    window.location.reload();
                } else {
                    alert('部分节点安装失败: ' + failed.join(', '));
                }
            }
        }
    </script>
    """)
    
    return "".join(html_parts)

def generate_model_status_html(model_data):
    """生成模型状态 HTML"""
    # 若 model_data 是字符串，进行 JSON 解析
    if isinstance(model_data, str):
        try:
            # 处理反斜杠转义问题，将单个反斜杠替换为双反斜杠
            model_data = re.sub(r'\\', r'\\\\', model_data)
            model_data = model_data.replace("\'", "\"")
            model_data = json.loads(model_data)
        except json.JSONDecodeError as e:
            print(f"解析模型信息失败: {e}")
            return f"<p style='margin:0; padding:0;'>解析模型信息失败，请检查数据格式:{model_data}</p>"
    # 检查 model_data 是否为空或者不是字典类型
    if not model_data or not isinstance(model_data, dict):
        print(f"model_data 为空或不是字典类型: {model_data}")
        return f"<p style='margin:0; padding:0;'>没有可用的模型数据:{model_data}</p>"

    html_parts = ["<div class='model-status' style='margin:2px 0; padding:6px 8px;'>"]
    
    # 统计模型数量
    total_models = len(model_data)
    available_models = 0
    for model_name, model_info in model_data.items():
        if isinstance(model_info, dict) and model_info.get("path"):
            if check_model_exists(model_info["path"],model_name):
                available_models += 1
    
    html_parts.append(f"<h4 style='margin:0 0 2px 0; padding:0; line-height:1.3;'>工作流所需模型 <span style='font-weight:normal;font-size:13px;color:#e0e0e0;'>(共 {total_models} 个模型，已安装 {available_models} 个，缺少 {total_models - available_models} 个)</span></h4>")
    
    # 模型列表
    html_parts.append("<ul style='margin:2px 0; padding-left:20px; list-style-position:outside;'>")
    missing_models_html = []
    installed_models_html = []
    
    for model_name, model_info in model_data.items():
        if isinstance(model_info, dict):
            download_url = model_info.get("downloadurl", "")
            model_path = model_info.get("path", "")
        else:
            # 如果model_info不是字典，使用空值
            download_url = ""
            model_path = ""
        
        # 检查模型是否存在于本地
        is_model_available = check_model_exists(model_path,model_name) if model_path else False
        
        model_html = f"<li style='margin-bottom:1px;line-height:1.3;'><span style='color: {'#4caf50' if is_model_available else '#f44336'};'>"
        model_html += "✅ " if is_model_available else "❌ "
        model_html += f"{model_name}</span>"
        
        if model_path:
            model_html += f" <span style='color: #9e9e9e; font-size: 0.9em;'>({model_path})</span>"
            
        if not is_model_available and download_url:
            model_html += f" <a href='{download_url}' target='_blank'>下载</a>"
            
        model_html += "</li>"
        
        if is_model_available:
            installed_models_html.append(model_html)
        else:
            missing_models_html.append(model_html)
    
    # 优先显示缺失的模型
    html_parts.extend(missing_models_html)
    html_parts.extend(installed_models_html)
    html_parts.append("</ul>")
    
    # 添加全部下载按钮
    missing_models = []
    for model_name, info in model_data.items():
        if isinstance(info, dict) and info.get("path") and info.get("downloadurl"):
            if not check_model_exists(info["path"],model_name):
                missing_models.append((model_name, info["downloadurl"]))
    
    if missing_models:
        html_parts.append("<div style='margin-top: 6px;'>")
        html_parts.append("""<button onclick="(function() {
          if (confirm('这些模型文件可能很大，是否继续下载所有缺失模型？')) {""")
        
        for model_name, url in missing_models:
            if url:
                html_parts.append(f"    window.open('{url}', '_blank');")
                
        html_parts.append("""  }
        })()" style='background-color: #2196f3; color: white; border: none; padding: 4px 8px; 
        border-radius: 2px; cursor: pointer; font-size: 13px; height: 26px; display: inline-flex; 
        align-items: center; justify-content: center;'>
        下载所有缺失模型
        </button>""")
        html_parts.append("</div>")
    
    html_parts.append("</div>")
    return "".join(html_parts)

def check_node_exists(node_name):
    """
    通过动态导入模块检查节点是否已经安装
    :param node_name: 节点名称
    :return: 如果节点存在返回 True，否则返回 False
    """
    return node_name in NODE_CLASS_MAPPINGS

def check_model_exists(model_path,model_name):
    """检查模型是否存在于本地"""
    full_path = os.path.join(folder_paths.base_path, model_path,model_name)
    print(f"full_path: {full_path}")
    if os.path.isfile(full_path):
        return True
    return False
