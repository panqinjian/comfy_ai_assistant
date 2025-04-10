from lxml import html, etree
from typing import Union, Dict, List
import re
import markdown2  # 添加 markdown2 库来处理 Markdown
from bs4 import BeautifulSoup, Tag
import logging
from ..utils.handler_loader import load_handler_function
from ..prompt_api import load_prompt_data
from bs4 import BeautifulSoup
from jsonfinder import jsonfinder
import re
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HtmlParser:
    """HTML内容解析器"""
    
    # 允许的HTML标签和属性
    ALLOWED_TAGS = {
        'button': ['onclick', 'class', 'id', 'style'],
        'div': ['class', 'id', 'style'],
        'pre': ['class'],
        'code': ['class'],
        'p': ['class'],
        'h1': ['class'],
        'h2': ['class'],
        'h3': ['class'],
        'h4': ['class'],
        'h5': ['class'],
        'h6': ['class'],
        'ul': ['class'],
        'ol': ['class'],
        'li': ['class'],
        'span': ['class'],
        'br': [],
    }
    
    # 允许的事件处理程序
    ALLOWED_EVENTS = {
        'onclick': [
            # 允许的 ComfyUI API 调用模式
            r'fetch\([\'"]http://127\.0\.0\.1:8188/load-workflow[\'"]\s*,\s*\{[^}]+\}\)',
            # 其他安全的事件处理程序模式
        ]
    }

    @classmethod
    def parse_ai_response(cls, content: str) -> str:
        """
        解析AI返回的内容，处理HTML和Markdown
        
        Args:
            content: AI返回的原始内容
            
        Returns:
            处理后的安全HTML内容
        """
        try:
            # 检查是否包含HTML标签
            if re.search(r'<[a-z][\s\S]*>', content, re.I):
                return cls.clean_html(content)
            return content
        except Exception as e:
            print(f"解析AI响应失败: {str(e)}")
            return content

    @classmethod
    def clean_html(cls, html_content: str) -> str:
        """
        清理HTML内容，移除不安全的标签和属性
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            清理后的安全HTML
        """
        try:
            # 解析HTML
            doc = html.fromstring(html_content)
            
            # 遍历所有元素
            for element in doc.iter():
                # 跳过注释和文本节点
                if not isinstance(element.tag, str):
                    continue
                
                tag = element.tag.lower()
                
                # 检查标签是否允许
                if tag not in cls.ALLOWED_TAGS:
                    # 将不允许的标签替换为span
                    element.tag = 'span'
                    # 清除所有属性
                    element.attrib.clear()
                    continue
                
                # 检查属性
                allowed_attrs = cls.ALLOWED_TAGS[tag]
                for attr in list(element.attrib.keys()):
                    if attr not in allowed_attrs:
                        # 移除不允许的属性
                        del element.attrib[attr]
                    elif attr in cls.ALLOWED_EVENTS:
                        # 检查事件处理程序是否安全
                        value = element.attrib[attr]
                        if not cls.is_safe_event_handler(attr, value):
                            del element.attrib[attr]
            
            # 转换回字符串
            return etree.tostring(doc, encoding='unicode', method='html')
            
        except Exception as e:
            print(f"清理HTML失败: {str(e)}")
            return html_content

    @classmethod
    def is_safe_event_handler(cls, event: str, handler: str) -> bool:
        """
        检查事件处理程序是否安全
        
        Args:
            event: 事件名称
            handler: 事件处理程序代码
            
        Returns:
            是否安全
        """
        if event not in cls.ALLOWED_EVENTS:
            return False
            
        # 检查是否匹配允许的模式
        for pattern in cls.ALLOWED_EVENTS[event]:
            if re.search(pattern, handler):
                return True
                
        return False

    @classmethod
    def parse_code_block(cls, code: str, lang: str = '') -> Dict:
        """
        解析代码块
        
        Args:
            code: 代码内容
            lang: 语言标识
            
        Returns:
            解析后的代码块数据
        """
        return {
            'type': 'code',
            'language': lang,
            'content': code
        } 
    
    @classmethod
    def create_code_block(cls, code_content: str, lang: str = 'plaintext') -> Tag:
        """
        创建代码块元素

        Args:
            code_content: 代码内容
            lang: 编程语言

        Returns:
            BeautifulSoup Tag 对象
        """
        soup = BeautifulSoup('', 'html.parser')

        # 创建代码块容器
        code_block = soup.new_tag('div', attrs={'class': 'code-block'})

        # 创建头部
        header = soup.new_tag('div', attrs={'class': 'code-header'})
        lang_span = soup.new_tag('span', attrs={'class': 'code-lang'})
        lang_span.string = lang
        copy_btn = soup.new_tag('button', attrs={
            'class': 'copy-button',
            'onclick': 'copyCode(this)'
        })
        copy_btn.string = '复制'

        # 创建代码内容
        pre = soup.new_tag('pre')
        code = soup.new_tag('code', attrs={'class': f'language-{lang}'})
        code.string = code_content

        # 组装代码块
        header.append(lang_span)
        header.append(copy_btn)
        code_block.append(header)
        pre.append(code)
        code_block.append(pre)

        return code_block

    @classmethod
    def format_code_blocks(cls, content: str) -> str:
        """格式化代码块，添加语法高亮"""
        try:
            # 检查内容是否为空
            if not content or content.strip() == '':
                return content
            
            # 预处理：保护已有的 HTML 元素块
            protected_blocks = {}
            block_id = 0
            
            # 保护 <div class="code-block"> 已经格式化的代码块
            def protect_existing_code_blocks(match):
                nonlocal block_id
                placeholder = f"__PROTECTED_CODE_BLOCK_{block_id}__"
                protected_blocks[placeholder] = match.group(0)
                block_id += 1
                return placeholder
            
            # 保护其他 HTML 元素
            def protect_html_elements(match):
                nonlocal block_id
                # 排除 pre 和 code 标签，它们需要特殊处理
                tag = match.group(1).lower()
                if tag in ['pre', 'code']:
                    return match.group(0)
                
                placeholder = f"__PROTECTED_HTML_{block_id}__"
                protected_blocks[placeholder] = match.group(0)
                block_id += 1
                return placeholder
            
            # 保护已有的代码块
            content = re.sub(
                r'<div\s+class=["\']code-block["\'][^>]*>[\s\S]*?</div>',
                protect_existing_code_blocks,
                content
            )
            
            # 保护其他 HTML 元素 (排除 pre 和 code)
            content = re.sub(
                r'<(\w+)(?:\s+[^>]*)?(?:>[\s\S]*?</\1>|/>)',
                protect_html_elements,
                content
            )
            
            # 使用 markdown2 处理 Markdown 内容
            html_content = markdown2.markdown(content, extras=['fenced-code-blocks'])
            
            # 使用 html5lib 解析 HTML (更准确的解析)
            soup = BeautifulSoup(html_content, 'html5lib')
            
            # 处理代码块
            for pre in soup.find_all('pre'):
                code = pre.find('code')
                if code and code.parent == pre:
                    # 获取语言类名
                    lang = code.get('class', ['language-plaintext'])[0].replace('language-', '') if code.get('class') else 'plaintext'
                    
                    # 获取代码内容，保留换行符和空格
                    code_content = code.get_text(strip=False)
                    # 只清理开头和结尾的空白
                    code_content = code_content.strip('\n\r\t ')
                    
                    # 创建新的代码块
                    code_block = cls.create_code_block(code_content, lang)
                    
                    # 替换原始的 pre 标签
                    pre.replace_with(code_block)
            
            # 获取处理后的 HTML
            result = str(soup.body).replace('<body>', '').replace('</body>', '')
            
            # 恢复被保护的块
            for placeholder, original in protected_blocks.items():
                result = result.replace(placeholder, original)
            
            return result
            
        except Exception as e:
            logger.error(f"格式化代码块失败: {str(e)}")
            logger.exception(e)
            return content

    @classmethod
    def process_content_by_prompt(cls, content: str, prompt_id: str = None) -> str:
        """
        根据提示词ID处理内容
        
        Args:
            content: 原始内容
            prompt_id: 提示词ID
            
        Returns:
            处理后的内容
        """
        prompt_data = None
        
        if prompt_id:
            # 使用prompt_id加载提示词数据
            prompt_data = load_prompt_data(prompt_id)
                        
        # 检查是否有处理函数配置     
        if prompt_data and prompt_data.get('prompt_fun') and prompt_data.get('prompt_fun_path'):
            try:
                # 加载处理函数
                prompt_fun = load_handler_function(prompt_data.get('prompt_fun_path'), prompt_data.get('prompt_fun'))
                if prompt_fun:
                    # 执行处理函数
                    formatted_content = prompt_fun(content)
                    return formatted_content
                else:
                    # 如果处理函数加载失败，使用默认格式化
                    return cls.format_code_blocks(content)
            except Exception as e:
                logger.error(f"执行处理函数{prompt_data.get('prompt_fun')}失败: {str(e)}")
                # 出错时使用默认格式化
                return cls.format_code_blocks(content)
        else:
            # 没有处理函数配置时使用默认格式化
            return cls.format_code_blocks(content)
        
    @classmethod
    def process_content_by_prompt_run(cls, prompt_id: str = None) -> str:
        """
        根据提示词ID处理内容
        
        Args:
            content: 原始内容
            prompt_id: 提示词ID
            
        Returns:
            处理后的内容
        """
        prompt_data = None
        
        if prompt_id:
            # 使用prompt_id加载提示词数据
            prompt_data = load_prompt_data(prompt_id)
                        
        # 检查是否有处理函数配置     
        if prompt_data and prompt_data.get('prompt_run') and prompt_data.get('prompt_run_path'):
            try:
                # 加载处理函数
                prompt_run = load_handler_function(prompt_data.get('prompt_run_path'), prompt_data.get('prompt_run'))
                if prompt_run:
                    # 执行处理函数
                    formatted_content = prompt_run()
                    return formatted_content
                else:
                    # 如果处理函数加载失败，使用默认格式化
                    return ""
            except Exception as e:
                logger.error(f"执行处理函数{prompt_data.get('prompt_run')}失败: {str(e)}")
                # 出错时使用默认格式化
                return ""
        else:
            # 没有处理函数配置时使用默认格式化
            return ""

    @classmethod
    def parse_dynamic_tags(cls, content: str):
        """
        动态解析所有存在的<xxx>标签，并按类型分组
        
        Args:
            text: 包含多种标签的原始文本
            
        Returns:
        dict: 按标签类型分组的结果，包含所有发现的标签类型、JSON和普通文本
        """
        soup = BeautifulSoup(content, 'html.parser')
    
        # 1. 动态获取所有存在的标签类型
        tag_types = set()
        for tag in soup.find_all(True):  # True表示匹配所有标签
            tag_types.add(tag.name)
    
        groups = {'html': [], 'json': [], 'text': [], 'code': []}  # 增加 'code' 分组
        groups_tag_type = {}
    
        # 2. 按标签类型提取内容
        for tag_type in tag_types:
            groups_tag_type[tag_type] = []
            tags = soup.find_all(tag_type)
            for tag in tags:
                tag_content = tag.get_text(strip=True)
                groups_tag_type[tag_type].append(tag_content)
        
                # 特殊处理 <code> 标签
                if tag_type == 'code':
                    groups['code'].append(tag_content)  # 将代码块内容单独存储
                else:
                    groups['html'].append(f'<{tag_type}> {tag_content} </{tag_type}>')
        
                tag.decompose()  # 移除已处理的标签

        # 3. 提取 Markdown 格式的代码块
        remaining_text = str(soup)
        markdown_code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', remaining_text, re.DOTALL)
        groups['code'].extend([block.strip() for block in markdown_code_blocks])

        # 3. 处理剩余文本中的JSON
        remaining_text = str(soup)
        for json_obj in jsonfinder(remaining_text):
            groups['json'].append(json_obj)
            # 从剩余文本中移除JSON内容（需要更精确的替换逻辑）
            # 此处简化处理，实际可能需要正则表达式匹配
            remaining_text = remaining_text.replace(str(json_obj), '')
    
        # 4. 提取剩余的普通文本
        plain_text = BeautifulSoup(remaining_text, 'html.parser').get_text()
        text_chunks = [chunk.strip() for chunk in re.split(r'\n|\s{2,}', plain_text) if chunk.strip()]
        groups['text'] = text_chunks
    
        return groups
    
    @classmethod
    def parse_dynamic_tags_text(cls, content: str):
        groups = {'html': [], 'json': [], 'text': []}  # 存储解析结果
        stack = []  # 用于处理嵌套标签
        buffer = ''  # 当前正在处理的内容缓冲区
        i = 0  # 指针位置
    
        while i < len(content):
            char = content[i]
    
            # 检测标签起始
            if char == '<':
                # 如果缓冲区有内容，存储为普通文本
                if buffer.strip():
                    if stack:
                        # 如果在标签内，作为标签内容
                        groups['html'].append(f"<{stack[-1]}> {buffer.strip()} </{stack[-1]}>")
                    else:
                        # 如果不在标签内，作为普通文本
                        groups['text'].append(buffer.strip())
                    buffer = ''  # 清空缓冲区
    
                # 解析标签名称
                tag_start = i + 1
                tag_end = content.find('>', tag_start)
                if tag_end == -1:
                    raise ValueError("未闭合的标签")
                tag_name = content[tag_start:tag_end].strip()
    
                # 检测结束标签
                if tag_name.startswith('/'):
                    tag_name = tag_name[1:]  # 去掉结束标签的斜杠
                    if stack and stack[-1] == tag_name:
                        stack.pop()  # 弹出匹配的开始标签
                    else:
                        raise ValueError(f"标签不匹配：{tag_name}")
                else:
                    stack.append(tag_name)  # 推入栈中
    
                i = tag_end  # 移动指针到标签结束位置
    
            # 检测普通字符
            else:
                buffer += char
    
            i += 1
    
        # 处理剩余的缓冲区内容
        if buffer.strip():
            if stack:
                groups['html'].append(f"<{stack[-1]}> {buffer.strip()} </{stack[-1]}>")
            else:
                groups['text'].append(buffer.strip())
    
        # 返回解析结果
        return groups
    
    @classmethod
    def parse_dynamic_tags_text_new(cls, content: str):
        """
        逐字解析内容，发现特定特征块时调用 parse_dynamic_tags 处理，并支持 Markdown 代码块和 JSON 数据的提取。
        
        Args:
            content: 待解析的文本内容。
            
        Returns:
            dict: 按类型分类的解析结果。
        """
        print(content)
        groups = {'html': [], 'json': [], 'text': [], 'code': []}  # 按类型分类存储
        content,groups_json = cls.parse_content_json(content)
        groups['json'] = groups_json
        print(content,groups_json)

        ordered_groups = []  # 按顺序存储解析结果
        tag_types = cls.get_tags_type(content)  # 缓存所有标签类型
        max_iterations = 10000  # 最大循环次数，防止死循环
        iteration_count = 0  # 当前循环次数

        while content.strip():  # 循环处理剩余内容
            iteration_count += 1
            if iteration_count > max_iterations:
                raise RuntimeError("解析过程中出现死循环，已达到最大循环次数")
    
            buffer = ''  # 当前正在处理的内容缓冲区
            i = 0  # 指针位置
            content_length = len(content)  # 当前内容长度
    
            while i < content_length:
                char = content[i]
    
    
                # 检测 Markdown 代码块
                if content[i:i+3] == '```':
                    # 提取 Markdown 代码块
                    end_index = content.find('```', i + 3)
                    if end_index == -1:
                        raise ValueError("未闭合的 Markdown 代码块")
                    markdown_block = content[i+3:end_index].strip()
                    groups['code'].append(markdown_block)
                    ordered_groups.append(('code', markdown_block))  # 按顺序存储
                    content = content[:i] + content[end_index+3:]  # 跳过已处理的代码块
                    content_length = len(content)  # 更新内容长度
                    break  # 跳出当前循环，重新处理剩余内容
    
                # 检测 HTML 标签起始
                elif char == '<':
                    # 如果缓冲区有内容，存储为普通文本
                    if buffer.strip():
                        groups['text'].append(buffer.strip())
                        ordered_groups.append(('text', buffer.strip()))  # 按顺序存储
                        buffer = ''  # 清空缓冲区
    
                    # 检测特定块
                    tag_start = i + 1
                    tag_end = content.find('>', tag_start)
                    if tag_end == -1:
                        raise ValueError("未闭合的标签")
                    tag_name = content[tag_start:tag_end].strip()
    
                    # 检测是否为特定块
                    if tag_name in tag_types:
                        # 调用 get_tags_value 提取标签内容
                        parsed_result, remaining_content = cls.get_tags_value(content, tag_name)
    
                        # 根据标签类型存储解析结果
                        if tag_name == 'code':
                            groups['code'].extend(parsed_result)
                            ordered_groups.extend([('code', item) for item in parsed_result])  # 按顺序存储
                        elif tag_name == 'json':
                            groups['json'].extend(parsed_result)
                            ordered_groups.extend([('json', item) for item in parsed_result])  # 按顺序存储
                        else:
                            groups['html'].extend(parsed_result)
                            ordered_groups.extend([('html', item) for item in parsed_result])  # 按顺序存储
    
                        # 更新 content 为剩余未处理的内容
                        content = remaining_content
                        content_length = len(content)  # 更新内容长度
                        break  # 跳出当前循环，重新处理剩余内容
                    else:
                        # 非特定块，作为普通 HTML 处理
                        buffer += char
    
                else:
                    # 普通字符，加入缓冲区
                    buffer += char
    
                i += 1

    
            # 处理剩余的缓冲区内容
            if buffer.strip():
                groups['text'].append(buffer.strip())
                ordered_groups.append(('text', buffer.strip()))  # 按顺序存储
                content = content[len(buffer):]  # 更新 content，移除已处理的部分
    
        return {'groups': groups, 'ordered_groups': ordered_groups}
    
    @classmethod
    def render_ordered_groups_as_html(cls, content: str):
        """
        将 ordered_groups 合成为 HTML 字符串以便直接显示给用户。
        
        Args:
            content (str): 待解析的文本内容。
        
        Returns:
            str: 合成的 HTML 字符串。
        """
        result = cls.parse_dynamic_tags_text_new(content)
        html_output = []
        
        for item_type, content in result['ordered_groups']:
            if item_type == 'html':
                # 直接保留 HTML 内容
                html_output.append(content)
            elif item_type == 'text':
                # 将普通文本用 <p> 包裹
                html_output.append(f"<p>{content}</p>")
            elif item_type == 'code':
                # 将代码块用 <pre><code> 包裹，支持语言标识
                lines = content.split("\n", 1)
                language = lines[0].strip() if len(lines) > 1 else ""
                code_content = lines[1] if len(lines) > 1 else content
                html_output.append(f"<pre><code class='{language}'>{code_content}</code></pre>")
            elif item_type == 'json':
                # 将 JSON 数据格式化并用 <pre> 包裹
                try:
                    formatted_json = json.dumps(json.loads(content), indent=4, ensure_ascii=False)
                    html_output.append(f"<pre>{formatted_json}</pre>")
                except (json.JSONDecodeError, TypeError):
                    html_output.append(f"<pre>Invalid JSON: {content}</pre>")
            else:
                # 未知类型，作为普通文本处理
                html_output.append(f"<p>{content}</p>")
                print(f"Warning: Unknown item type '{item_type}', treated as text.")
        
        # 拼接所有内容为一个完整的 HTML 字符串
        return "\n".join(html_output)
    @classmethod
    def get_tags_type(cls, content: str):
        """
        动态获取所有存在的标签类型。
        
        Args:
            content: HTML 内容。
            
        Returns:
            set: 包含所有标签类型的集合。
        """
        soup = BeautifulSoup(content, 'html.parser')
        tag_types = {tag.name for tag in soup.find_all(True)}
        print(f"发现的标签类型: {tag_types}")  # 可选调试输出
        return tag_types
    
    @classmethod
    def get_tags_value(cls, content: str, tag_type: str):
        """
        提取指定标签类型的全部内容（包括标签本身及其内部内容）。
        """
        soup = BeautifulSoup(content, 'html.parser')
        tags = soup.find_all(tag_type)
        tag_values = [str(tag) for tag in tags]
        print(f"发现的标签内容: {tag_values}")  # 可选调试输出

        # 移除已处理的标签
        for tag in tags:
            tag.decompose()

        remaining_content = str(soup)
        return tag_values, remaining_content
    
    
    @classmethod
    def parse_content_json(cls, content: str):
        """
        解析工作流JSON
        """
        # 对内容进行预处理
        content = cls.preprocess_content(content)
    
        groups = {'json': []}
        start_index = 0  # 当前解析的起始位置
    
        while start_index < len(content):
            # 使用 jsonfinder 提取 JSON 数据
            for json_obj in jsonfinder(content[start_index:]):
                if json_obj:
                    json_data = str(json_obj)  # 将 JSON 对象转换为字符串
    
                    try:
                        # 将 JSON 数据解析为字典
                        parsed_json = json.loads(json_data)
                    except json.JSONDecodeError:
                        # 如果解析失败，跳过当前 JSON 数据
                        continue
    
                    # 将 JSON 数据存储到结果中
                    groups['json'].append(json_data)
    
                    # 找到 JSON 数据在 content 中的起始和结束位置
                    json_start = content.find(json_data, start_index)
                    if json_start == -1:
                        raise ValueError("无法在 content 中找到提取的 JSON 数据")
    
                    json_end = json_start + len(json_data)
    
                    # 更新起始位置，跳过已处理的 JSON 数据
                    start_index = json_end
                    content = content[:json_start] + content[json_end:]
                    break
            else:
                # 如果没有找到更多的 JSON 数据，退出循环
                break
    
        # 返回剩余的内容和提取的 JSON 数据
        return content, groups
    
    @staticmethod
    def preprocess_content(content: str) -> str:
        """
        对内容进行预处理：
        1. 将多个空格合并为单个空格。
        2. 将换行符替换为空格。
        3. 移除 `{}` 和 `[]` 符号周围的多余空格。
        """
        # 将换行符替换为空格
        #content = content.replace('\n', ' ').replace('\r', ' ')
    
        # 将多个空格合并为单个空格
        content = re.sub(r'\s+', ' ', content)
    
        # 移除 `{}` 和 `[]` 符号周围的多余空格
        content = re.sub(r'\s*([\{\}\[\]\<\>])\s*', r'\1', content)
    
        return content
    
    
    @staticmethod
    def parse_content_tag(content: str): 
        """
        对内容进行预处理：
        1. 将多个空格合并为单个空格。
        2. 将换行符替换为空格。
        3. 移除 `{}` 和 `[]` 符号周围的多余空格。
        """
        # 对内容进行预处理
        #content = HtmlParser.preprocess_content(content)
        groups = {}
        soup = BeautifulSoup(content, 'html.parser')
    
        # 获取所有标签类型
        tag_types = {tag.name for tag in soup.find_all(True)}
    
        # 遍历每种标签类型，提取对应的标签内容
        for tag_type in tag_types:
            # 提取标签的纯文本内容
            tag_values = [tag.text for tag in soup.find_all(tag_type)]  # 提取纯文本内容
            groups[tag_type] = tag_values
    
            # 删除已处理的标签
            for tag in soup.find_all(tag_type):
                tag.decompose()
    
        # 剩余未处理的内容
        remaining_content = str(soup)
    
        return groups, remaining_content

