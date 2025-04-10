import json
import time
import html
from pathlib import Path
from decimal import Decimal
from urllib.parse import quote
from aiohttp import web
from typing import Optional
from ai_services.utils.html_parser import HtmlParser


def str_process(string):
    # 移除命令中的中括号
    try:
        if string.startswith('[') and string.endswith(']'):
            string = json.loads(string)
            for item in string :
              string = item
              break
        else:
            string = str(string)
            if string.startswith('[') and string.endswith(']'):
               string = string[1:-1]
            # 移除开头和结尾的引号
            if string.startswith('"') and string.endswith('"'):
               string = string[1:-1]
            string = string.replace(f'\\"', ' ')
    except:
        string = str(string)
        if string.startswith('[') and string.endswith(']'):
           string = string[1:-1]
        # 移除开头和结尾的引号
        if string.startswith('"') and string.endswith('"'):
           string = string[1:-1]
        string = string.replace(f'\\"', ' ')
    string = string.replace(f'\'', '\"')
    return string


def fun_process_ffmpeg_command(ai_response):
    """
    处理FFmpeg相关命令的函数，解析AI响应并生成HTML内容
    
    Args:
        ai_response: AI返回的响应文本
    
    Returns:
        str: 格式化的HTML结果
    """
    # 解析AI响应中的内容标签
    groups, content = HtmlParser.parse_content_tag(ai_response)
    
    # 提取并统一转换为字符串
    type = str_process(groups.get('type', [])[0] if groups.get('type', []) else None)
    title = str_process(groups.get('title', [])[0] if groups.get('title', []) else "FFmpeg命令")
    content = str_process(groups.get('content', [])[0] if groups.get('content', []) else None)
    explanation = str_process(groups.get('explanation', [])[0] if groups.get('explanation', []) else None)
    error = str_process(groups.get('error', [])[0] if groups.get('error', []) else None)
    error_para = str_process(groups.get('error_para', [])[0] if groups.get('error_para', []) else None)

    if not content:
        return ai_response
    # 生成唯一的时间戳，避免函数名冲突
    timestamp = int(time.time() * 1000)
    
    # 构建 HTML
    html_parts = []
    
    # 添加容器开始
    html_parts.append('<div class="ffmpeg-container" style="all:initial;border:1px solid #ddd; font-family:Arial,sans-serif; display:block; color:#e0e0e0;">')
    
    # 添加 CSS 样式
    html_parts.append("""
    <style>
        .ffmpeg-container {
            font-family: Arial, sans-serif;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            background-color: #2a2a3a;
            color: #e0e0e0;
        }
         .ffmpeg-container {
            font-family: Arial, sans-serif;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #2a2a3a;
            color: #e0e0e0;
        }
        .ffmpeg-header {
            background-color: #3a3a4a;
            padding: 8px 12px;
            border-bottom: 1px solid #555;
        }
        .ffmpeg-title {
            margin: 0;
            font-size: 14px;
            color: #ffffff;
            font-weight: 500;
        }
        .ffmpeg-message {
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid #555;
            white-space: pre-wrap;
            color: #e0e0e0;
        }
        .ffmpeg-message.success {
            background-color: #2e7d32;
            color: #e8f5e9;
        }
        .ffmpeg-message.error {
            background-color: #c62828;
            color: #ffebee;
        }
        .ffmpeg-explanation {
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid #555;
            white-space: pre-wrap;
            color: #e0e0e0;
        }
        .ffmpeg-code {
            margin: 0 12px 12px;
            position: relative;
        }
        .ffmpeg-code pre {
            background-color: #1e1e2e;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 12px;
            overflow: auto;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            color: #e0e0e0;
            margin: 8px 0;
        }
        .ffmpeg-actions {
            margin: 0 12px 12px;
            display: flex;
            gap: 8px;
        }
        .ffmpeg-button {
            padding: 6px 12px !important;
            border: none !important;
            border-radius: 2px !important;
            cursor: pointer !important;
            font-weight: normal !important;
            font-size: 14px !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 4px !important;
            height: 56px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }
        .execute-button {
            background-color: #4caf50;
            color: white;
        }
        .execute-button:hover {
            background-color: #388e3c;
        }
        .copy-button {
            background-color: #2196f3;
            color: white;
        }
        .copy-button:hover {
            background-color: #1976d2;
        }
        .ffmpeg-result {
            border: 1px solid #555;
            display: flex;
            flex-direction: column;
            background-color: #1e1e2e;
            border-radius: 1px;
            color: #e0e0e0;
            margin-top: 1px;
            margin-bottom: 1px; /* 添加下边距 */
            
        }
        .ffmpeg-result-title {
            font-size: 20px;
            font-weight: normal;
            flex-grow: 1;
            margin: 0;
            padding: 2px 4px;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    </style>
    """)
    
    # 1. 检测到ffmpeg命令
    html_parts.append('<div class="ffmpeg-message">检测到FFmpeg命令</div>')
    
    # 2. 标题
    html_parts.append(f'<div class="ffmpeg-header"><h3 class="ffmpeg-title">{html.escape(title)}</h3></div>')
    
    # 3. 命令行说明
    if explanation:
        html_parts.append(f'<div class="ffmpeg-explanation">{html.escape(explanation)}</div>')
    
    # 4. 错误说明（如果有）
    if error:
        html_parts.append(f'<div class="ffmpeg-message error">{html.escape(error)}</div>')
    if error_para:
        html_parts.append(f'<div class="ffmpeg-explanation">{html.escape(error_para)}</div>')
    

    
    # 5. 命令内容
    # 添加一个隐藏的纯文本区域，用于复制
    html_parts.append(f'<textarea id="ffmpeg_cmd_{timestamp}" style="display:none;">{html.escape(content)}</textarea>')
    
    html_parts.append('<div class="ffmpeg-code">')
    html_parts.append(f'<pre><code id="cmd_display_{timestamp}">{html.escape(content)}</code></pre>')
    html_parts.append('</div>')
    
    # 6. 操作按钮
    html_parts.append('<div class="ffmpeg-actions">')
    
    
    # 执行按钮的 JavaScript 代码
    execute_button_js = f"""
    (function() {{
        const resultTitle = document.getElementById('result_title_{timestamp}');
        resultTitle.textContent = '命令执行中';
        resultTitle.display = 'block';
        resultTitle.parentElement.style.display = 'block'; 
        try {{
            const cmd = document.getElementById('ffmpeg_cmd_{timestamp}').value;
            fetch('/comfy_ai_assistant/cmd_win_ffmpeg', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{ cmd: cmd }})
            }})
            .then(response => response.json())
            .then(data => {{
                // 获取结果容器
                const copyButton = document.getElementById('copy_btn_{timestamp}');
                const resultTitle = document.getElementById('result_title_{timestamp}');
                const resultCode = document.getElementById('result_code_{timestamp}');
                const result = data.result;
                resultTitle.textContent = result.message;

                if (data.success) {{
                    
                    if (result.success) {{
                        
                        resultCode.textContent = result.output;
                    }} else {{
                        resultCode.textContent = result.error;
                    }}

                    resultCode.style.display = 'block';
                    resultTitle.display = 'block';
                    copyButton.style.display = 'inline-flex';
                    resultTitle.parentElement.style.display = 'block'; 
                    resultCode.parentElement.style.display = 'block'; 
                }} else {{
                    resultTitle.textContent = '执行请求失败';
                    resultCode.textContent = data.error || '未知错误';
                    resultCode.style.display = 'block';
                    resultTitle.display = 'block';
                    copyButton.style.display = 'inline-flex';
                    resultCode.parentElement.style.display = 'block'; 
                }}
            }})
            .catch(error => {{
                alert('执行命令时出错: ' + error.message);
            }});
        }} catch (error) {{
            alert('执行命令时出错: ' + error.message);
        }}
    }})()
    """
    
    # 复制按钮的 JavaScript 代码
    copy_button_js = f"""
    (function() {{
        try {{
            const textArea = document.getElementById('ffmpeg_cmd_{timestamp}');
            if (!textArea) throw new Error('找不到命令内容');
            
            textArea.style.display = 'block';
            textArea.select();
            const success = document.execCommand('copy');
            textArea.style.display = 'none';
            
            if (success) {{
                alert('命令已复制到剪贴板');
            }} else {{
                throw new Error('复制命令失败');
            }}
        }} catch (err) {{
            console.error('复制失败:', err);
            alert('自动复制失败，请手动选择并复制命令内容');
            
            const codeElement = document.getElementById('cmd_display_{timestamp}');
            if (codeElement) {{
                const range = document.createRange();
                range.selectNode(codeElement);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
            }}
        }}
    }})()
    """
    
    # 添加操作按钮
    html_parts.append(f"""
    <button class="ffmpeg-button execute-button" onclick="{html.escape(execute_button_js)}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 12H19M19 12L13 6M19 12L13 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        执行命令
    </button>
    """)

    html_parts.append(f"""
    <button class="ffmpeg-button copy-button" onclick="{html.escape(copy_button_js)}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5H6C4.89543 5 4 5.89543 4 7V19C4 20.1046 4.89543 21 6 21H16C17.1046 21 18 20.1046 18 19V17M8 5C8 6.10457 8.89543 7 10 7H14C15.1046 7 16 6.10457 16 5M8 5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5M16 5V7C16 8.10457 16.8954 9 18 9H20C21.1046 9 22 9.89543 22 11V17C22 18.1046 21.1046 19 20 19H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        复制命令
    </button>
    """)

    html_parts.append(f"""
    <button id="copy_btn_{timestamp}" class="ffmpeg-button copy-button" style="display:none;" onclick="(function(event) {{
                const btn = event.target;
                const text = document.getElementById('result_code_{timestamp}').textContent;
                navigator.clipboard.writeText(text).then(() => {{
                    alert('已复制到剪贴板');
                }}).catch(() => alert('复制失败'));
            }})(event)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5H6C4.89543 5 4 5.89543 4 7V19C4 20.1046 4.89543 21 6 21H16C17.1046 21 18 20.1046 18 19V17M8 5C8 6.10457 8.89543 7 10 7H14C15.1046 7 16 6.10457 16 5M8 5C8 3.89543 8.89543 3 10 3H14C15.1046 3 16 3.89543 16 5M16 5V7C16 8.10457 16.8954 9 18 9H20C21.1046 9 22 9.89543 22 11V17C22 18.1046 21.1046 19 20 19H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        复制结果
    </button>
    """)
    
    # 关闭 按钮 div
    html_parts.append('</div>')

    # 添加结果容器
    html_parts.append('<div>')

    # 2. 标题
    html_parts.append(f'<div class="ffmpeg-header"  style="display:none;"><div id="result_title_{timestamp}" class="ffmpeg-result-title  style="display:none;"></div></div>')


    html_parts.append(f'<pre   style="display:none;"><code id="result_code_{timestamp}" style="display:none;">{html.escape(content)}</code></pre>')
    # 关闭 容器div
    html_parts.append('</div>')
    
    # 关闭主容器
    html_parts.append('</div>')
    
    # 返回完整的 HTML
    return ''.join(html_parts)